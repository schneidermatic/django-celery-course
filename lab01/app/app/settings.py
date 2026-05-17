"""
settings.py — Django project settings for chap01 (skeleton).

Chapter context:
  chap01 is a bare-bones skeleton with no custom Django app.  The only
  addition compared to a freshly generated Django project is the Celery
  connection block at the bottom.  The goal is to confirm the wiring is
  correct before building the notification feature in chap02.
"""

from pathlib import Path
import os

# Absolute path to the directory that contains manage.py.
# Used as the base for database file paths and other filesystem references.
BASE_DIR = Path(__file__).resolve().parent.parent

# All three of these sensitive/environment-specific values are injected via
# Docker Compose environment variables so no secrets appear in source code.
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
    # No custom app in chap01 — worker01 is added from chap02 onward.
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
# Both values are read from environment variables injected by Docker Compose.
# The fallback 'redis://redis:6379/0' refers to the 'redis' service defined in
# docker-compose.yml; database index 0 is used for both the broker and the
# result store to keep the setup simple.
#
# Because app/app/celery.py calls:
#   app.config_from_object('django.conf:settings', namespace='CELERY')
# every setting whose name starts with CELERY_ is automatically mapped to its
# Celery counterpart by stripping the prefix:
#   CELERY_BROKER_URL     → broker_url
#   CELERY_RESULT_BACKEND → result_backend
CELERY_BROKER_URL     = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND", "redis://redis:6379/0")
