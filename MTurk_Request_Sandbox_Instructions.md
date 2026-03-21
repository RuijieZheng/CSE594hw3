# MTurk Requester Sandbox Setup (A3-1)

## 1) Host your task interface

Your task interface must be accessible via a public URL so MTurk workers can open it.

### Option A (quick test only): use a tunneling service
- Run your app locally:
  ```powershell
  cd a3_submission
  .\.venv\Scripts\python.exe app/app.py
  ```
- Use a tunnel service (e.g., ngrok) to expose `http://localhost:5000` publicly.
  ```powershell
  ngrok http 5000
  ```
- Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`).

Notes:
- Tunnel links can be blocked by some campus/public Wi-Fi networks.
- Do not use localtunnel links that show a tunnel-password interstitial for worker data collection.

### Option B (recommended for class collection): deploy to a public host
Deploy this repository to Render so your classmates can open a stable URL without a tunnel warning page.

#### Render deployment steps (one-time)
1. Push your project to GitHub.
2. Go to Render dashboard -> New -> Blueprint.
3. Select your repository and deploy from `render.yaml`.
4. Wait for build to finish and copy the generated URL, e.g. `https://your-app.onrender.com`.
5. Verify these endpoints are reachable:
   - `https://your-app.onrender.com/start/baseline`
   - `https://your-app.onrender.com/start/with_ai`

Repository is already prepared for Render with:
- `a3_submission/render.yaml`
- `a3_submission/Procfile`
- `a3_submission/wsgi.py`
- `a3_submission/requirements.txt` (includes `gunicorn`)

---

## 2) Prepare MTurk Requester Sandbox HIT details

### Suggested HIT settings
- Title: **Human-AI Mental Health Triage Task (Sandbox)**
- Description: **Classify symptom severity from a short case description. Some versions include AI suggestions. You will do 6 trials in < 10 minutes.**
- Keywords: `mental health, classification, AI, study, survey`
- Reward: e.g. `$1.00` (adjust as you like)
- Time allotted per assignment: `30 minutes`
- HIT lifetime: `7 days` (or longer)
- Max assignments: `50` (or appropriate)

---

## 3) MTurk Requester Sandbox “External Question” HTML

Use the following HTML as the **External Question** in the MTurk task setup.

Replace `YOUR_PUBLIC_URL` with the public URL of your deployed task. For example:
- baseline:  `https://your-app.onrender.com/start/baseline`
- with AI:  `https://your-app.onrender.com/start/with_ai`

```html
<html>
  <head>
    <title>CSE594 A3: Human-AI Study</title>
    <style>
      body { font-family: Arial, sans-serif; line-height: 1.45; }
      .box { border: 1px solid #ccc; padding: 14px; margin: 14px 0; border-radius: 8px; }
      .button { background: #0066cc; color: #fff; padding: 10px 14px; text-decoration: none; border-radius: 6px; display: inline-block; }
      .warning { color: #b00; font-weight: bold; }
    </style>
  </head>
  <body>
    <h2>CSE594 A3: Mental Health Triage Task</h2>
    <p>This HIT is part of a research study comparing task performance <strong>with</strong> and <strong>without</strong> AI suggestions. Please follow the instructions below.</p>

    <div class="box">
      <p><strong>Step 1:</strong> Choose the correct link below and complete all trials.</p>
      <p>
        <a class="button" href="YOUR_PUBLIC_URL/start/baseline" target="_blank">Without AI (Baseline)</a>
        <a class="button" href="YOUR_PUBLIC_URL/start/with_ai" target="_blank">With AI Assistance</a>
      </p>
      <p class="warning">IMPORTANT:</p>
      <ul>
        <li>Complete the task in one sitting (about 8–10 minutes).</li>
        <li>Do NOT skip trials.</li>
        <li>At the end, you will receive a <strong>survey code</strong>. Copy it.</li>
      </ul>
    </div>

    <div class="box">
      <p><strong>Step 2:</strong> After finishing, enter the survey code below and submit.</p>
      <p>The code is required so we can approve your work.</p>
      <label for="survey_code">Survey code:</label><br>
      <input id="survey_code" name="survey_code" type="text" style="width: 100%; padding: 8px;" required>
    </div>

    <div class="box">
      <p><strong>Important:</strong> You must complete 6 trials in one condition before submitting. If you close the browser early, your session may not be recorded.</p>
    </div>

    <p>Once you have your survey code, paste it into the field above and submit this HIT.</p>

    <script>
      // Prevent accidental navigation away (optional)
      window.onbeforeunload = function() {
        return 'Make sure you have copied your survey code before leaving.';
      };
    </script>
  </body>
</html>
```

---

## 4) MTurk Worker Instructions (copy into MTurk task description)

**Instructions (what workers should do):**
1. Click the link for your assigned condition (with or without AI).  
2. Read the instructions on the task page.  
3. Classify each case into one of: **Low / Moderate / High / Crisis** (severity).  
4. Submit each trial and complete all 6 trials.  
5. Copy the **survey code** shown at the end of the task and paste it into this MTurk HIT.  
6. Submit the HIT.

**Notes for workers:**
- The task takes about 8–10 minutes.
- Do your best; there is no single correct answer for many cases.
- If the link doesn’t work, try refreshing or contact the requester.

---

## 5) MTurk Sandbox Workflow (for you)
1. Create a HIT using the **External Question** type.
2. Paste the HTML from section 3 into the HIT’s HTML content.
3. Enter the reward, duration, and lifespan settings.
4. Publish the HIT (in Sandbox, so it doesn’t cost real money).
5. Use another account as a worker (Worker Sandbox) to verify it opens and works.
6. Record the survey codes produced and confirm they appear in your backend export.

---

## 6) What you need to hand in for A3-1
✅ 2 links in the shared spreadsheet:
- Without AI link
- With AI link

✅ Your name + any comments in the spreadsheet

✅ Make sure at least 5 participants finish each condition

---

> Tip: You only need to replace `YOUR_PUBLIC_URL` in the External Question HTML above with your real public URL (for example, `https://your-app.onrender.com`).

If you want, I can also generate a ready-to-paste HTML file and a stricter MTurk HIT settings checklist (input fields, rewards, and worker constraints).