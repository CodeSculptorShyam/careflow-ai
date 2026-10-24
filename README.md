# CareFlow AI — Healthcare Appointment & Follow-up Assistant

A Streamlit prototype for clinic appointment administration. It supports appointment creation and status tracking, follow-up task management, and an AI-assisted reminder generator.

## Features
- Appointment dashboard with total, upcoming, pending follow-up, and completed metrics
- Add appointments and update status
- Add follow-up tasks with due dates and priority
- Generate appointment reminder text using Gemini when an API key is configured
- Clearly labelled local template fallback if Gemini is not configured or unavailable
- SQLite persistence for demo appointments and tasks

## Safety and privacy
- Use fictional demo data only.
- Do not enter real patient information or sensitive medical details.
- This application does not diagnose, triage, or recommend treatment.
- Reminder messages should be reviewed by a human before use.
- Never commit API keys or `.env` files to GitHub.

## Run locally
Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install and run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

The app works in template mode without an API key.

## Enable Gemini
1. Obtain an API key from Google AI Studio.
2. Set an environment variable named `GEMINI_API_KEY`.
3. Restart Streamlit.

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="your_key_here"
streamlit run app.py
```

macOS/Linux:
```bash
export GEMINI_API_KEY="your_key_here"
streamlit run app.py
```

Do not upload your API key to GitHub.

## Deploy
1. Push this folder to a GitHub repository.
2. Create a Streamlit Community Cloud app and select `app.py`.
3. Add `GEMINI_API_KEY` in the deployment's Secrets settings if you want live AI generation.
4. Test the public URL in a private/incognito window.
5. Keep demo data fictional. For a production healthcare system, add authentication, access controls, encryption, audit logging, retention policies, and an appropriate privacy/security review.

## Suggested demo flow
1. Add a fictional appointment.
2. Show the dashboard count update.
3. Change appointment status.
4. Generate a reminder and show the output.
5. Add a follow-up task and mark it complete.
6. Explain the AI integration and fallback behavior.
