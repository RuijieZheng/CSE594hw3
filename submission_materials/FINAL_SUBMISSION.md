# CSE594 Assignment 3 Final Submission (Markdown)

## A3-1 Deployment Links
- Without AI (Worker Sandbox): [PASTE YOUR LINK]
- With AI (Worker Sandbox): [PASTE YOUR LINK]

## Task Description
This project evaluates human task performance with and without AI assistance on a mental health triage classification task.

- Baseline condition: participants classify symptom severity without AI suggestions.
- AI-assisted condition: participants classify symptom severity with precomputed AI output from Assignment 2.

The implementation uses participant-level trial sampling so different participants do not all receive the same subset of trials.

## Interface and Backend Design Decisions
- Shared interface structure across conditions to isolate AI effect.
- Condition-specific AI panel appears only in the AI-assisted condition.
- Per-trial logging captures participant severity response, confidence, correctness, and reaction time.
- SQLite backend stores participant metadata and trial-level responses.
- Export endpoint generates a flat CSV for analysis reproducibility.
- Severity labels used in both conditions: Low, Moderate, High, Crisis.

## Study Setup
- Study type: two-condition human-subjects comparison.
- Per-participant trial count: configurable (default 6).
- Runtime target: under 10 minutes including instructions.
- Data tables:
  - participants
  - responses
  - sessions_audit

## Measurements
Primary metric:
- Severity classification performance (`correct`, aggregated as accuracy)

Additional metrics:
- Reaction time (`reaction_time_seconds`)
- Confidence rating (`confidence`, 1 to 5)

## Data Analysis Method
Analysis script: `analysis/analyze.py`

Steps:
1. Aggregate per participant and condition.
2. Compare baseline vs AI-assisted means for accuracy, reaction time, and confidence.
3. Report paired t-test (normal-approx p-value) and paired sign test.

Outputs:
- `analysis/analysis_output/participant_summary.csv`
- `analysis/analysis_output/analysis_report.txt`

## Assignment 2 Model Results Used for AI Assistance
The AI suggestions shown in the AI-assisted condition are generated from Assignment 2 outputs.

Reference metrics from `HW2/evaluation_report.txt`:
- Severity Classification Accuracy: 0.600
- Concern Classification Accuracy: 0.888
- Both Correct (Overall): 0.516

Main observed severity confusion patterns:
- Low -> Moderate: 41 cases
- Moderate -> High: 23 cases
- Crisis -> High: 21 cases
- Adjacent severity confusion accounts for 98.0% of severity errors

## Running and Verification Results (Current)
End-to-end smoke tests were executed successfully:

- Baseline flow: start session -> submit 6 trials -> completion page reached.
- AI-assisted flow: AI panel visible -> submit 6 trials -> completion page reached.
- Export endpoint: generated `data/responses_export.csv` with status `ok`.
- Analysis pipeline: generated both required analysis output files.
- Study dataset in `data/trials.csv` has been replaced with 250 Assignment 2 mental health cases.

Current sample analysis summary from smoke-test data:
- Rows analyzed: 48
- Participant summary rows: 8 (4 baseline, 4 with AI)
- Paired statistical tests: not enough paired participants yet (expected before real data collection)

## Reflection (To Be Finalized After Real Data Collection)
The final reflection will address:
- Whether Assignment 2 prediction holds under human-subject data.
- Which error patterns changed with AI assistance.
- Whether AI improved performance, speed, or confidence.
- Whether outliers or misunderstanding influenced results.

Planned hypothesis grounded in Assignment 2 findings:
- AI assistance is expected to improve classification consistency for clear Crisis and High cases.
- AI assistance may bias workers toward over-predicting severity in boundary cases (Low vs Moderate, Moderate vs High).

## Bonus Work Status
- Custom backend and logging implemented.
- Additional measurements (confidence and reaction time) implemented.
- Literature review section: [OPTIONAL, ADD IF COMPLETED]

## Reproducibility Assets Included
- Interface code: `app/`
- Data files: `data/`
- Analysis code and outputs: `analysis/`

## Runtime Access (Web)
- This system runs as a web app.
- Local URL: `http://localhost:5000`
- Start page: `http://localhost:5000/start`
- Direct baseline start link: `http://localhost:5000/start/baseline`
- Direct AI-assisted start link: `http://localhost:5000/start/with_ai`
- Export endpoint: `http://localhost:5000/admin/export?token=YOUR_ADMIN_TOKEN`

## Final Submission Checklist
- [ ] Replace placeholder study links above.
- [x] Replace sample trial dataset with Assignment 2 dataset.
- [ ] Collect at least 5 participants per condition.
- [ ] Re-run export and analysis on full collected data.
- [ ] Update reflection and final results text in this file.
