# Analysis Usage

## 1) Export data from app backend
After collecting data, call:

`/admin/export?token=YOUR_ADMIN_TOKEN`

This creates `data/responses_export.csv`.

## 2) Run analysis
From project root:

```powershell
python analysis/analyze.py --input data/responses_export.csv --outdir analysis/analysis_output
```

## 3) Outputs
- `analysis/analysis_output/participant_summary.csv`
- `analysis/analysis_output/analysis_report.txt`

These files can be included in A3-2 submission.
