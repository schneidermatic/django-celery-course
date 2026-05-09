import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# django.setup() MUST be called before importing Celery.
# autodiscover_tasks() imports tasks.py which imports models.py — the ORM
# must be ready before that chain runs.
django.setup()

from celery import Celery

app = Celery('worker01')
app.config_from_object('celeryconfig')
app.autodiscover_tasks(['payload'])
