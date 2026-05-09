"""
tasks.py — Celery tasks for the message app (chap04: task routing).

chap04 uses two specialised tasks:

  send_transactional — fast, time-sensitive messages (e.g. password resets).
                       Simulated with a 1-second sleep.
                       Routed to the 'fast' queue via CELERY_TASK_ROUTES.

  send_newsletter    — bulk, non-urgent messages (e.g. weekly digests).
                       Simulated with a 5-second sleep.
                       Routed to the 'bulk' queue via CELERY_TASK_ROUTES.

Having separate tasks enables the routing table in settings.py to map each
task to its own queue without any logic in the view — the view just calls
.delay() and Celery applies the route automatically based on the task name.
"""

import time
from celery import shared_task


@shared_task
def send_transactional(message_id):
    """
    Process a time-sensitive transactional message.

    This task runs on worker_fast (the 'fast' queue).  The 1-second sleep
    simulates a fast external delivery call.

    Args:
        message_id: Primary key of the Message to process.
    """
    from message.models import Message

    m = Message.objects.get(id=message_id)
    time.sleep(1)
    m.status = 'sent'
    m.save()


@shared_task
def send_newsletter(message_id):
    """
    Process a bulk newsletter message.

    This task runs on worker_bulk (the 'bulk' queue).  The 5-second sleep
    simulates a slow batch delivery process.

    Args:
        message_id: Primary key of the Message to process.
    """
    from message.models import Message

    m = Message.objects.get(id=message_id)
    time.sleep(5)
    m.status = 'sent'
    m.save()
