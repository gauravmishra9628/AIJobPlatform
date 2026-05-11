# AIJobPlatform

AIJobPlatform is a LinkedIn-style job and networking platform built with a
Django REST backend and a React + Vite frontend. It supports student,
recruiter, and admin workflows for job discovery, resume analysis, application
tracking, recruiter dashboards, AI-assisted career guidance, and messaging.

The active application lives in `AIJobPlatform/`. The root `legacy/` directory
contains older starter files kept only for reference.

## Tech Stack

- Backend: Django 5, Django REST Framework, Django Channels, SQLite
- Frontend: React 18, Vite, Axios, React Router, Framer Motion, Recharts
- Auth: Custom Django user model with JWT-style access and refresh tokens
- Realtime: Django Channels with an in-memory channel layer for development
- AI and integrations: OpenAI/Gemini-ready settings, external job API hooks,
  resume parsing and scoring utilities

## Project Structure

```text
.
|-- AIJobPlatform/
|   |-- backend/
|   |   |-- accounts/        # Custom user model, auth, profiles, email flows
|   |   |-- core/            # Django settings, routing, middleware, root URLs
|   |   |-- jobs/            # Jobs, resumes, applications, AI features, chat
|   |   |-- manage.py
|   |   `-- requirements.txt
|   |-- frontend/
|   |   |-- src/
|   |   |   |-- components/  # Dashboard, AI, chat, notification components
|   |   |   |-- api.js       # Frontend API client
|   |   |   |-- App.jsx
|   |   |   `-- main.jsx
|   |   |-- package.json
|   |   `-- vite.config.js
|   `-- FEATURES.md          # Detailed feature inventory and roadmap ideas
|-- legacy/                  # Old reference files
|-- package.json             # Root-level shared frontend dependencies
`-- README.md
```

## Main Features

- Secure signup, login, logout, token refresh, email verification, password
  reset, and protected API routes.
- Role-aware dashboards for students, recruiters, and admins.
- Student profiles with skills, education, experience, and profile media.
- Recruiter job posting, applicant review, and application status updates.
- Resume upload, latest-resume lookup, ATS scoring, and AI resume analysis.
- Personalized job recommendations and AI match scoring.
- Application tracking with status history and recruiter notes.
- Job bookmarks, notifications, interview preparation, and analytics.
- Direct messaging and realtime chat surfaces.
- External job search hooks and resume PDF generation endpoints.
- AI career tools for skill gaps, career plans, roadmaps, mock interview
  support, reputation scoring, and hiring-market insights.

## Prerequisites

- Python 3.11+ recommended
- Node.js 18+ recommended
- npm
- Optional: Redis, if you later switch Channels away from the in-memory
  development layer

## Backend Setup

From the repository root:

```bash
cd AIJobPlatform/backend
python -m venv ../../.venv
../../.venv/Scripts/python.exe -m pip install -r requirements.txt
../../.venv/Scripts/python.exe manage.py migrate
../../.venv/Scripts/python.exe manage.py createsuperuser
../../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

On macOS or Linux, replace `../../.venv/Scripts/python.exe` with
`../../.venv/bin/python`.

The backend API will run at:

```text
http://127.0.0.1:8000
```

## Frontend Setup

Open a second terminal from the repository root:

```bash
cd AIJobPlatform/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the app at:

```text
http://127.0.0.1:5173
```

## Environment Variables

The backend reads configuration from environment variables. Defaults are set for
local development, but production deployments should provide secure values.

Common backend variables:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_SSL_REDIRECT=False

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=AI Job Portal <noreply@example.com>

OPENAI_API_KEY=
GOOGLE_GEMINI_KEY=
JSEARCH_API_KEY=
ADZUNA_API_ID=
ADZUNA_API_KEY=
```

Frontend API base paths can be overridden when needed:

```env
VITE_API_AUTH_BASE=/api/auth
VITE_API_JOBS_BASE=/api/jobs
```

When using Vite's dev server with the Django backend, configure any proxy rules
in `AIJobPlatform/frontend/vite.config.js` if direct API calls need to be routed
to `http://127.0.0.1:8000`.

