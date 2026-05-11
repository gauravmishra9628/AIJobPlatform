# AIJobPlatform

Modern LinkedIn-style AI job platform with a Django backend and React frontend.

## Directory Structure

```text
AIJobPlatform/
  backend/          Django API, auth, users, jobs, resumes, recommendations
  frontend/         React + Vite web application
legacy/            Old starter files kept only for reference
.venv/             Local Python virtual environment
```

The active application lives in `AIJobPlatform/`. The root `legacy/` folder only
keeps old scratch files for reference.

## Run Locally

Backend:

```bash
cd AIJobPlatform/backend
../../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

Frontend:

```bash
cd AIJobPlatform/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Login Notes

In development, signup returns a frontend verification link so you can verify a
new account immediately from the UI. In production, users should verify through
email.

## Current Feature Set

- JWT signup, login, email verification, token refresh, and protected routes.
- AI-style job recommendations from resume/profile keyword overlap.
- Resume upload with extracted text, detected skills, and improvement notes.
- Student dashboard with profile strength, recommendations, applications, and career roadmap.
- Recruiter portal with job posting, applicant review, and shortlist/reject workflow.
- Networking messages between applicants and recruiters.
- Responsive React UI backed by Django API endpoints.
