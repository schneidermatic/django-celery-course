"""
celeryconfig.py — Celery configuration for the standalone worker (chap05).

This file is loaded by celerytask.py via app.config_from_object('celeryconfig').
It extends the basic chap03/04 config with broker_transport_options, which is
the critical addition that makes priority queues work on the consumer side.

Why broker_transport_options must be here:
  When Django dispatches a task with apply_async(queue='default', priority=5),
  Celery (guided by CELERY_BROKER_TRANSPORT_OPTIONS in settings.py) writes the
  message to the Redis key 'default:5' (queue name + sep + priority number).

  If this worker config lacked broker_transport_options, the Celery worker
  would subscribe to the plain 'default' key — which stays empty because all
  messages went to 'default:5' and 'default:9'.  The result: tasks submitted
  with normal or low priority would remain 'pending' forever.

  Both the dispatcher (Django) and the consumer (this worker) must have
  matching broker_transport_options so they agree on how queue names map
  to Redis keys.
"""

import os

broker_url     = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')
result_backend = os.environ.get('CELERY_BACKEND', 'redis://redis:6379/0')

# Mirrors CELERY_BROKER_TRANSPORT_OPTIONS in app/app/settings.py exactly.
# Any mismatch between dispatcher and consumer configuration causes tasks to
# be written to sub-keys the worker never reads.
#
#   priority_steps        — 10 priority buckets (0 = highest, 9 = lowest)
#   sep                   — separator between queue name and priority number
#                           in the Redis key (e.g. 'default' + ':' + '5')
#   queue_order_strategy  — 'priority' = always serve the highest-priority
#                           bucket first rather than cycling through buckets
broker_transport_options = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}
