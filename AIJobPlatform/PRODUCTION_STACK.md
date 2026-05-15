# Production Stack

## Services

- `frontend`: Vite build served by Nginx with `/api/` proxied to Django.
- `backend`: Django ASGI app served by Daphne.
- `celery`: background worker for async jobs.
- `postgres`: production database target.
- `redis`: cache, channel layer, and Celery broker/result backend.

## Local Docker Run

```bash
cd AIJobPlatform
docker compose up --build
```

Then apply migrations:

```bash
docker compose exec backend python manage.py migrate
```

Frontend: `http://localhost:5173`
Backend: `http://localhost:8000`

## Billing

The subscription API supports Stripe and Razorpay checkout intent creation:

- `GET /api/jobs/billing/overview/`
- `POST /api/jobs/billing/checkout/`
- `POST /api/jobs/billing/checkout/confirm/`
- `POST /api/jobs/billing/usage/`

Set provider secrets in `.env` or your production secret manager:

- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

The dev flow records simulated confirmations so the UI can be tested without live payment credentials.
