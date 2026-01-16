import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
app = Celery('portal')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'to-byn-ten-minutes': {
        'task': 'newsapp.tasks.to_byn',
        'schedule': 600
    },
    'parsing-every-thirty-minutes':{
        'task': 'newsapp.tasks.news_pars',
        'schedule': 1800
    },
    'weather': {
        'task': 'newsapp.tasks.fetch_weather',
        'schedule': 1000
    }
}