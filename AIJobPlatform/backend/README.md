# AI Job Platform - Backend

![CI/CD](https://github.com/yourusername/aijobplatform/actions/workflows/ci-cd.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![License](https://img.shields.io/badge/license-proprietary-orange)

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── pytest.ini
├── conftest.py
├── core/
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   ├── asgi.py              # ASGI config
│   ├── wsgi.py              # WSGI config
│   ├── middleware.py        # Custom middleware
│   ├── ai_integrations.py   # AI service integrations
│   ├── health.py            # Health check endpoints
│   └── api_versioning.py    # API versioning
├── accounts/
│   ├── models.py            # User & Profile models
│   ├── views.py             # Auth endpoints
│   ├── urls.py              # Auth routing
│   ├── decorators.py        # JWT decorators
│   ├── tokens.py            # JWT token handling
│   ├── oauth.py             # OAuth services
│   └── tests.py             # Auth tests
└── jobs/
    ├── models.py            # 60+ job-related models
    ├── views.py            # Job endpoints
    ├── urls.py             # Job routing
    ├── ai_views.py         # AI feature endpoints
    ├── serializers.py      # DRF serializers
    ├── management/
    │   └── commands/
    │       └── seed_data.py  # Test data generator
    └── tests.py            # Job tests
```

## Features

### Authentication & User Management
- Email/password authentication with JWT tokens
- Google OAuth integration
- OTP email verification
- Password reset functionality
- Role-based access (Student, Recruiter, Admin)

### Job Management
- Job posting with rich details
- Advanced search with filters
- Job recommendations
- Job bookmarks/favorites
- External job API integration

### AI Features
- Resume analysis with GPT-3.5/GPT-4
- AI Career Coach
- Resume-Job Match Scoring
- Interview question generation
- Salary prediction

### Security
- JWT authentication
- Rate limiting (60 req/min API, 10 req/min auth)
- Input sanitization
- Security headers
- Request size limits

## Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py seed_data --users=20 --jobs=50 --applications=100

# Run server
python manage.py runserver
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-xxxxx
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## Health Checks

- Health: `GET /health/`
- Readiness: `GET /ready/`

## Testing

```bash
# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration

# Run with verbose output
pytest -v
```

## Docker

```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.production.yml up --build
```

## Kubernetes

```bash
# Deploy to K8s
kubectl apply -k k8s/
```

## API Endpoints

| Category | Base Path | Features |
|----------|-----------|----------|
| Auth | `/api/auth/` | login, signup, logout, refresh, password reset |
| Jobs | `/api/jobs/` | list, detail, create, search, recommend |
| Resume | `/api/jobs/resume/` | upload, analyze, match |
| AI | `/api/jobs/ai/` | career coach, interview prep, salary prediction |
| Billing | `/api/jobs/billing/` | subscriptions, payments |

## Tech Stack

- **Framework**: Django 5.1 + DRF
- **Database**: PostgreSQL (production), SQLite (dev)
- **Cache**: Redis
- **Task Queue**: Celery
- **AI**: OpenAI, spaCy, sentence-transformers
- **Deployment**: Docker, Kubernetes

## Contributing

1. Create feature branch
2. Add tests for new features
3. Ensure all tests pass
4. Submit pull request