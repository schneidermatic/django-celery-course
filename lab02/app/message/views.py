"""
views.py — HTTP request handlers for the message app (chap02: basics).

This module demonstrates the core async dispatch pattern:
  1. Django receives a form POST.
  2. A Message record is saved to the database immediately (status='pending').
  3. The task is dispatched to Redis with .delay() — this returns instantly,
     before the worker has done any work.
  4. Django redirects the user to the results page.
  5. The Celery worker processes the task in the background and updates the
     record to status='sent'.

The user sees 'pending' briefly, then 'sent' after refreshing.  This is the
fundamental decoupling that Celery provides: the web process never blocks on
the slow work.
"""

from django.shortcuts import render, redirect
from .models import Message
from .tasks import send_message


def index(request):
    """
    GET  — render the message submission form.
    POST — create a Message, dispatch the async task, redirect to results.

    .delay(m.id) is shorthand for .apply_async(args=[m.id]).  It serialises
    the task name and arguments to JSON, writes the message to the Redis
    broker, and returns a task ID — all in a few milliseconds.  The actual
    work happens later, in the Celery worker container.
    """
    if request.method == 'POST':
        m = Message.objects.create(
            recipient=request.POST['recipient'],
            subject=request.POST['subject'],
            body=request.POST['body'],
        )
        # Dispatch: the task is queued, not executed here.
        # The worker will call send_message(m.id) asynchronously.
        send_message.delay(m.id)
        return redirect('results')

    return render(request, 'message/index.html')


def results(request):
    """Display all messages ordered by newest first."""
    message_list = Message.objects.all().order_by('-created_at')
    return render(request, 'message/result.html', {'message_list': message_list})
