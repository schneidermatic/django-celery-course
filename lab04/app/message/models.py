"""
models.py — Message domain model for the message app (chap04: task routing).

chap04 adds the message_type field so the database records the routing
decision alongside the message content.  The view reads this field to
choose which task to dispatch (send_transactional or send_newsletter), and
the result list template uses it as a label so you can see at a glance which
queue handled each message.
"""

from django.db import models


class Message(models.Model):
    """
    Stores one outbound message and tracks its delivery state.

    Fields:
        recipient    — who the message is addressed to
        subject      — short summary line
        body         — full message text (named 'body' to avoid Message.message redundancy)
        message_type — 'transactional' (fast queue) or 'newsletter' (bulk queue);
                       recorded at creation time so the result page can show which
                       worker handled the task
        status       — 'pending' until the worker processes it, then 'sent'
        created_at   — UTC timestamp set automatically on creation
    """

    recipient    = models.CharField(max_length=100)
    subject      = models.CharField(max_length=200)
    body         = models.TextField()
    # The type drives the routing decision in views.py and reflects which
    # worker queue processed (or will process) this message.
    message_type = models.CharField(max_length=20, default='transactional')
    status       = models.CharField(max_length=20, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)
