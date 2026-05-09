"""
celery.py — Celery application entry point for the Django project.

This module creates the Celery application instance used by the Django web
process to dispatch tasks.  It is imported at startup via app/app/__init__.py.

Chapter context (chap05 — priority queues + dedicated workers):
  chap05 combines two techniques from previous chapters:

  1. Queue routing (from chap04): urgent tasks go to the 'urgent' queue;
     normal and low tasks go to the 'default' queue.  Routing is done
     explicitly in views.py using apply_async(queue=...) rather than via
     CELERY_TASK_ROUTES, because the routing decision depends on runtime
     data (the priority chosen by the user), not on the task's identity.

  2. Priority ordering (new in chap05): within the 'default' queue Redis
     maintains 10 priority buckets.  CELERY_BROKER_TRANSPORT_OPTIONS in
     settings.py activates this feature.  The Celery instance created here
     picks up that setting automatically via config_from_object().

  Both the Django process (dispatcher) and the standalone workers
  (executor) must load the same broker_transport_options; the workers load
  them from worker01/celeryconfig.py.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery("app")

# CELERY_BROKER_TRANSPORT_OPTIONS (defined in settings.py) is applied here,
# enabling Redis priority sub-queues for the 'default' queue.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
