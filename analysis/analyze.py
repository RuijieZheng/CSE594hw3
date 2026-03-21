import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_rows(input_path: Path) -> list[dict]:
    with input_path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def participant_summary(rows: list[dict]) -> list[dict]:
    buckets = defaultdict(lambda: {"correct": [], "rt": [], "confidence": [], "trial_ids": set()})

    for row in rows:
        key = (row.get("participant_id", ""), row.get("condition", ""))
        buckets[key]["correct"].append(parse_int(row.get("correct"), 0))
        buckets[key]["rt"].append(parse_float(row.get("reaction_time_seconds"), 0.0))
        confidence_raw = row.get("confidence", "")
        if confidence_raw not in {"", None}:
            buckets[key]["confidence"].append(parse_float(confidence_raw, 0.0))
        buckets[key]["trial_ids"].add(row.get("trial_id", ""))

    summary = []
    for (participant_id, condition), vals in buckets.items():
        summary.append(
            {
                "participant_id": participant_id,
                "condition": condition,
                "accuracy": mean(vals["correct"]) if vals["correct"] else 0.0,
                "mean_rt": mean(vals["rt"]) if vals["rt"] else 0.0,
                "mean_confidence": mean(vals["confidence"]) if vals["confidence"] else "",
                "n_trials": len(vals["trial_ids"]),
            }
        )
    return summary


def normal_approx_p_from_t(t_stat: float) -> float:
    z = abs(t_stat)
    return math.erfc(z / math.sqrt(2.0))


def paired_t_test(a: list[float], b: list[float]) -> tuple[float, float]:
    diffs = [x - y for x, y in zip(a, b)]
    n = len(diffs)
    if n < 2:
        return float("nan"), float("nan")

    d_bar = mean(diffs)
    s = stdev(diffs)
    if s == 0:
        return float("nan"), float("nan")

    t_stat = d_bar / (s / math.sqrt(n))
    p_val = normal_approx_p_from_t(t_stat)
    return t_stat, p_val


def sign_test(a: list[float], b: list[float]) -> tuple[int, int, float]:
    plus = 0
    minus = 0
    for x, y in zip(a, b):
        if x > y:
            plus += 1
        elif x < y:
            minus += 1

    n = plus + minus
    if n == 0:
        return plus, minus, float("nan")

    k = min(plus, minus)
    prob = 0.0
    for i in range(0, k + 1):
        prob += math.comb(n, i) * (0.5**n)
    p_two_sided = min(1.0, 2 * prob)
    return plus, minus, p_two_sided


def collect_pairs(summary: list[dict], metric: str) -> tuple[list[float], list[float]]:
    per_participant = defaultdict(dict)
    for row in summary:
        pid = row["participant_id"]
        cond = row["condition"]
        per_participant[pid][cond] = row

    baseline = []
    with_ai = []
    for pid, conds in per_participant.items():
        if "baseline" in conds and "with_ai" in conds:
            b_val = conds["baseline"].get(metric, "")
            a_val = conds["with_ai"].get(metric, "")
            if b_val == "" or a_val == "":
                continue
            baseline.append(float(b_val))
            with_ai.append(float(a_val))
    return baseline, with_ai


def write_summary_csv(summary_rows: list[dict], out_path: Path) -> None:
    fieldnames = ["participant_id", "condition", "accuracy", "mean_rt", "mean_confidence", "n_trials"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def metric_report_block(metric_name: str, baseline: list[float], with_ai: list[float]) -> list[str]:
    lines = [f"Metric: {metric_name}"]
    n = min(len(baseline), len(with_ai))
    lines.append(f"  n_pairs: {n}")
    if n < 2:
        lines.append("  Not enough paired samples for tests")
        lines.append("")
        return lines

    b = baseline[:n]
    a = with_ai[:n]
    t_stat, t_p = paired_t_test(b, a)
    plus, minus, sign_p = sign_test(a, b)

    lines.append(f"  baseline_mean: {mean(b):.6f}")
    lines.append(f"  with_ai_mean: {mean(a):.6f}")
    lines.append(f"  paired_t_stat: {t_stat:.6f}")
    lines.append(f"  paired_t_p_approx: {t_p:.6f}")
    lines.append(f"  sign_test_plus: {plus}")
    lines.append(f"  sign_test_minus: {minus}")
    lines.append(f"  sign_test_p: {sign_p:.6f}")
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze A3 study data")
    parser.add_argument("--input", required=True, help="Path to responses_export.csv")
    parser.add_argument("--outdir", default="analysis_output", help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_path)
    required = {"participant_id", "condition", "correct", "reaction_time_seconds", "confidence", "trial_id"}
    if not rows:
        raise ValueError("Input CSV has no rows")
    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {sorted(missing)}")

    summary_rows = participant_summary(rows)
    write_summary_csv(summary_rows, outdir / "participant_summary.csv")

    report = []
    report.append("A3 Statistical Analysis Summary")
    report.append("=" * 40)
    report.append(f"Input file: {input_path}")
    report.append(f"Rows: {len(rows)}")
    report.append("")
    report.append("Statistical notes:")
    report.append("- Paired t-test p-values use a normal approximation.")
    report.append("- A paired sign test is also reported as a robust non-parametric alternative.")
    report.append("")

    b_acc, a_acc = collect_pairs(summary_rows, "accuracy")
    b_rt, a_rt = collect_pairs(summary_rows, "mean_rt")
    b_cf, a_cf = collect_pairs(summary_rows, "mean_confidence")

    report.extend(metric_report_block("accuracy", b_acc, a_acc))
    report.extend(metric_report_block("reaction_time", b_rt, a_rt))
    report.extend(metric_report_block("confidence", b_cf, a_cf))

    (outdir / "analysis_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("Analysis complete.")
    print(f"Saved: {outdir / 'participant_summary.csv'}")
    print(f"Saved: {outdir / 'analysis_report.txt'}")


if __name__ == "__main__":
    main()
