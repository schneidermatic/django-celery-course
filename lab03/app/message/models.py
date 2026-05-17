"""
models.py — Message domain model for the message app.

A Message represents a single item that a user submits through the web form.
It is persisted immediately by Django (status='pending') and then updated
asynchronously by the Celery worker once the simulated delivery completes
(status='sent').

This two-phase write pattern — persist first, update later — works because
both the Django container and the worker01 container share the same SQLite
database file via the Docker volume mount.
"""

from django.db import models


class Message(models.Model):
    """
    Stores one outbound message and tracks its delivery state.

    Fields:
        recipient  — who the message is addressed to
        subject    — short summary line
        body       — full message text (named 'body' to avoid the redundancy
                     of Message.message)
        status     — 'pending' until the worker processes it, then 'sent'
        created_at — UTC timestamp set automatically on creation
    """

    recipient  = models.CharField(max_length=100)
    subject    = models.CharField(max_length=200)
    body       = models.TextField()
    # 'pending' is the default so the record is meaningful in the database
    # even before the worker has picked up the task.
    status     = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
