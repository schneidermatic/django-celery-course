"""
celerytask.py — Celery application entry point for the standalone worker service.

This file is the heart of the standalone worker pattern introduced in chap03.
It creates a Celery instance that is completely independent of the Django
project's own Celery instance (app/app/celery.py).

Why a second, independent Celery instance?
  The Django process and the worker process run in different Docker containers
  from different images.  The worker image does not include Django's runserver;
  it only needs to import and execute tasks.  Having its own Celery instance
  means the worker can be deployed, scaled, and updated without touching the
  Django image at all.

How the standalone worker accesses the Django ORM:
  The worker01 container mounts the Django codebase as a Docker volume and
  adds it to PYTHONPATH (see docker-compose.yml).  This means `import message`
  works inside the worker — without running Django's web server.  Calling
  django.setup() initialises the ORM so the task can call Message.objects.get().

Import order matters:
  django.setup() MUST be called before importing Celery or any Django model.
  If Celery were imported first, the app registry would not yet be ready when
  autodiscover_tasks later tries to import tasks.py (which imports models.py).
  The order here — os.environ → django.setup() → Celery import — is deliberate.
"""

import os
import django

# Tell Django which settings file to use.  This is set by the environment
# variable DJANGO_SETTINGS_MODULE in docker-compose.yml, but the setdefault
# call ensures the module also works if run manually outside Docker.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Initialise Django's app registry and ORM.  This is what allows worker tasks
# to call Message.objects.get() even though no web server is running.
django.setup()

# Celery import is AFTER django.setup() so the app registry is ready when
# autodiscover_tasks() scans for tasks.py files.
from celery import Celery

# 'worker01' is the application name.  It can be anything, but naming it after
# the worker service makes Celery log output and Flower display easier to read.
app = Celery('worker01')

# Read broker and result backend from celeryconfig.py (this directory).
# Using a plain Python module for config rather than Django settings keeps the
# worker independent of the Django settings namespace convention.
app.config_from_object('celeryconfig')

# Tell Celery to look for tasks.py inside the message package.
# The explicit list is required because the worker does not run Django's
# INSTALLED_APPS discovery — it only knows the packages given here.
app.autodiscover_tasks(['message'])
