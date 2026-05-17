"""
views.py — HTTP request handlers for the message app (chap04: task routing).

This view introduces explicit task selection based on the message type chosen
in the form.  The routing itself (which queue each task goes to) is configured
centrally in settings.CELERY_TASK_ROUTES — the view only decides which of the
two task functions to call.
"""

from django.shortcuts import render, redirect
from .models import Message
from .tasks import send_transactional, send_newsletter


def index(request):
    """
    GET  — render the message form (type dropdown: transactional / newsletter).
    POST — create a Message, dispatch the correct task, redirect to results.
    """
    if request.method == 'POST':
        message_type = request.POST.get('message_type', 'transactional')
        m = Message.objects.create(
            recipient=request.POST['recipient'],
            subject=request.POST['subject'],
            body=request.POST['body'],
            message_type=message_type,
        )
        # Choose the task based on type; CELERY_TASK_ROUTES handles queue selection.
        if message_type == 'newsletter':
            send_newsletter.delay(m.id)
        else:
            send_transactional.delay(m.id)

        return redirect('results')

    return render(request, 'message/index.html')


def results(request):
    """Display all messages ordered by newest first."""
    message_list = Message.objects.all().order_by('-created_at')
    return render(request, 'message/result.html', {'message_list': message_list})
