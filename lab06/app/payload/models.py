from django.db import models


class Payload(models.Model):
    label           = models.CharField(max_length=100)
    data            = models.TextField()
    status          = models.CharField(max_length=20, default='pending')
    response_body   = models.TextField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
