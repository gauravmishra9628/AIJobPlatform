# AI Job Portal Django Authentication

## Project structure

```text
backend/
  manage.py
  requirements.txt
  .env.example
  core/
    settings.py
    urls.py
    asgi.py
    wsgi.py
  accounts/
    admin.py
    apps.py
    authentication.py
    decorators.py
    emails.py
    managers.py
    models.py
    tokens.py
    urls.py
    views.py
    migrations/
```

## Features

- Student and recruiter signup.
- Email-only login with a custom Django user model.
- Admin role plus Django admin panel at `/admin/`.
- Login, logout, JWT access and refresh tokens.
- Email verification and resend verification email.
- Forgot password and password reset.
- Role-based dashboard endpoints.
- Secure session cookie settings and password validation.

## Setup

```bash
cd AIJobPlatform/backend
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

During local development, emails print to the console unless SMTP environment variables are configured.

## API endpoints

Base path: `/api/auth/`

- `POST signup/`
- `POST login/`
- `POST logout/`
- `POST token/refresh/`
- `GET verify-email/<token>/`
- `POST verify-email/resend/`
- `POST password/forgot/`
- `POST password/reset/<token>/`
- `GET me/`
- `GET dashboard/student/`
- `GET dashboard/recruiter/`
- `GET dashboard/admin/`

Protected endpoints expect:

```http
Authorization: Bearer <access-token>
```

## Example signup

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

Recruiter signup uses `"role": "recruiter"` and may include `"company_name"`.
