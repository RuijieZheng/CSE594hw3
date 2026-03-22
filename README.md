# CSE594 Assignment 3 Submission Package

This repository contains a complete, runnable package for Assignment 3 with:
- Baseline interface (without AI assistance)
- AI-assisted interface
- Backend logging in SQLite
- Data export endpoint
- Statistical analysis pipeline
- Submission final markdown

## Quick Start

## 1) Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Configure environment variables
```powershell
$env:FLASK_SECRET_KEY="replace_with_random_secret"
$env:ADMIN_TOKEN="replace_with_secure_admin_token"
$env:TRIALS_PER_PARTICIPANT="6"
```

## 3) Run app
```powershell
python app/app.py
```

Open `http://127.0.0.1:5000`

This project is a web app (browser-based), not a desktop executable.

## 3.1) Where to see running results
- Study interface: `http://127.0.0.1:5000`
- Start form page: `http://127.0.0.1:5000/start`
- Completion page appears after all trials are submitted
- Data export result (JSON): `http://127.0.0.1:5000/admin/export?token=YOUR_ADMIN_TOKEN`

## 4) Two conditions for MTurk deployment
- Baseline (without AI): select `Without AI (Baseline)` in start form
- AI-assisted: select `With AI Assistance` in start form

You can also host two separate links by pre-filling condition query in your MTurk setup instructions.

### Recommended MTurk External Survey setup (best practice)
Use dedicated URLs so each HIT is pinned to one condition and MTurk parameters are preserved:

- Baseline URL: `https://YOUR-APP-DOMAIN/mturk/baseline`
- With-AI URL: `https://YOUR-APP-DOMAIN/mturk/with_ai`

How this works:
- MTurk provides `workerId`, `assignmentId`, `hitId`, and `turkSubmitTo` in query params.
- Your web app runs the study flow and logs responses.
- Completion page submits back to MTurk using external submit with `assignmentId` + `surveyCode`.

Important testing note:
- In preview mode, MTurk uses `ASSIGNMENT_ID_NOT_AVAILABLE`; this will not show final MTurk submit button.
- Always test the full submit flow after clicking **Accept HIT** in Worker Sandbox.

## 5) Replace study data from Assignment 2
Update `data/trials.csv` with your own trials.
Required columns:
- trial_id
- prompt
- gold_answer
- ai_suggestion
- difficulty (optional)

## 6) Export data after collection
Call endpoint in browser:

`http://127.0.0.1:5000/admin/export?token=YOUR_ADMIN_TOKEN`

This generates `data/responses_export.csv`.

## 7) Run analysis for A3-2
```powershell
python analysis/analyze.py --input data/responses_export.csv --outdir analysis/analysis_output
```

## Submission Files
See `submission_materials/` for:
- Final submission markdown: `submission_materials/FINAL_SUBMISSION.md`

## Notes for Grading
- Backend stores participant/session/trial records.
- Each participant gets sampled trials (not all get identical trial sets).
- Includes confidence and reaction-time logs as additional measurements.
