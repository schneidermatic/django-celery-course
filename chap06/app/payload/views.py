import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import Payload
from .tasks import post_to_httpbin


def index(request):
    if request.method == 'POST':
        p = Payload.objects.create(
            label=request.POST['label'],
            data=request.POST['data'],
        )
        post_to_httpbin.delay(p.id)
        return redirect('list')
    return render(request, 'payload/index.html')


def payload_list(request):
    payloads = Payload.objects.all().order_by('-created_at')
    has_pending = payloads.filter(status='pending').exists()
    return render(request, 'payload/list.html', {
        'payloads': payloads,
        'auto_refresh': has_pending,
    })


def payload_detail(request, pk):
    p = get_object_or_404(Payload, pk=pk)
    pretty_body = None
    if p.response_body:
        try:
            pretty_body = json.dumps(json.loads(p.response_body), indent=2)
        except (json.JSONDecodeError, ValueError):
            pretty_body = p.response_body
    return render(request, 'payload/detail.html', {
        'payload': p,
        'pretty_body': pretty_body,
    })
