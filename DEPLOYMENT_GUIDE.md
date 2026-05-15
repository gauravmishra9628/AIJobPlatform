# AI Job Platform - Deployment Guide

## Quick Start (Development)

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL (optional, SQLite for dev)
- Redis (optional, in-memory for dev)

### Backend Setup
```bash
cd AIJobPlatform/backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### Frontend Setup
```bash
cd AIJobPlatform/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

```bash
cd AIJobPlatform

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Manual Production Setup

#### Backend (Render/Railway/VPS)

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Set environment variables**
```bash
export DEBUG=False
export DJANGO_SECRET_KEY=your-secure-secret-key
export DJANGO_ALLOWED_HOSTS=yourdomain.com
export DATABASE_URL=postgresql://user:pass@host:5432/db
export REDIS_URL=redis://host:6379/0
```

3. **Run migrations**
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

4. **Start with Gunicorn**
```bash
gunicorn core.asgi:application -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend (Vercel/Netlify)

1. **Build for production**
```bash
cd frontend
npm run build
```

2. **Deploy to Vercel**
```bash
npm i -g vercel
vercel
```

3. **Or deploy to Netlify**
```bash
npm run build
# Drag dist folder to Netlify
```

---

## Environment Variables

### Backend (.env)
```env
DEBUG=False
DJANGO_SECRET_KEY=your-secret-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
OPENAI_API_KEY=sk-...
GOOGLE_GEMINI_KEY=...
```

### Frontend (.env)
```env
VITE_API_AUTH_BASE=/api/auth
VITE_API_JOBS_BASE=/api/jobs
```

---

## Production Checklist

- [ ] Set DEBUG=False
- [ ] Use strong DJANGO_SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Use PostgreSQL (not SQLite)
- [ ] Use Redis for caching
- [ ] Set up Celery for background tasks
- [ ] Configure HTTPS/SSL
- [ ] Set up proper CORS settings
- [ ] Implement rate limiting
- [ ] Set up logging (Sentry)
- [ ] Configure backup strategy
- [ ] Test all features in production

---

## Monitoring & Maintenance

### Logs
```bash
# Docker logs
docker-compose logs -f backend

# Application logs
tail -f logs/django.log
```

### Health Check
```bash
curl http://localhost:8000/api/jobs/
```

### Database Backup
```bash
# PostgreSQL
pg_dump -U user dbname > backup.sql

# SQLite (development)
cp db.sqlite3 db.sqlite3.backup
```

### Update Application
```bash
# Pull latest code
git pull

# Install updates
pip install -r requirements.txt
npm install

# Run migrations
python manage.py migrate

# Restart services
docker-compose restart
```

---

## Troubleshooting

### Common Issues

1. **Port already in use**
```bash
# Find process
lsof -i :8000
# Kill it
kill -9 PID
```

2. **Database migration errors**
```bash
python manage.py migrate --fake-initial
```

3. **Static files not loading**
```bash
python manage.py collectstatic --noinput
```

4. **Memory issues**
```bash
# Increase worker memory
gunicorn --workers 2 --worker-class=uvicorn.workers.UvicornWorker --max-requests=1000
```

---

## Tech Stack Summary

| Component | Technology |
|-----------|------------|
| Backend | Django 5 + DRF |
| Database | PostgreSQL |
| Cache | Redis |
| Frontend | React 18 + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Auth | JWT |
| Deployment | Docker, Vercel, Render |

---

## Security Checklist

- [ ] HTTPS enabled
- [ ] SECRET_KEY changed
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CSRF protection
- [ ] File upload validation
- [ ] Strong password policy
- [ ] 2FA available

---

## Performance Optimization

1. **Database**
   - Add indexes on frequently queried fields
   - Use select_related/prefetch_related
   - Implement pagination

2. **Caching**
   - Cache API responses
   - Use Redis for session storage
   - Implement cache invalidation

3. **Frontend**
   - Lazy load components
   - Optimize images
   - Use code splitting

4. **Static Files**
   - Use CDN (CloudFront)
   - Enable compression
   - Set cache headers