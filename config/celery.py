from celery import Celery
from celery.signals import setup_logging
from logging.config import dictConfig
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('Kyrt')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):
    # source: https://siddharth-pant.medium.com/the-missing-how-to-for-celery-logging-85e21f0231de
    from django.conf import settings
    dictConfig(settings.LOGGING)
