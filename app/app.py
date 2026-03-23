import csv
import hashlib
import os
import random
import sqlite3
import string
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, abort, redirect, render_template, request, session, url_for

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "study.db"
TRIAL_CSV = DATA_DIR / "trials.csv"

DEFAULT_TRIALS_PER_PARTICIPANT = int(os.environ.get("TRIALS_PER_PARTICIPANT", "6"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "change-me-before-deploy")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

app = Flask(__name__)
app.secret_key = SECRET_KEY


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            participant_id TEXT PRIMARY KEY,
            worker_id TEXT,
            assignment_id TEXT,
            condition TEXT NOT NULL,
            n_trials INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            total_seconds REAL,
            order_label TEXT,
            survey_code TEXT
        )
        """
    )
    # Backward-compatible schema migration for older DB files.
    participant_columns = {row[1] for row in cur.execute("PRAGMA table_info(participants)").fetchall()}
    if "survey_code" not in participant_columns:
        cur.execute("ALTER TABLE participants ADD COLUMN survey_code TEXT")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id TEXT NOT NULL,
            trial_id TEXT NOT NULL,
            trial_index INTEGER NOT NULL,
            condition TEXT NOT NULL,
            prompt TEXT NOT NULL,
            gold_answer TEXT NOT NULL,
            ai_suggestion TEXT,
            ai_visible INTEGER NOT NULL,
            response_text TEXT NOT NULL,
            confidence INTEGER,
            correct INTEGER NOT NULL,
            reaction_time_seconds REAL,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY(participant_id) REFERENCES participants(participant_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions_audit (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id TEXT NOT NULL,
            event_name TEXT NOT NULL,
            event_value TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def load_trials() -> list[dict]:
    if not TRIAL_CSV.exists():
        raise FileNotFoundError(f"Missing trials file: {TRIAL_CSV}")

    trials = []
    with open(TRIAL_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"trial_id", "prompt", "gold_answer", "ai_suggestion"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"trials.csv missing required columns: {sorted(missing)}")

        for row in reader:
            trials.append(
                {
                    "trial_id": (row.get("trial_id") or "").strip(),
                    "prompt": (row.get("prompt") or "").strip(),
                    "gold_answer": (row.get("gold_answer") or "").strip(),
                    "ai_suggestion": (row.get("ai_suggestion") or "").strip(),
                    "difficulty": (row.get("difficulty") or "").strip(),
                }
            )

    if not trials:
        raise ValueError("trials.csv has no rows")
    return trials


def stable_sample(trials: list[dict], participant_id: str, n: int) -> list[dict]:
    if n >= len(trials):
        sampled = list(trials)
    else:
        seed_value = int(hashlib.sha256(participant_id.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed_value)
        sampled = rng.sample(trials, n)
    return sampled


def sanitize_condition(condition: str) -> str:
    normalized = (condition or "").strip().lower()
    if normalized in {"baseline", "no_ai", "without_ai"}:
        return "baseline"
    if normalized in {"with_ai", "ai"}:
        return "with_ai"
    raise ValueError("Invalid condition")


def create_survey_code(length: int = 10) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def insert_participant(
    participant_id: str,
    worker_id: str,
    assignment_id: str,
    condition: str,
    n_trials: int,
    order_label: str,
    survey_code: str,
) -> None:
    conn = get_db_conn()
    conn.execute(
        """
        INSERT INTO participants (participant_id, worker_id, assignment_id, condition, n_trials, started_at, order_label, survey_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (participant_id, worker_id, assignment_id, condition, n_trials, now_utc_iso(), order_label, survey_code),
    )
    conn.commit()
    conn.close()


