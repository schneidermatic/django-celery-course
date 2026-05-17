"""
celerytask.py — Celery application entry point for the standalone worker service.

Both worker_urgent and worker_default Docker containers are built from the
same worker01 image and both import this file.  The only difference between
the two workers is the queue they subscribe to (-Q flag in docker-compose.yml).

Chapter context (chap05 — priority queues):
  worker_urgent:  celery -A celerytask worker -Q urgent   (fast lane)
  worker_default: celery -A celerytask worker -Q default  (priority-ordered lane)

  The 'default' queue uses Redis priority sub-queues (default:0 … default:9).
  For that feature to work, the Celery instance on the WORKER side must also
  load broker_transport_options — which is done in celeryconfig.py loaded
  below.  Without matching broker_transport_options on the worker, it would
  only poll the bare 'default' key while tasks sit unread in 'default:5' and
  'default:9'.

See chap03/worker01/celerytask.py for a full explanation of the standalone
worker pattern (django.setup() ordering, PYTHONPATH volume mount, etc.).
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Must run before importing Celery so the ORM is ready when autodiscover_tasks
# imports tasks.py (which imports models.py).
django.setup()

from celery import Celery

app = Celery('worker01')

# celeryconfig.py in this directory defines broker_url, result_backend, AND
# broker_transport_options.  The transport options must match what Django's
# settings.py sends — otherwise the worker subscribes to the wrong Redis keys.
app.config_from_object('celeryconfig')

# It looks for tasks.py in the listed modules and imports them, which registers the tasks with the Celery app.
# This is necessary for the worker to know about the tasks defined in those modules.  In this case,
# it will look for message.tasks and import it, which allows the worker to execute tasks defined there.
app.autodiscover_tasks(['message'])
