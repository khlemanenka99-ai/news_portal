import os
from celery import Celery

# celery -A portal worker --loglevel=info команда для запуска воркера
# celery -A portal beat --loglevel=info команда для запуска расписания для воркера
# celery -A newsapp.tasks call dollar_to_byn для вызова одной задачи

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
    'weather-every-hour': {
        'task': 'weatherapp.tasks.fetch_weather',
        'schedule': 300
    }
}