from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
# from celery.signals import setup_logging  # noqa

# Set the default Django settings module for the 'celery' program.
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.development')

celery_app = Celery('app')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
#
# @setup_logging.connect
# def config_loggers(*args, **kwargs):
#     from logging.config import dictConfig  # noqa
#     from django.conf import settings  # noqa
#
#     dictConfig(settings.LOGGING)

# Load task modules from all registered Django app configs.
celery_app.autodiscover_tasks()

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Check invoice reminder eligibility every day at midnight
    'check-invoice-reminder-eligibility-daily': {
        'task': 'costasiella.tasks.finance.invoices.tasks.finance_invoices_check_reminder_eligibility',
        'schedule': crontab(minute=0, hour=0),  # Run at midnight every day
        'args': (),
    },
    # Mark invoices as overdue every day at 1 AM
    'mark-invoices-overdue-daily': {
        'task': 'costasiella.tasks.finance.invoices.tasks.finance_invoices_mark_overdue',
        'schedule': crontab(minute=0, hour=1),  # Run at 1 AM every day
        'args': (),
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

