"""
settings.py — Django project settings for chap04 (task routing).

Chapter context:
  chap04 introduces CELERY_TASK_ROUTES, which tells Celery which queue to use
  for each task.  Two dedicated workers (worker_fast and worker_bulk) each
  subscribe to exactly one queue, so newsletter tasks (slow, bulk) can never
  block transactional tasks (fast, time-sensitive).

  The routing is configured once here; the view code simply calls .delay()
  without specifying a queue, and Celery applies the route automatically.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Injected by Docker Compose — no secrets in source code.
SECRET_KEY    = os.environ.get("SECRET_KEY")
DEBUG         = os.environ.get("DEBUG")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'message',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

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

WSGI_APPLICATION = 'app.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Celery configuration
# ---------------------------------------------------------------------------
CELERY_BROKER_URL     = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND", "redis://redis:6379/0")

# Task routing table — maps each fully-qualified task name to a named queue.
# When the view calls send_transactional.delay(m.id), Celery looks up
# 'message.tasks.send_transactional' in this dict and writes the message
# to the 'fast' queue in Redis.  The worker_fast container subscribes to
# 'fast' (via -Q fast) and worker_bulk subscribes to 'bulk' (via -Q bulk).
#
# This means:
#   - send_transactional → fast queue → worker_fast (sleep 1s)
#   - send_newsletter    → bulk queue → worker_bulk  (sleep 5s)
#
# Slow newsletter tasks never block worker_fast from processing the next
# transactional task immediately.
CELERY_TASK_ROUTES = {
    'message.tasks.send_transactional': {'queue': 'fast'},
    'message.tasks.send_newsletter':    {'queue': 'bulk'},
}
