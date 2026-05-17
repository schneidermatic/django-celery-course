import os

broker_url     = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')
result_backend = os.environ.get('CELERY_BACKEND', 'redis://redis:6379/0')
