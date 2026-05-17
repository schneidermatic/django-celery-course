"""
celery.py — Celery application entry point for the Django project.

This module creates the single Celery application instance that both Django
and any connected workers share.  It is imported at Django startup via
app/app/__init__.py, ensuring Celery is ready before the first request arrives.

Chapter context (chap02 — basics):
  The instance created here powers the send_message task in
  message/tasks.py.  Both the Django web process (which dispatches tasks)
  and the celery worker container (which executes them) import this module,
  so both share the same broker URL and result backend.

Startup sequence:
  1. Django launches → loads app/app/__init__.py.
  2. That file imports celery_app from here → this module runs.
  3. Celery instance is created, reads settings, and is ready.
  4. The Celery worker (separate container) imports this module directly
     and gets the identical configuration.
"""

import os
from celery import Celery

# Provide a fallback so this module works when imported by a standalone Celery
# worker process that starts before Django's normal startup machinery runs.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# 'app' matches the Django project package name so Celery's task names
# (e.g. 'message.tasks.send_message') and log lines are consistent
# with the rest of the project.
app = Celery("app")

# Read Celery config from Django settings, limiting to keys prefixed 'CELERY_'.
# This keeps Celery settings clearly separated from Django's own settings.
#
# Mapping (Django setting → Celery key):
#   CELERY_BROKER_URL      → broker_url
#   CELERY_RESULT_BACKEND  → result_backend
app.config_from_object("django.conf:settings", namespace="CELERY")

# Scan every INSTALLED_APP for a tasks.py and register all @shared_task
# functions.  Without this, Celery would not know about send_message in
# message/tasks.py and would reject any attempt to route messages to it.
app.autodiscover_tasks()
