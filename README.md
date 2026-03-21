# CSE594hw3

## Render Deploy Notes

This repository contains the app under `a3_submission/`.

If you deploy with Render Web Service (manual settings), use either of these options:

1. Preferred:
- Root Directory: `a3_submission`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

2. Root-level fallback (if Root Directory is left empty):
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn render_wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`