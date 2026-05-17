"""
settings.py — Django project settings for chap02 (basics).

Chapter context:
  chap02 introduces the first real Celery task: send_message.  The
  message app is registered here so Django can discover its model and task.
  The Celery settings at the bottom connect the broker and result backend;
  everything else is standard Django configuration.
"""

from pathlib import Path
import os

# Absolute path to the directory that contains manage.py.
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
    # The Message domain app — contains models, tasks, views, templates.
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
# Values are injected by Docker Compose.  The fallback addresses the Redis
# service by its Docker Compose service name ('redis'), which Docker's
# internal DNS resolves automatically within the Compose network.
#
# Because celery.py calls:
#   app.config_from_object('django.conf:settings', namespace='CELERY')
# every CELERY_* key here is mapped to its Celery counterpart by stripping
# the prefix:
#   CELERY_BROKER_URL     → broker_url   (where tasks are queued)
#   CELERY_RESULT_BACKEND → result_backend (where return values are stored)
CELERY_BROKER_URL     = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND", "redis://redis:6379/0")
