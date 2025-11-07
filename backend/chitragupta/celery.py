from os import environ

from celery import Celery

environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitragupta.settings')

app = Celery('chitragupta-celery')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

