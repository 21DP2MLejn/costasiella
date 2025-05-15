import os
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Template, Context, loader
from django.utils.translation import gettext as _
from django.utils import timezone
import datetime

from ..dudes.app_settings_dude import AppSettingsDude


class MailTemplateDude:
    def __init__(self, email_template, **kwargs):
        """
        :param email_template: field "name" in SystemMailTemplate model
        :param kwargs: one or more of
        - account
        - finance_order
        """
        self.email_template = email_template
        self.kwargs = kwargs
        self.app_settings_dude = AppSettingsDude()

    def render(self):
        """
        Switch render functions and return render function output
        :return: HTML message
        """
        from ..models import SystemMailTemplate

        functions = {
            "class_info_mail": self._render_class_info_mail,
            "event_info_mail": self._render_event_info_mail,
            "notification_order_received": self._render_template_notification_order_received,
            "order_received": self._render_template_order_received,
            "recurring_payment_failed": self._render_template_recurring_payment_failed,
            "trialpass_followup": self._render_template_triaplass_followup,
            "invoice_notification": self._render_invoice_notification,
            "invoice_initial_notification": self._render_invoice_initial_notification,
            "subscription_activated": self._render_subscription_activated,
        }

        func = functions.get(self.email_template, lambda: None)
        content = func()
        if content is None:
            return "Invalid Template"

        return content

    def _render_class_info_mail(self):
        """
        Render info mail for a class
        :return: HTML message
        """
        from ..models import SystemMailTemplate

        schedule_item = self.kwargs.get('schedule_item', None)
        if not schedule_item:
            raise Exception(_("Schedule item not found!"))

        mail_template = SystemMailTemplate.objects.get(name=self.email_template)

        content_context = Context({
            "schedule_item": schedule_item,
            "account": self.kwargs.get('account', None)
        })
        content_template = Template(mail_template.content)
        content = content_template.render(content_context)

        return dict(
            subject=mail_template.subject,
            title=mail_template.title,
            description=mail_template.description,
            content=content,
            comments=mail_template.comments
        )

    def _render_invoice_notification(self):
        """
        Render invoice notification template
        :return: HTML message
        """
        from ..models import Organization

        # Check if we have the required arguments
        invoice = self.kwargs.get('invoice', None)
        if not invoice:
            raise Exception(_("Invoice not found!"))

        # Get organization info
        organization = Organization.objects.get(pk=100)

        # Get site URL from system settings
        from ..models import SystemSetting
        try:
            hostname = SystemSetting.objects.get(setting='system_hostname').value
        except SystemSetting.DoesNotExist:
            hostname = 'http://localhost:3000'  # Default fallback

        # Get payment URL if Mollie is enabled
        payment_url = None
        from ..dudes.mollie_dude import MollieDude
        mollie_dude = MollieDude()
        if mollie_dude.is_mollie_enabled():
            try:
                payment_url = mollie_dude.create_payment_for_invoice(invoice)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating Mollie payment for invoice #{invoice.invoice_number}: {str(e)}")

        # Calculate overdue days
        from django.utils import timezone
        now = timezone.now()
        
        # Create a customer-facing payment URL for the shop interface
        from graphql_relay import to_global_id
        invoice_global_id = to_global_id('FinanceInvoiceNode', invoice.id)
        invoice_url = f"{hostname}/#/shop/account/invoice/{invoice_global_id}"
        
        # Prepare context
        context = {
            "invoice": invoice,
            "account": invoice.account,
            "organization": organization,
            "site_url": hostname,
            "payment_url": payment_url,
            "invoice_url": invoice_url,
            "now": now,
            "overdue_days": (now.date() - invoice.date_due.date()).days if invoice.date_due else 0
        }

        # Render the template using our preferred unified template
        html_message = render_to_string('email/invoice_reminder_with_payment_link.html', context)

        return dict(
            subject=f'Rēķins Nr. {invoice.finance_invoice_group.prefix}{invoice.invoice_number}',
            title='Rēķins',
            description=f'Rēķins Nr. {invoice.finance_invoice_group.prefix}{invoice.invoice_number}',
            html_message=html_message
        )

    def _render_invoice_initial_notification(self):
        """
        Render initial invoice notification template sent immediately after creation
        :return: HTML message
        """
        from ..models import Organization
        from ..dudes.mollie_dude import MollieDude

        # Check if we have the required arguments
        invoice = self.kwargs.get('invoice', None)
        if not invoice:
            raise Exception(_("Invoice not found!"))

        # Get organization info
        organization = Organization.objects.get(pk=100)

        # Get site URL from system settings
        from ..models import SystemSetting
        try:
            hostname = SystemSetting.objects.get(setting='system_hostname').value
        except SystemSetting.DoesNotExist:
            hostname = 'http://localhost:3000'  # Default fallback

        # Get payment URL if Mollie is enabled
        payment_url = None
        mollie_dude = MollieDude()
        if mollie_dude.is_mollie_enabled():
            try:
                payment_url = mollie_dude.create_payment_for_invoice(invoice)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating Mollie payment for invoice #{invoice.invoice_number}: {str(e)}")

        # Get bank transfer details from system settings
        bank_name = None
        account_holder = None
        iban = None
        bic = None
        try:
            bank_name = SystemSetting.objects.get(setting='finance_bank_name').value
            account_holder = SystemSetting.objects.get(setting='finance_bank_account_holder').value
            iban = SystemSetting.objects.get(setting='finance_bank_iban').value
            bic = SystemSetting.objects.get(setting='finance_bank_bic').value
        except SystemSetting.DoesNotExist:
            pass

        # Create a customer-facing payment URL for the shop interface
        from graphql_relay import to_global_id
        invoice_global_id = to_global_id('FinanceInvoiceNode', invoice.id)
        invoice_url = f"{hostname}/#/shop/account/invoice/{invoice_global_id}"

        # Prepare context
        context = {
            "invoice": invoice,
            "account": invoice.account,
            "organization": organization,
            "site_url": hostname,
            "invoice_url": invoice_url,
            "bank_name": bank_name,
            "account_holder": account_holder,
            "iban": iban,
            "bic": bic
        }

        # Add payment URL if available
        if payment_url:
            context["payment_url"] = payment_url

        # Render the template using the initial notification template
        html_message = render_to_string('email/invoice_initial_notification.html', context)

        return dict(
            subject=f'Rēķins Nr. {invoice.finance_invoice_group.prefix}{invoice.invoice_number}',
            title='Rēķins',
            description=f'Rēķins Nr. {invoice.finance_invoice_group.prefix}{invoice.invoice_number}',
            html_message=html_message
        )
        
    def _render_subscription_activated(self):
        """
        Render subscription activation notification template
        :return: HTML message
        """
        from ..models import Organization
        
        account_subscription = self.kwargs.get('account_subscription', None)
        if not account_subscription:
            raise Exception(_("Account subscription not found!"))
            
        # Get organization info
        organization = Organization.objects.get(pk=100)
        from ..models import SystemSetting
        try:
            hostname = SystemSetting.objects.get(setting='system_hostname').value
        except SystemSetting.DoesNotExist:
            hostname = 'http://localhost:3000'
            
        today = timezone.now().date()
        
        # Import DateToolsDude here to avoid circular imports
        from ..dudes import DateToolsDude
        date_dude = DateToolsDude()
        
        # Calculate next payment date
        current_month = today.month
        current_year = today.year
        next_month_date = date_dude.get_first_day_of_next_month_from_date(today)
        
        # Get subscription price
        subscription_price = account_subscription.organization_subscription.get_price_on_date(today, display=True)
        
        # Get related invoice if available
        from ..models import FinanceInvoice, FinanceInvoiceItem
        related_invoice = None
        invoice_items = FinanceInvoiceItem.objects.filter(
            account_subscription=account_subscription
        ).order_by('-finance_invoice__date_created')
        
        if invoice_items.exists():
            related_invoice = invoice_items.first().finance_invoice
        
        # Prepare context
        context = {
            "account_subscription": account_subscription,
            "account": account_subscription.account,
            "organization": organization,
            "site_url": hostname,
            "credits_total": account_subscription.get_credits_total(today),
            "subscription_price": subscription_price,
            "next_payment_date": next_month_date,
            "related_invoice": related_invoice
        }
        
        # Render the template
        html_message = render_to_string('email/subscription_activated.html', context)
        
        return dict(
            subject=f'Jūsu abonements ir aktivizēts: {account_subscription.organization_subscription.name}',
            title='Abonements aktivizēts',
            description=f'Abonements {account_subscription.organization_subscription.name} ir aktivizēts',
            html_message=html_message
        )
        
    def _render_event_info_mail(self):
        """
        Render info mail for an event
        :return: HTML message
        """
        from ..models import SystemMailTemplate

        schedule_item_event = self.kwargs.get('schedule_item_event', None)
        if not schedule_item_event:
            raise Exception(_("Schedule event item not found!"))

        mail_template = SystemMailTemplate.objects.get(name=self.email_template)

        content_context = Context({
            "schedule_item_event": schedule_item_event,
            "account": self.kwargs.get('account', None)
        })
        content_template = Template(mail_template.content)
        content = content_template.render(content_context)

        return dict(
            subject=mail_template.subject,
            title=mail_template.title,
            description=mail_template.description,
            content=content,
            comments=mail_template.comments
        )

    def _render_template_order_received(self):
        """
        Render order received template
        :return: HTML message
        """
        from ..models import SystemMailTemplate

        finance_order = self.kwargs.get('finance_order', None)
        if not finance_order:
            raise Exception(_("Order not found!"))

        mail_template = SystemMailTemplate.objects.get(name=self.email_template)
        content_context = Context({
            "finance_order": finance_order,
            "account": self.kwargs.get('account', None)
        })
        content_template = Template(mail_template.content)
        content = content_template.render(content_context)

        return dict(
            subject=mail_template.subject,
            title=mail_template.title,
            description=mail_template.description,
            content=content,
            comments=mail_template.comments
        )

    def _render_template_notification_order_received(self):
        """
        Render notification order received template
        :return: HTML message
        """
        from ..models import SystemMailTemplate

        finance_order = self.kwargs.get('finance_order', None)
        if not finance_order:
            raise Exception(_("Order not found!"))

        mail_template = SystemMailTemplate.objects.get(name=self.email_template)
        content_context = Context({
            "finance_order": finance_order,
            "account": self.kwargs.get('account', None)
        })
        content_template = Template(mail_template.content)
        content = content_template.render(content_context)

        return dict(
            subject=mail_template.subject,
            title=mail_template.title,
            description=mail_template.description,
            content=content,
            comments=mail_template.comments
        )

    def _render_template_recurring_payment_failed(self):
        """
        Render recurring payment failed template
        :return: HTML message
        """
        from ..models import SystemMailTemplate

        account_subscription = self.kwargs.get('account_subscription', None)
        if not account_subscription:
            raise Exception(_("Subscription not found!"))

        mail_template = SystemMailTemplate.objects.get(name=self.email_template)
        content_context = Context({
            "account_subscription": account_subscription,
            "account": self.kwargs.get('account', None)
        })
        content_template = Template(mail_template.content)
        content = content_template.render(content_context)

        return dict(
            subject=mail_template.subject,
            title=mail_template.title,
            description=mail_template.description,
            content=content,
            comments=mail_template.comments
        )

    def _render_template_triaplass_followup(self):
        """
        :return:
        """
        from ..models import SystemMailTemplate

        account_classpass = self.kwargs.get('account_classpass', None)
        if not account_classpass:
            raise Exception(_("Class pass not found!"))

        mail_template = SystemMailTemplate.objects.get(name=self.email_template)
        content_context = Context({
            "account_classpass": account_classpass,
            "account": self.kwargs.get('account', None)
        })
        content_template = Template(mail_template.content)
        content = content_template.render(content_context)

        return dict(
            subject=mail_template.subject,
            title=mail_template.title,
            description=mail_template.description,
            content=content,
            comments=mail_template.comments
        )