def log_event(participant_id: str, event_name: str, event_value: str = "") -> None:
    conn = get_db_conn()
    conn.execute(
        """
        INSERT INTO sessions_audit (participant_id, event_name, event_value, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (participant_id, event_name, event_value, now_utc_iso()),
    )
    conn.commit()
    conn.close()


def save_response(payload: dict) -> None:
    conn = get_db_conn()
    conn.execute(
        """
        INSERT INTO responses (
            participant_id, trial_id, trial_index, condition, prompt, gold_answer,
            ai_suggestion, ai_visible, response_text, confidence, correct,
            reaction_time_seconds, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["participant_id"],
            payload["trial_id"],
            payload["trial_index"],
            payload["condition"],
            payload["prompt"],
            payload["gold_answer"],
            payload["ai_suggestion"],
            payload["ai_visible"],
            payload["response_text"],
            payload["confidence"],
            payload["correct"],
            payload["reaction_time_seconds"],
            payload["submitted_at"],
        ),
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mturk/<condition>", methods=["GET"])
def mturk_entry(condition: str):
    """MTurk external entrypoint that preserves worker/query params and pins condition."""
    try:
        normalized = sanitize_condition(condition)
    except ValueError:
        abort(400, "Invalid condition")

    params = request.args.to_dict(flat=True)
    params["condition"] = normalized
    return redirect(url_for("start", **params))


@app.route("/start", methods=["GET", "POST"])
def start():
    if request.method == "GET":
        preselected = (request.args.get("condition") or "baseline").strip().lower()
        if preselected not in {"baseline", "with_ai"}:
            preselected = "baseline"
        prefill_worker_id = (request.args.get("workerId") or "").strip()
        prefill_assignment_id = (request.args.get("assignmentId") or "sandbox_assignment").strip()
        prefill_turk_submit_to = (request.args.get("turkSubmitTo") or "").strip()
        prefill_hit_id = (request.args.get("hitId") or "").strip()
        preview_mode = (prefill_assignment_id == "ASSIGNMENT_ID_NOT_AVAILABLE")
        return render_template(
            "start.html",
            preselected_condition=preselected,
            prefill_worker_id=prefill_worker_id,
            prefill_assignment_id=prefill_assignment_id,
            prefill_turk_submit_to=prefill_turk_submit_to,
            prefill_hit_id=prefill_hit_id,
            preview_mode=preview_mode,
        )

    try:
        condition = sanitize_condition(request.form.get("condition", ""))
    except ValueError:
        abort(400, "Invalid condition")

    worker_id = (request.form.get("worker_id") or "anonymous_worker").strip()
    assignment_id = (request.form.get("assignment_id") or "sandbox_assignment").strip()
    order_label = (request.form.get("order_label") or "unknown").strip()
    mturk_submit_to = (request.form.get("turk_submit_to") or "").strip()
    hit_id = (request.form.get("hit_id") or "").strip()

    participant_id = f"P-{uuid.uuid4().hex[:10]}"

    trials = load_trials()
    n = min(DEFAULT_TRIALS_PER_PARTICIPANT, len(trials))
    sampled_trials = stable_sample(trials, participant_id, n)

    session.clear()
    session["participant_id"] = participant_id
    session["worker_id"] = worker_id
    session["assignment_id"] = assignment_id
    session["condition"] = condition
    session["order_label"] = order_label
    session["n_trials"] = n
    session["trial_ids"] = [t["trial_id"] for t in sampled_trials]
    session["trial_cursor"] = 0
    session["start_epoch"] = time.time()
    session["trial_start_epoch"] = time.time()
    survey_code = create_survey_code()
    session["survey_code"] = survey_code
    session["mturk_submit_to"] = mturk_submit_to
    session["hit_id"] = hit_id

    insert_participant(participant_id, worker_id, assignment_id, condition, n, order_label, survey_code)
    log_event(participant_id, "session_started", f"condition={condition};hit_id={hit_id}")

    return redirect(url_for("trial"))


@app.route("/start/baseline", methods=["GET"])
def start_baseline_link():
    params = request.args.to_dict(flat=True)
    params["condition"] = "baseline"
    return redirect(url_for("start", **params))


@app.route("/start/with_ai", methods=["GET"])
def start_with_ai_link():
    params = request.args.to_dict(flat=True)
    params["condition"] = "with_ai"
    return redirect(url_for("start", **params))


@app.route("/trial", methods=["GET"])
def trial():
    participant_id = session.get("participant_id")
    if not participant_id:
        return redirect(url_for("start"))

    condition = session.get("condition")
    trial_cursor = int(session.get("trial_cursor", 0))
    n_trials = int(session.get("n_trials", 0))

    if trial_cursor >= n_trials:
        return redirect(url_for("complete"))

    trial_ids = session.get("trial_ids", [])
    trial_lookup = {t["trial_id"]: t for t in load_trials()}
    trial_obj = trial_lookup.get(trial_ids[trial_cursor])
    if not trial_obj:
        abort(500, "Trial missing from dataset")

    session["trial_start_epoch"] = time.time()

    return render_template(
        "trial.html",
        condition=condition,
        trial_obj=trial_obj,
        trial_number=(trial_cursor + 1),
        total_trials=n_trials,
        title=("With AI Condition" if condition == "with_ai" else "Baseline Condition"),
    )


@app.route("/submit_trial", methods=["POST"])
def submit_trial():
    participant_id = session.get("participant_id")
    if not participant_id:
        return redirect(url_for("start"))

    condition = session.get("condition")
    trial_cursor = int(session.get("trial_cursor", 0))
    n_trials = int(session.get("n_trials", 0))

    if trial_cursor >= n_trials:
        return redirect(url_for("complete"))

    response_text = (request.form.get("response_text") or "").strip()
    if not response_text:
        abort(400, "Response is required")

    confidence_raw = (request.form.get("confidence") or "").strip()
    confidence = int(confidence_raw) if confidence_raw.isdigit() else None

    trial_ids = session.get("trial_ids", [])
    trial_lookup = {t["trial_id"]: t for t in load_trials()}
    trial_obj = trial_lookup.get(trial_ids[trial_cursor])
    if not trial_obj:
        abort(500, "Trial missing from dataset")

    reaction_time = max(0.0, time.time() - float(session.get("trial_start_epoch", time.time())))
    gold = trial_obj["gold_answer"].strip().lower()
    pred = response_text.strip().lower()
    correct = int(gold == pred)

    save_response(
        {
            "participant_id": participant_id,
            "trial_id": trial_obj["trial_id"],
            "trial_index": trial_cursor,
            "condition": condition,
            "prompt": trial_obj["prompt"],
            "gold_answer": trial_obj["gold_answer"],
            "ai_suggestion": trial_obj["ai_suggestion"],
            "ai_visible": int(condition == "with_ai"),
            "response_text": response_text,
            "confidence": confidence,
            "correct": correct,
            "reaction_time_seconds": reaction_time,
            "submitted_at": now_utc_iso(),
        }
    )

    session["trial_cursor"] = trial_cursor + 1

    if session["trial_cursor"] >= n_trials:
        conn = get_db_conn()
        total_seconds = max(0.0, time.time() - float(session.get("start_epoch", time.time())))
        conn.execute(
            """
            UPDATE participants
            SET completed_at = ?, total_seconds = ?
            WHERE participant_id = ?
            """,
            (now_utc_iso(), total_seconds, participant_id),
        )
        conn.commit()
        conn.close()
        log_event(participant_id, "session_completed")

    return redirect(url_for("trial"))


@app.route("/complete", methods=["GET"])
def complete():
    participant_id = session.get("participant_id")
    if not participant_id:
        return redirect(url_for("start"))

    survey_code = session.get("survey_code", "")
    assignment_id = session.get("assignment_id", "sandbox_assignment")
    worker_id = session.get("worker_id", "")
    hit_id = session.get("hit_id", "")
    mturk_submit_to = (
        session.get("mturk_submit_to")
        or request.args.get("turkSubmitTo", "")
        or request.args.get("turk_submit_to", "")
    ).strip()
    is_preview_assignment = assignment_id in {"", "sandbox_assignment", "ASSIGNMENT_ID_NOT_AVAILABLE"}

    submit_action = ""
    submit_url = ""
    if mturk_submit_to and not is_preview_assignment:
        submit_action = f"{mturk_submit_to.rstrip('/')}/mturk/externalSubmit"
        submit_query = urlencode(
            {
                "assignmentId": assignment_id,
                "workerId": worker_id,
                "hitId": hit_id,
                "surveyCode": survey_code,
            }
        )
        submit_url = f"{submit_action}?{submit_query}"

    return render_template(
        "complete.html",
        participant_id=participant_id,
        survey_code=survey_code,
        assignment_id=assignment_id,
        worker_id=worker_id,
        hit_id=hit_id,
        submit_action=submit_action,
        submit_url=submit_url,
        is_preview_assignment=is_preview_assignment,
        condition=session.get("condition", "baseline"),
        title="Study Complete",
    )


@app.route("/admin/export")
def admin_export():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(403)

    out_csv = DATA_DIR / "responses_export.csv"
    conn = get_db_conn()
    rows = conn.execute(
        """
        SELECT r.*, p.worker_id, p.assignment_id, p.survey_code, p.started_at, p.completed_at, p.total_seconds, p.order_label
        FROM responses r
        LEFT JOIN participants p ON p.participant_id = r.participant_id
        ORDER BY r.submitted_at ASC
        """
    ).fetchall()
    conn.close()

    columns = [
        "response_id", "participant_id", "trial_id", "trial_index", "condition", "prompt",
        "gold_answer", "ai_suggestion", "ai_visible", "response_text", "confidence", "correct",
        "reaction_time_seconds", "submitted_at", "worker_id", "assignment_id", "survey_code", "started_at",
        "completed_at", "total_seconds", "order_label"
    ]

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[col] for col in columns])

    return {
        "status": "ok",
        "export_path": str(out_csv),
        "rows": len(rows),
    }


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
