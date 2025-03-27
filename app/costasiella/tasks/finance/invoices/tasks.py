from celery import shared_task

from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q
import datetime

from ....models import FinanceInvoice


@shared_task
def finance_invoices_mark_overdue():
    """
    Update the status of all sent invoices with due date < today as overdue
    :return: None
    """
    today = timezone.now().date()

    result = FinanceInvoice.objects.filter(status="SENT", date_due__lt=today).update(status="OVERDUE")

    return _("Marked %s invoices as overdue") % result


@shared_task
def finance_invoices_check_reminder_eligibility():
    """
    Check which invoices are eligible for reminders and update their status
    This task should run daily to ensure reminders can be sent for invoices
    where the last reminder was sent more than 24 hours ago
    :return: Number of invoices eligible for reminders
    """
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    
    # Find overdue invoices where:
    # 1. Either no reminder has been sent yet (date_last_reminder is None)
    # 2. OR the last reminder was sent at least 1 day ago
    query = Q(status="OVERDUE") & (
        Q(date_last_reminder__isnull=True) | 
        Q(date_last_reminder__lte=yesterday)
    )
    
    # Get the count of eligible invoices
    eligible_count = FinanceInvoice.objects.filter(query).count()
    
    return _("Found %s invoices eligible for reminders") % eligible_count
