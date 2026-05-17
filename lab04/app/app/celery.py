"""
celery.py — Celery application entry point for the Django project.

This module creates the Celery application instance used by the Django web
process to dispatch tasks.  It is imported at startup via app/app/__init__.py.

Chapter context (chap04 — task routing):
  chap04 introduces CELERY_TASK_ROUTES in settings.py, which maps each fully-
  qualified task name to a dedicated queue.  This Celery instance reads that
  routing table automatically when app.config_from_object() loads settings,
  so the view code does not need to specify a queue — it just calls .delay()
  and the routing happens transparently.

  The two queues ('fast' and 'bulk') are each served by a dedicated worker
  container (worker_fast and worker_bulk in docker-compose.yml), so slow
  newsletter tasks can never block time-sensitive transactional ones.

Startup sequence:
  1. Django launches → loads app/app/__init__.py.
  2. That file imports celery_app from here → this module runs.
  3. The Celery instance reads settings including CELERY_TASK_ROUTES.
  4. autodiscover_tasks() registers message.tasks.send_transactional and
     message.tasks.send_newsletter.
  5. The standalone workers (worker01 image) import celerytask.py instead.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery("app")

# CELERY_TASK_ROUTES (defined in settings.py) is picked up here automatically.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
