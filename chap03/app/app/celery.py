"""
celery.py — Celery application entry point for the Django project.

This module creates the single Celery application instance used by the Django
web process.  It is imported at Django startup via app/app/__init__.py.

Chapter context (chap03 — standalone worker):
  In this chapter the Celery worker runs as a completely separate Docker
  service with its own image (worker01/).  That service does NOT import this
  file; instead it creates its own Celery instance in worker01/celerytask.py.
  Both instances connect to the same Redis broker, so tasks dispatched here
  are picked up and executed by the standalone worker.

  The Django-side app object created here is used only for dispatching tasks
  (via .delay()) — not for executing them.

Startup sequence:
  1. Django launches → loads app/app/__init__.py.
  2. That file imports celery_app from here → this module runs.
  3. The Celery instance reads settings and registers tasks via autodiscovery.
  4. When a view calls .delay(), this instance serialises the call and writes
     it to Redis.  The standalone worker picks it up from there.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery("app")

# Read Celery config from Django settings (CELERY_* prefix → stripped key).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in all INSTALLED_APPS so the dispatcher knows their names
# and can serialise them correctly when writing to the broker.
app.autodiscover_tasks()
