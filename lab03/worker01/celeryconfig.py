"""
celeryconfig.py — Celery configuration for the standalone worker (chap03).

This module provides the broker and result backend URLs to the worker's own
Celery instance (see celerytask.py).  It is loaded via:

    app.config_from_object('celeryconfig')

Why a separate config file instead of Django settings?
  The standalone worker reads Django settings only for the ORM (so it can
  access the database).  Using a dedicated celeryconfig.py means the worker's
  Celery configuration is self-contained and does not depend on the Django
  settings namespace pattern (CELERY_* prefixes).  Both approaches work; this
  one makes the worker easier to reason about in isolation.

Values are injected by Docker Compose environment variables so no connection
strings are hardcoded.  The fallback uses the 'redis' Docker Compose service
name, which Docker's internal DNS resolves within the Compose network.
"""

import os

# URL of the message broker.  Celery writes task messages here;
# the worker reads and removes them as it processes tasks.
broker_url = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')

# URL of the result backend.  After a task completes, Celery writes the return
# value (or exception info) here so callers can retrieve it with .get().
result_backend = os.environ.get('CELERY_BACKEND', 'redis://redis:6379/0')
