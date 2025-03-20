import os
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Template, Context, loader
from django.utils.translation import gettext as _

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

        # Prepare context
        context = {
            "invoice": invoice,
            "account": invoice.account,
            "organization": organization,
            "site_url": hostname
        }

        # Render the template using our preferred unified template
        html_message = render_to_string('email/invoice_reminder_with_payment_link.html', context)

        return dict(
            subject=f'Rēķins Nr. {invoice.finance_invoice_group.prefix}{invoice.invoice_number}',
            title='Rēķins',
            description=f'Rēķins Nr. {invoice.finance_invoice_group.prefix}{invoice.invoice_number}',
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