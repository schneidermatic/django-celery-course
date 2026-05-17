import requests
from celery import shared_task


@shared_task
def post_to_httpbin(payload_id):
    from payload.models import Payload

    p = Payload.objects.get(id=payload_id)
    try:
        response = requests.post(
            'https://httpbin.org/post',
            json={'label': p.label, 'data': p.data},
        )
        p.status          = 'done'
        p.response_body   = response.text
        p.response_status = response.status_code
    except Exception as exc:
        p.status        = 'failed'
        p.response_body = str(exc)
    p.save()
