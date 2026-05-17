"""
views.py — HTTP request handlers for the message app (chap05: priority queues).

This view implements the combined routing + prioritisation strategy of chap05:

  URGENT messages → 'urgent' queue → worker_urgent
    Dispatched with apply_async(queue='urgent').
    The urgent queue is a plain FIFO queue with a dedicated worker.  Because
    worker_urgent never reads from 'default', it is never blocked by a backlog
    of lower-priority work.  No priority number is needed.

  NORMAL messages → 'default' queue → worker_default, priority 5
    Dispatched with apply_async(queue='default', priority=5).
    Redis stores this message under the key 'default:5'.

  LOW messages → 'default' queue → worker_default, priority 9
    Dispatched with apply_async(queue='default', priority=9).
    Redis stores this message under the key 'default:9'.

PRIORITY_MAP translates human-readable labels to integers.
Lower number = higher priority (processed sooner).
"""

from django.shortcuts import render, redirect
from .models import Message
from .tasks import send_message

# Maps the form's priority string to the integer Celery passes to Redis.
# Scale: 0 (highest urgency) to 9 (lowest urgency).
PRIORITY_MAP = {'normal': 5, 'low': 9}


def index(request):
    """
    GET  — render the message form with a priority dropdown (Urgent / Normal / Low).
    POST — create a Message, route to the correct queue, redirect.
    """
    if request.method == 'POST':
        priority = request.POST.get('priority', 'normal')
        m = Message.objects.create(
            recipient=request.POST['recipient'],
            subject=request.POST['subject'],
            body=request.POST['body'],
            priority=priority,
        )

        if priority == 'urgent':
            # Fast lane: dedicated queue + dedicated worker.
            send_message.apply_async(args=[m.id], queue='urgent')
        else:
            # Shared queue: numeric priority controls execution order.
            send_message.apply_async(
                args=[m.id],
                queue='default',
                priority=PRIORITY_MAP[priority],
            )

        return redirect('results')

    return render(request, 'message/index.html')


def results(request):
    """Display all messages ordered by newest first."""
    message_list = Message.objects.all().order_by('-created_at')
    return render(request, 'message/result.html', {'message_list': message_list})
