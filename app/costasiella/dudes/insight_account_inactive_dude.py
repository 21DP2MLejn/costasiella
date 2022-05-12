from django.db.models import Q

from ..models import Account, \
    AccountClasspass, \
    AccountNote, \
    AccountSubscription, \
    AccountScheduleEventTicket, \
    FinanceOrder, \
    FinanceInvoice, \
    InsightAccountInactiveAccount, \
    ScheduleItemAttendance


class InsightAccountClasspassesDude:
    def get_inactive_accounts_for_insight_account_inactive_from_date(self, insight_account_inactive, date):
        # Loop over all accounts and for each account perform a number of checks.
        accounts = Account.objects.all()

        # TODO: set up debug logging for the guard clauses
        # If any check returns true, the account isn't seen as inactive
        for account in accounts:
            # Check if the account is a superuser
            if self._account_is_superuser(account):
                continue

            # Check if the account is a teacher or employee
            if self._account_is_teacher_or_employee(account):
                continue

            # Check if the account was created or updated after date
            if self._account_has_been_created_or_updated_on_or_after_date(account, date):
                continue

            # Check when the last sign in was, if any
            if self._account_has_logged_in_on_or_after_date(account, date):
                continue

            # Check if a classpass is active on or after date
            if self._account_has_active_classpass_on_or_after_date(account, date):
                continue

            # Check if a subscription is active on or after date
            if self._account_has_active_subscription_on_or_after_date(account, date):
                continue

            # Check if an event ticket exits for an event on or after date
            if self._account_has_event_ticket_on_or_after_date(account, date):
                continue

            # Check if there's at least one note created or updated on or after date
            if self._account_has_note_on_or_after_date(account, date):
                continue

            # Check if there's at least one class booking on or after date
            if self._account_has_class_booking_on_or_after_date(account, date):
                continue

            # Check if there's at least one order created or updated on or after date
            if self._account_has_order_on_or_after_date(account, date):
                continue

            # Check if there's at least one invoice created or updated on or after date
            if self._account_has_invoice_on_or_after_date(account, date):
                continue

            # When all guard clauses have been passed, we've found an inactive account.
            insight_account_inactive_account = InsightAccountInactiveAccount(
                insight_account_inactive=insight_account_inactive,
                account=account,
            )
            insight_account_inactive_account.save()

    @staticmethod
    def _account_is_superuser(account):
        return account.is_superuser

    @staticmethod
    def _account_is_teacher_or_employee(account):
        is_teacher_or_employee = False

        if account.employee or account.teacher:
            is_teacher_or_employee = True

        return is_teacher_or_employee

    @staticmethod
    def _account_has_been_created_or_updated_on_or_after_date(account, date):
        mutation_after_date = False

        if account.created_at >= date or account.updated_at >= date:
            mutation_after_date = True

        return mutation_after_date

    @staticmethod
    def _account_has_logged_in_on_or_after_date(account, date):
        last_login_after_date = False

        if account.last_login:
            if account.last_login >= date:
                last_login_after_date = True

        return last_login_after_date

    @staticmethod
    def _account_has_active_classpass_on_or_after_date(account, date):
        active_classpass_found = False

        qs = AccountClasspass.objects.filter(
            Q(account=account),
            (Q(date_end__gte=date) | Q(date_end_isnull=True))
        )
        if qs.exists():
            active_classpass_found = True

        return active_classpass_found

    @staticmethod
    def _account_has_active_subscription_on_or_after_date(account, date):
        active_subscription_found = False

        qs = AccountSubscription.objects.filter(
            Q(account=account),
            (Q(date_end__gte=date) | Q(date_end_isnull=True))
        )
        if qs.exists():
            active_subscription_found = True

        return active_subscription_found

    @staticmethod
    def _account_has_event_ticket_on_or_after_date(account, date):
        event_ticket_found = False

        qs = AccountScheduleEventTicket.objects.filter(
            Q(account=account),
            (Q(schedule_event_ticket__schedule_event_date_end__gte=date) |
             Q(schedule_event_ticket__schedule_event_date_end__isnull=True))
        )
        if qs.exists():
            event_ticket_found = True

        return event_ticket_found

    @staticmethod
    def _account_has_note_on_or_after_date(account, date):
        notes_found = False

        qs = AccountNote.objects.filter(
            Q(account=account),
            (Q(created_at__gte=date) | Q(updated_at__gte=date))
        )
        if qs.exists():
            notes_found = True

        return notes_found

    @staticmethod
    def _account_has_class_booking_on_or_after_date(account, date):
        class_booking_found = False

        qs = ScheduleItemAttendance.objects.filter(
            Q(account=account),
            Q(date__gte=date),
            ~Q(booking_status="CANCELLED")
        )
        if qs.exists():
            class_booking_found = True

        return class_booking_found

    @staticmethod
    def _account_has_order_on_or_after_date(account, date):
        order_found = False

        qs = FinanceOrder.objects.filter(
            Q(account=account),
            Q(created_at__gte=date),
        )
        if qs.exists():
            order_found = True

        return order_found

    @staticmethod
    def _account_has_invoice_on_or_after_date(account, date):
        invoice_found = False

        qs = FinanceInvoice.objects.filter(
            Q(account=account),
            Q(date_sent__gte=date),
        )
        if qs.exists():
            invoice_found = True

        return invoice_found
