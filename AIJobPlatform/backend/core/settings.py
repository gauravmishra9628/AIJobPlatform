import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-this-secret-key-before-deploying-ai-job-portal",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'daphne',  # WebSocket support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'accounts',
    'jobs',
]

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
USE_REDIS = os.environ.get("USE_REDIS", "False") == "True"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.SimpleCorsMiddleware',
    'core.middleware.ApiRateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    parsed_database_url = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_database_url.path.lstrip("/"),
            "USER": parsed_database_url.username or "",
            "PASSWORD": parsed_database_url.password or "",
            "HOST": parsed_database_url.hostname or "",
            "PORT": parsed_database_url.port or "",
            "OPTIONS": {"sslmode": os.environ.get("POSTGRES_SSLMODE", "require")},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get("SQLITE_DB_PATH", BASE_DIR / 'db.sqlite3'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

JWT_ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)
EMAIL_VERIFICATION_MAX_AGE = int(timedelta(hours=24).total_seconds())

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "False") == "True"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 2
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "False") == "True"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "False") == "True"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_SECURE_HSTS_PRELOAD", "False") == "True"
API_RATE_LIMIT_PER_MINUTE = int(os.environ.get("API_RATE_LIMIT_PER_MINUTE", "120"))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get("DATA_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get("FILE_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024)))
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "AI Job Portal <noreply@example.com>")

# Channels & WebSockets Configuration
ASGI_APPLICATION = "core.asgi.application"

if USE_REDIS:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache" if USE_REDIS else "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": REDIS_URL if USE_REDIS else "aijobplatform-local-cache",
        "KEY_PREFIX": os.environ.get("CACHE_KEY_PREFIX", "aijobplatform"),
        "TIMEOUT": int(os.environ.get("CACHE_TIMEOUT_SECONDS", "300")),
    }
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# API Keys for External Services
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_GEMINI_KEY = os.environ.get("GOOGLE_GEMINI_KEY", "")
ENABLE_SENTENCE_TRANSFORMERS = os.environ.get("ENABLE_SENTENCE_TRANSFORMERS", "False") == "True"
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY", "")
ADZUNA_API_ID = os.environ.get("ADZUNA_API_ID", "")
ADZUNA_API_KEY = os.environ.get("ADZUNA_API_KEY", "")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")
GOOGLE_JOBS_API_KEY = os.environ.get("GOOGLE_JOBS_API_KEY", "")
LINKEDIN_JOBS_API_KEY = os.environ.get("LINKEDIN_JOBS_API_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
