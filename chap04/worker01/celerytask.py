"""
celerytask.py — Celery application entry point for the standalone worker service.

This file creates an independent Celery instance for the worker01 service.
Both worker_fast and worker_bulk Docker containers are built from the same
worker01 image; only the -Q flag in docker-compose.yml differs between them.

Chapter context (chap04 — task routing):
  The two workers built from this file subscribe to different queues:
    worker_fast:  celery -A celerytask worker -Q fast   (handles send_transactional)
    worker_bulk:  celery -A celerytask worker -Q bulk   (handles send_newsletter)
  By subscribing to only one queue each, worker_fast is never delayed by slow
  newsletter tasks queued in 'bulk', and vice versa.

See chap03/worker01/celerytask.py for a detailed explanation of why
django.setup() must be called before importing Celery, and why a second
independent Celery instance is used here.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Initialise Django's ORM before Celery so autodiscover_tasks can safely
# import tasks.py (which imports models.py).
django.setup()

from celery import Celery

app = Celery('worker01')

# Load broker_url and result_backend from celeryconfig.py in this directory.
app.config_from_object('celeryconfig')

# Register tasks from message — this is the Django app whose tasks.py defines
# send_transactional and send_newsletter.
app.autodiscover_tasks(['message'])
