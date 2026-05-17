"""
settings.py — Django project settings for chap05 (priority queues).

Chapter context:
  The key addition in chap05 is CELERY_BROKER_TRANSPORT_OPTIONS, which
  activates Redis priority sub-queues.  Without this setting, writing a
  task with apply_async(priority=5) would still succeed but the priority
  value would be silently ignored — Redis would treat all messages in the
  queue as equal.

  IMPORTANT: Both the dispatcher (this Django process) and the consumer
  (the standalone worker in worker01/) must have identical broker_transport_options.
  If the worker lacks this setting, it reads from the bare 'default' key in
  Redis while the dispatcher writes to 'default:5' and 'default:9' — those
  messages would never be consumed.  See worker01/celeryconfig.py for the
  matching configuration on the worker side.
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

# Priority queue configuration for the Redis broker.
#
# When a task is dispatched with apply_async(priority=N), Celery uses these
# settings to determine the Redis key where the message is stored:
#
#   queue='default', priority=5  →  Redis key 'default:5'
#   queue='default', priority=9  →  Redis key 'default:9'
#
# The worker reads from all 10 sub-keys (default:0 through default:9) and
# always serves lower-numbered (= higher-priority) messages first.
#
#   priority_steps  — list of valid integer priorities (0–9 here).
#                     Lower number = higher priority (processed sooner).
#                     0 is the highest possible priority; 9 is the lowest.
#   sep             — character inserted between queue name and priority
#                     number to form the Redis key (e.g. 'default' + ':' + '5').
#   queue_order_strategy — 'priority' tells Celery to merge and sort all
#                          sub-queues by priority before handing tasks to
#                          the worker, rather than round-robining.
#
# NOTE: The 'urgent' queue does NOT use priority buckets.  It is a simple
# FIFO queue — tasks arrive there in submission order and are processed in
# that same order.  Priority ordering only applies within the 'default' queue.
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}
