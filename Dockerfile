FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY AIJobPlatform/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY AIJobPlatform/backend/ .

RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]
