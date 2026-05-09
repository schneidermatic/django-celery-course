"""
tasks.py — Celery tasks for the message app (chap02: basics).

This module defines the asynchronous work that the Celery worker executes.
The task is decorated with @shared_task instead of @app.task for two reasons:

1. Reusability across Celery app instances — @shared_task binds lazily to
   whichever Celery app is active at call time.  This matters from chap03
   onward, where the worker runs as a standalone service with its own Celery
   instance (worker01/celerytask.py) rather than sharing the Django app's one.

2. Avoids circular imports — importing the Celery app object directly from
   app/app/celery.py inside a task file would create an import cycle.

The model import is deferred inside the function body (not at module level)
because this file is imported by both Django and the standalone Celery worker.
At the time the module loads the Django ORM may not yet be fully initialised,
so deferring the import avoids 'Apps aren't loaded yet' errors.
"""

import time
from celery import shared_task


@shared_task
def send_message(message_id):
    """
    Simulate sending a message and update its status in the database.

    This task is triggered by the Django view via send_message.delay(m.id)
    immediately after the Message record is created with status='pending'.
    The worker picks it up from the Redis broker, waits 2 seconds to simulate
    an external delivery call (e.g. an SMTP or SMS API), then marks the record
    as 'sent'.

    Args:
        message_id: Primary key of the Message record to process.
                    The view passes the integer ID, not the whole object,
                    because Celery serialises task arguments to JSON —
                    a Django model instance is not JSON-serialisable.
    """
    # Deferred import: the Django ORM must be fully initialised before models
    # can be accessed, but that is guaranteed by the time the worker calls
    # this function (django.setup() runs before any task execution).
    from message.models import Message

    m = Message.objects.get(id=message_id)

    # Simulate work (e.g. calling an external delivery API).
    # In a real application, the actual delivery call would go here.
    time.sleep(2)

    m.status = 'sent'
    m.save()
