"""
views.py — HTTP request handlers for the message app (chap03: standalone worker).

The dispatch logic here is identical to chap02.  The architectural difference
is invisible at this layer: the task is still dispatched with .delay(), but it
is now executed by a completely separate Docker container (worker01) instead of
a worker that shares the Django image.

The decoupling is achieved in docker-compose.yml and worker01/celerytask.py —
the view simply writes a message to Redis and trusts that some worker is
listening on the other end.
"""

from django.shortcuts import render, redirect
from .models import Message
from .tasks import send_message


def index(request):
    """
    GET  — render the message submission form.
    POST — create a Message, dispatch the async task, redirect to results.

    Dispatch pattern:
      send_message.delay(m.id)
        → serialises task name + argument to JSON
        → writes the message to the Redis default queue
        → returns immediately (does not wait for the worker)
      The standalone worker01 container receives the message, calls
      send_message(m.id), and updates the database record.
    """
    if request.method == 'POST':
        m = Message.objects.create(
            recipient=request.POST['recipient'],
            subject=request.POST['subject'],
            body=request.POST['body'],
        )
        send_message.delay(m.id)
        return redirect('results')

    return render(request, 'message/index.html')


def results(request):
    """Display all messages ordered by newest first."""
    message_list = Message.objects.all().order_by('-created_at')
    return render(request, 'message/result.html', {'message_list': message_list})