## API Overview

Backend routes are mounted from `AIJobPlatform/backend/core/urls.py`:

```text
/admin/       Django admin
/api/auth/    Authentication, profiles, dashboards
/api/jobs/    Jobs, resumes, applications, AI tools, chat
/media/       Uploaded media in local development
```

Important auth endpoints:

```text
POST /api/auth/signup/
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/token/refresh/
GET  /api/auth/verify-email/<token>/
POST /api/auth/verify-email/resend/
POST /api/auth/password/forgot/
POST /api/auth/password/reset/<token>/
GET  /api/auth/me/
PATCH /api/auth/profile/
GET  /api/auth/dashboard/student/
GET  /api/auth/dashboard/recruiter/
GET  /api/auth/dashboard/admin/
```

Important jobs and feature endpoints:

```text
GET  /api/jobs/
POST /api/jobs/
GET  /api/jobs/my/
POST /api/jobs/<job_id>/apply/
GET  /api/jobs/applications/
GET  /api/jobs/applications/<application_id>/
POST /api/jobs/resume/upload/
GET  /api/jobs/resume/latest/
GET  /api/jobs/recommendations/
POST /api/jobs/resume/analyze-ats/
POST /api/jobs/resume/analyze-ai/
POST /api/jobs/match/calculate/
GET  /api/jobs/bookmarks/
POST /api/jobs/bookmarks/toggle/
GET  /api/jobs/notifications/
POST /api/jobs/chat/send/
GET  /api/jobs/chat/list/
GET  /api/jobs/external-jobs/
GET  /api/jobs/student/dashboard/
GET  /api/jobs/recruiter/dashboard/
GET  /api/jobs/admin/analytics/
```

Protected endpoints expect an authorization header:

```http
Authorization: Bearer <access-token>
```

## Example Signup Payloads

Student:

```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!",
  "first_name": "Asha",
  "last_name": "Rao",
  "role": "student",
  "university_name": "Example University"
}
```

Recruiter:

```json
{
  "email": "recruiter@example.com",
  "password": "StrongPassword123!",
  "first_name": "Ravi",
  "last_name": "Mehta",
  "role": "recruiter",
  "company_name": "Example Labs"
}
```

In development, verification flows can return frontend-friendly verification
links. If SMTP is not configured, email output is printed to the backend console.

## Data Models

The backend includes model support for:

- Custom `User` and `UserProfile`
- `Job`, `JobApplication`, and `ApplicationStageLog`
- `Resume`, `ResumeAtsScore`, and `AIResumeAnalysis`
- `AIJobMatch`, `JobBookmark`, and `Notification`
- `InterviewPreparation` and `RecruiterAnalytics`
- `NetworkMessage` and chat-related data
- External job listings and OTP/password-reset support

## Development Notes

- SQLite is used for local development at `AIJobPlatform/backend/db.sqlite3`.
- Uploaded resumes and media are served from `AIJobPlatform/backend/media/`
  while `DEBUG=True`.
- The default Channels layer is in-memory, so it is suitable for local
  development only.
- The frontend stores auth tokens in `localStorage` under `aijob_tokens`.
- `AIJobPlatform/FEATURES.md` contains a broader feature inventory and roadmap.
- Generated folders such as `node_modules/`, frontend `dist/`, Python cache
  files, and local databases should generally not be committed.

## Useful Commands

Backend:

```bash
cd AIJobPlatform/backend
../../.venv/Scripts/python.exe manage.py makemigrations
../../.venv/Scripts/python.exe manage.py migrate
../../.venv/Scripts/python.exe manage.py test
../../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

Frontend:

```bash
cd AIJobPlatform/frontend
npm install
npm run dev
npm run build
npm run preview
```

## Roadmap

Potential next areas are listed in detail in `AIJobPlatform/FEATURES.md`,
including OAuth login, video interviews, coding assessments, certificate
verification, company integrations, subscription plans, live job feeds, salary
intelligence, and richer AI hiring analytics.
