"""
settings.py — Django project settings for chap03 (standalone worker).

Chapter context:
  chap03 introduces the standalone worker pattern: the Celery worker runs as
  a separate Docker service (worker01/) that mounts the Django codebase as a
  volume.  From the Django perspective, the settings here are identical to
  chap02 — the architectural change is in docker-compose.yml and worker01/.
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
    # message must be listed here so Django discovers its models and tasks.
    # The standalone worker also imports message via PYTHONPATH, not INSTALLED_APPS.
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
# These settings are read by both the Django process and the standalone worker.
# The standalone worker loads this settings file via the DJANGO_SETTINGS_MODULE
# environment variable injected by Docker Compose, so there is a single source
# of truth for the broker URL.
#
# CELERY_BROKER_URL     → where tasks are written (Redis list / queue)
# CELERY_RESULT_BACKEND → where task return values are stored after execution
CELERY_BROKER_URL     = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND", "redis://redis:6379/0")
