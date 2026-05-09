"""
models.py — Message domain model for the message app (chap05: priority queues).

chap05 adds the priority field to record the urgency level at which each
message was submitted.  The result list template uses this field to show
a [urgent] / [normal] / [low] label next to each entry, making it easy to
observe which queue handled the task.
"""

from django.db import models


class Message(models.Model):
    """
    Stores one outbound message and tracks its delivery state.

    Fields:
        recipient  — who the message is addressed to
        subject    — short summary line
        body       — full message text (named 'body' to avoid Message.message redundancy)
        priority   — urgency level chosen in the form:
                       'urgent' → dedicated 'urgent' queue (worker_urgent)
                       'normal' → 'default' queue with priority 5
                       'low'    → 'default' queue with priority 9
                     Stored here so the result list can label each entry.
        status     — 'pending' until the worker processes it, then 'sent'
        created_at — UTC timestamp set automatically on creation
    """

    recipient  = models.CharField(max_length=100)
    subject    = models.CharField(max_length=200)
    body       = models.TextField()
    # Stored at creation time so the result page can show the priority label
    # even before the worker has finished processing the task.
    priority   = models.CharField(max_length=10, default='normal')
    status     = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
