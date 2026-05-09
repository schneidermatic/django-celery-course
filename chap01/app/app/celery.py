"""
celery.py — Celery application entry point for the Django project.

This module creates the single Celery application instance that both Django
and any connected workers share.  It is imported at Django startup via
app/app/__init__.py, ensuring Celery is ready before the first request arrives.

Chapter context (chap01 — skeleton):
  No custom tasks exist yet.  The sole purpose of this chapter is to verify
  that the Celery/Redis pipeline is alive end-to-end before adding business
  logic in chap02.

How the startup sequence works:
  1. Django launches and loads app/app/__init__.py.
  2. That file imports `celery_app` from here, triggering this module to run.
  3. The Celery instance is created, connected to Django settings, and ready.
  4. A Celery worker (separate process/container) also imports this module
     directly, so both processes share an identical configuration.
"""

import os
from celery import Celery

# Provide a fallback so this module works when imported by a standalone Celery
# worker process that starts before Django's normal startup machinery runs.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Create the Celery application.  The name 'app' matches the Django project
# package so Celery's internal task naming (e.g. 'app.tasks.my_task') and
# log output are consistent with the project layout.
app = Celery('app')

# Pull Celery configuration from Django's settings module, but only keys that
# begin with 'CELERY_'.  The namespace prefix keeps Celery settings visually
# separated from Django's own settings in settings.py.
#
# Mapping examples (Django setting → Celery key):
#   CELERY_BROKER_URL      → broker_url
#   CELERY_RESULT_BACKEND  → result_backend
app.config_from_object('django.conf:settings', namespace='CELERY')

# Scan every app listed in INSTALLED_APPS for a tasks.py module and register
# any @shared_task functions found there.  Without this call Celery would not
# know about custom tasks and would refuse to route messages to them.
app.autodiscover_tasks()
