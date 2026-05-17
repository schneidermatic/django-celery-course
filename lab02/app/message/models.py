"""
models.py — Message domain model for the message app.

A Message represents a single item that a user submits through the web form.
It is persisted immediately by Django (status='pending') and then updated
asynchronously by the Celery worker once the simulated delivery completes
(status='sent').

This two-phase write pattern — persist first, update later — makes the task
result visible in the database regardless of whether the web process is still
running when the worker finishes.
"""

from django.db import models


class Message(models.Model):
    """
    Stores one outbound message and tracks its delivery state.

    Fields:
        recipient  — who the message is addressed to
        subject    — short summary line (like an email subject)
        body       — full message text (renamed from 'message' to avoid
                     the redundancy of Message.message)
        status     — lifecycle state; starts as 'pending', becomes 'sent'
                     after the Celery task completes
        created_at — UTC timestamp set automatically when the record is saved
    """

    recipient  = models.CharField(max_length=100)
    subject    = models.CharField(max_length=200)
    body       = models.TextField()
    # 'pending' is the default so the record is meaningful in the database
    # even before the worker has picked up the task.
    status     = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
