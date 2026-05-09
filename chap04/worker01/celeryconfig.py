"""
celeryconfig.py — Celery configuration for the standalone worker (chap04).

Provides broker and result backend connection strings to the worker's own
Celery instance.  This file is loaded via app.config_from_object('celeryconfig')
in celerytask.py.

In chap04, both worker_fast and worker_bulk use this same config file.  The
only difference between the two workers is the -Q flag on the celery command
in docker-compose.yml — the connection details are identical.
"""

import os

# The Redis service name ('redis') is resolved by Docker's internal DNS.
broker_url     = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')
result_backend = os.environ.get('CELERY_BACKEND', 'redis://redis:6379/0')
