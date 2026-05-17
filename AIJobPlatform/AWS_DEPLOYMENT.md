# AWS EC2 Deployment Guide

## Architecture Overview

```
                    ┌─────────────────────┐
                    │      Route 53       │
                    │   (DNS & SSL)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Application      │
                    │   Load Balancer     │
                    │   (ALB + SSL)       │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐  ┌──────▼──────┐  ┌─────────▼─────────┐
│   Frontend EC2   │  │ Backend EC2 │  │   Celery EC2      │
│   (Nginx+React)  │  │  (Gunicorn) │  │   (Worker)        │
└─────────┬─────────┘  └──────┬──────┘  └─────────┬─────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │    RDS PostgreSQL │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ElastiCache Redis │
                    └─────────────────┘
```

## Step 1: AWS Setup

### 1.1 Create VPC
```bash
# VPC with public and private subnets
Name: aijobplatform-vpc
CIDR: 10.0.0.0/16
Public Subnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
Private Subnets: 10.0.10.0/24, 10.0.20.0/24 (2 AZs)
```

### 1.2 Create RDS PostgreSQL
```
Instance: db.t3.medium
Storage: 50GB SSD
Multi-AZ: Yes (Production)
DB Name: aijobplatform
```

### 1.3 Create ElastiCache Redis
```
Type: cache.t3.medium
Nodes: 2 (Replica)
```

### 1.4 Create EC2 Instances
```
Backend: t3.medium (2 vCPU, 4GB RAM)
Frontend: t3.small (2 vCPU, 2GB RAM)
Worker: t3.small
```

## Step 2: EC2 Setup Script

SSH into each EC2 and run:

```bash
#!/bin/bash
# setup_ec2.sh

# Update and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3-pip nginx git curl

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Clone repository
cd /home/ubuntu
git clone https://github.com/yourusername/AIJobPlatform.git
cd AIJobPlatform

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Setup environment
cp .env.example .env
# Edit .env with production values

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput

# Create systemd service
sudo cp /home/ubuntu/aijobplatform/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Setup Nginx
sudo cp /home/ubuntu/aijobplatform/nginx/aws.conf /etc/nginx/sites-available/aijobplatform
sudo ln -s /etc/nginx/sites-available/aijobplatform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 3: Nginx Configuration

```nginx
# /etc/nginx/sites-available/aijobplatform

upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name aijobplatform.com www.aijobplatform.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aijobplatform.com www.aijobplatform.com;

    ssl_certificate /etc/letsencrypt/live/aijobplatform.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aijobplatform.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # Frontend static files
    location / {
        root /home/ubuntu/aijobplatform/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Admin
    location /admin/ {
        proxy_pass http://backend;
    }

    # Media files
    location /media/ {
        proxy_pass http://backend;
        expires 30d;
    }
}
```

## Step 4: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d aijobplatform.com -d www.aijobplatform.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Step 5: Gunicorn Service

```ini
# /home/ubuntu/aijobplatform/gunicorn.service

[Unit]
Description=AI Job Platform Gunicorn
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/aijobplatform/backend
Environment="PATH=/home/ubuntu/aijobplatform/backend/venv/bin"
ExecStart=/home/ubuntu/aijobplatform/backend/venv/bin/gunicorn \
    --access-logfile - \
    --error-logfile - \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    core.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## Step 6: Environment Variables

Create `/home/ubuntu/aijobplatform/backend/.env`:

```env
# Django
DJANGO_SECRET_KEY=your-very-long-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=aijobplatform.com,www.aijobplatform.com
DJANGO_ENV=production

# Database
DATABASE_URL=postgres://user:password@your-rds-endpoint.rds.amazonaws.com:5432/aijobplatform

# Redis
REDIS_URL=redis://your-redis-endpoint.cache.amazonaws.com:6379/0

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# AI
OPENAI_API_KEY=sk-xxxxx

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxx

# Sentry
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

## Step 7: Monitoring Setup

### CloudWatch Logs
```bash
# Install CloudWatch agent
sudo apt install -y amazon-cloudwatch-agent

# Configure
sudo cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "aijobplatform/nginx"
          },
          {
            "file_path": "/home/ubuntu/aijobplatform/backend/server.log",
            "log_group_name": "aijobplatform/django"
          }
        ]
      }
    }
  }
}
EOF
```

### Prometheus + Grafana (Optional)
Use AWS Managed Prometheus and Grafana or install on EC2.

## Step 8: Security Hardening

```bash
# SSH Key-based auth only
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PubkeyAuthentication yes

# Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## Step 9: Backup Strategy

### RDS Automated Backups
- Enable auto backup in RDS console
- Retention: 7 days

### S3 for Media Files
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'aijobplatform-media'
AWS_S3_REGION_NAME = 'us-east-1'
```

## Cost Estimate (Monthly)

| Resource | Specification | Cost |
|----------|---------------|------|
| EC2 t3.medium (Backend) | 2x | ~$50 |
| EC2 t3.small (Frontend) | 1x | ~$15 |
| EC2 t3.small (Worker) | 1x | ~$15 |
| RDS db.t3.medium | 50GB | ~$80 |
| ElastiCache t3.medium | 2 nodes | ~$60 |
| ALB | 1 | ~$25 |
| Data Transfer | ~100GB | ~$10 |
| Route 53 | 1 hosted zone | $0.50 |
| **Total** | | **~$255/month** |

## Quick Deploy Script

```bash
#!/bin/bash
# deploy.sh - Run from local machine

# Build frontend
cd AIJobPlatform/frontend
npm run build
cd ..

# Sync to S3 (static files)
aws s3 sync AIJobPlatform/frontend/dist s3://your-bucket --delete

# SSH and deploy to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip << 'EOF'
    cd /home/ubuntu/aijobplatform
    git pull origin main
    cd backend
    source venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py collectstatic --noinput
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
EOF
```

---

## Alternative: AWS Lightsail

If budget is tight, use AWS Lightsail:

```
- 4GB RAM, 2 vCPU, 80GB SSD
- Fixed IP + SSL
- ~$40/month
- Includes networking
```

Perfect for MVP/production until traffic grows!