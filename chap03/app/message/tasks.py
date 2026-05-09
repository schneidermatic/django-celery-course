"""
tasks.py — Celery tasks for the message app (chap03: standalone worker).

Chapter context:
  In chap03 this task is executed by the standalone worker01 service, not by
  a worker that shares the Django image.  The @shared_task decorator is what
  makes this possible: the task binds lazily to whichever Celery app instance
  is active at call time.  The standalone worker creates its own Celery
  instance (worker01/celerytask.py), discovers this task via autodiscover_tasks,
  and executes it using the worker's own instance — without any coupling to
  the Django-side Celery app.

Why @shared_task and not @app.task:
  @app.task requires a direct reference to the Celery app object, which would
  force an import from app/app/celery.py.  In a standalone worker that
  reference would be wrong (the worker has its own app).  @shared_task avoids
  this by using the current_app proxy, which resolves at call time.

Why the model import is inside the function:
  This file is loaded by both the Django process and the standalone worker.
  At module-load time the Django ORM may not yet be fully initialised (the
  worker calls django.setup() before executing tasks, not before loading the
  module).  Deferring the import until the function body ensures the ORM is
  ready when it is actually needed.
"""

import time
from celery import shared_task


@shared_task
def send_message(message_id):
    """
    Simulate sending a message and persist the updated status.

    Args:
        message_id: Primary key of the Message to process.  The view passes
                    an integer ID (not a model instance) because Celery
                    serialises arguments to JSON.

    Execution flow:
      1. Fetch the Message from the database.
      2. Sleep 2 seconds (simulates an external API call).
      3. Mark the record as 'sent' and save.
    """
    from message.models import Message

    m = Message.objects.get(id=message_id)
    time.sleep(2)
    m.status = 'sent'
    m.save()
