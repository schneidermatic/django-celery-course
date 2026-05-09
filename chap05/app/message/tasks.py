"""
tasks.py — Celery tasks for the message app (chap05: priority queues).

chap05 uses a single task (send_message) for all three priority levels:
urgent, normal, and low.  The routing and prioritisation are handled entirely
at dispatch time in views.py — the task itself has no knowledge of which queue
or priority level it was invoked with.

This is intentional: the task represents the work to be done (deliver a
message), while the queue and priority represent operational policy
(how urgently it should be done).  Keeping them separate means the policy
can be changed in the view or settings without touching the task code.

The task runs on whichever worker subscribed to the queue it was placed in:
  - urgent queue   → worker_urgent  (dedicated, never blocked by normal/low work)
  - default queue  → worker_default (serves normal before low due to priority ordering)
"""

import time
from celery import shared_task


@shared_task
def send_message(message_id):
    """
    Simulate sending a message and update its status in the database.

    This single task handles all three priority levels.  The caller (views.py)
    determines which queue and priority value to use via apply_async(); the task
    itself simply processes the message when the worker picks it up.

    Args:
        message_id: Primary key of the Message to process.

    Execution flow:
      1. Fetch the Message record from the database.
      2. Sleep 2 seconds (simulates an external delivery API call).
      3. Mark the record as 'sent' and persist.
    """
    from message.models import Message

    m = Message.objects.get(id=message_id)
    time.sleep(2)
    m.status = 'sent'
    m.save()
