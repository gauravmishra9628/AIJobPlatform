# Deployment Guide

## Frontend: Vercel

1. Import the repository in Vercel.
2. Set the root directory to `AIJobPlatform/frontend`.
3. Use:
   - Build command: `npm run build`
   - Output directory: `dist`
4. Add environment variables:
   - `VITE_API_AUTH_BASE=https://your-backend.onrender.com/api/auth`
   - `VITE_API_JOBS_BASE=https://your-backend.onrender.com/api/jobs`

`frontend/vercel.json` is already configured for Vite client-side routing.

## Backend: Render

1. Create a new Render blueprint from `AIJobPlatform/backend/render.yaml`, or create a web service manually.
2. Set the root directory to `AIJobPlatform/backend`.
3. Use:
   - Build command: `pip install -r requirements.txt && python manage.py migrate`
   - Start command: `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
4. Add environment variables:
   - `DJANGO_DEBUG=False`
   - `DJANGO_SECRET_KEY=<generated-secret>`
   - `DJANGO_ALLOWED_HOSTS=your-backend.onrender.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app`
   - `DJANGO_SESSION_COOKIE_SECURE=True`
   - `DJANGO_CSRF_COOKIE_SECURE=True`
   - `DJANGO_SECURE_SSL_REDIRECT=True`
   - `DJANGO_SECURE_HSTS_SECONDS=31536000`
   - `DATABASE_URL=<postgres-connection-string>`
   - Optional AI/email keys: `OPENAI_API_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

## Backend: Railway

1. Create a Railway project and connect this repository.
2. Set the service root to `AIJobPlatform/backend`.
3. Add a PostgreSQL plugin.
4. Set the same environment variables listed above.
5. Use the start command from `backend/Procfile`.

## Database: PostgreSQL

The backend reads `DATABASE_URL`. If present, it uses PostgreSQL with SSL. If absent, it falls back to local SQLite for development.

After changing database settings, run:

```bash
python manage.py migrate
```

## Production Checks

- Keep all secrets in hosting environment variables.
- Use HTTPS-only frontend and backend URLs.
- Set secure cookies in production.
- Configure SMTP or a transactional email provider.
- Confirm resume uploads reject unsupported extensions and files above the configured limit.
- Confirm `/api/` returns `429` after the configured rate limit.
