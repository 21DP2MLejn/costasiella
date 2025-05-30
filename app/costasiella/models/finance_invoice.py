from django.utils.translation import gettext as _
from django.utils import timezone

import datetime

from django.db import models

from .account import Account
from .business import Business
from .finance_invoice_group import FinanceInvoiceGroup
from .finance_payment_method import FinancePaymentMethod

from django.db.models.signals import post_save
from django.dispatch import receiver

from .helpers import model_string

from celery import shared_task


now = timezone.now()


class FinanceInvoice(models.Model):
    STATUSES = (
        ('DRAFT', _("Draft")),
        ('SENT', _("Sent")),
        ('PAID', _("Paid")),
        ('CANCELLED', _("Cancelled")),
        ('OVERDUE', _("Overdue"))
    )

    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="invoices")
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, related_name="invoices")
    finance_invoice_group = models.ForeignKey(FinanceInvoiceGroup, on_delete=models.CASCADE)
    finance_payment_method = models.ForeignKey(FinancePaymentMethod, on_delete=models.CASCADE, null=True)
    instructor_payment = models.BooleanField(default=False)
    employee_claim = models.BooleanField(default=False)
    # custom_to is used to control whether to copy relation info from an account or business, or not.
    custom_to = models.BooleanField(default=False)
    relation_company = models.CharField(max_length=255, default="")
    relation_company_registration = models.CharField(max_length=255, default="")
    relation_company_tax_registration = models.CharField(max_length=255, default="")
    relation_contact_name = models.CharField(max_length=255, default="")
    relation_address = models.CharField(max_length=255, default="")
    relation_postcode = models.CharField(max_length=255, default="")
    relation_city = models.CharField(max_length=255, default="")
    relation_country = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=255, choices=STATUSES, default="DRAFT")
    summary = models.CharField(max_length=255, default="")
    invoice_number = models.CharField(max_length=255, default="")  # Invoice #
    date_sent = models.DateField()
    date_due = models.DateField()
    date_last_reminder = models.DateField(null=True, blank=True)
    terms = models.TextField(default="")
    footer = models.TextField(default="")
    note = models.TextField(default="")
    subtotal = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    credit_invoice_for = models.IntegerField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def send_notification_email(self):
        """
        Send invoice notification email
        """
        from ..dudes.mail_dude import MailDude
        
        # Initialize MailDude with required arguments and context
        mail_dude = MailDude(
            account=self.account,
            email_template='invoice_notification',
            invoice=self  # Pass invoice as additional context
        )
        
        # Just call send() without parameters
        return mail_dude.send()

    def send_reminder(invoice):
        subject = f'Reminder: Invoice {invoice.id} is Overdue'
        message = render_to_string('reminder_email_template.html', {
            'invoice': invoice,
            'membership_fee': invoice.finance_invoice_group.registration_fee,  # Adjust based on your model
        })
        
        recipient_list = [invoice.account.email]  # Assuming the account has an email field

        # Create PDF
        pdf_file = create_invoice_pdf(invoice)

        # Create email
        email = EmailMessage(subject, message, 'from@example.com', recipient_list)
        email.attach('invoice_{}.pdf'.format(invoice.id), pdf_file.getvalue(), 'application/pdf')
        email.send()

    def create_invoice_pdf(invoice):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, f"Invoice ID: {invoice.id}")
        p.drawString(100, 730, f"Membership Fee: {invoice.finance_invoice_group.registration_fee}")
        p.drawString(100, 710, f"Due Date: {invoice.due_date}")
        # Add more details as needed
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer

    def __str__(self):
        return model_string(self)

    def set_relation_info(self):
        """ Set relation info from linked account or business, when not custom_to """
        from ..dudes.country_dude import CountryDude
        country_dude = CountryDude()

        if not self.custom_to:
            self.relation_company = ""
            self.relation_company_registration = ""
            self.relation_company_tax_registration = ""

            if self.account:
                # Set account info by default
                self.relation_contact_name = self.account.full_name
                self.relation_address = self.account.address
                self.relation_postcode = self.account.postcode
                self.relation_city = self.account.city
                self.relation_country = country_dude.iso_country_code_to_name(self.account.country)

            # Set default business from account on creation only (not self.id), if no other business has been set
            if self.account:
                if self.account.invoice_to_business and not self.id and not self.business:
                    # Set default business for account
                    self.business = self.account.invoice_to_business

            if self.business:
                self.relation_company = self.business.name
                self.relation_company_registration = self.business.registration
                self.relation_company_tax_registration = self.business.tax_registration
                # Use business address fields
                self.relation_contact_name = ""
                self.relation_address = self.business.address
                self.relation_postcode = self.business.postcode
                self.relation_city = self.business.city
                self.relation_country = country_dude.iso_country_code_to_name(self.business.country)

    def update_amounts(self):
        """ Update total amounts fields (subtotal, tax, total, paid, balance) """
        # Get totals from invoice items
        from .finance_invoice_item import FinanceInvoiceItem
        from .finance_invoice_payment import FinanceInvoicePayment
        from django.db.models import Sum

        sums = FinanceInvoiceItem.objects.filter(finance_invoice=self).aggregate(
            Sum('subtotal'), Sum('tax'), Sum('total')
        )

        self.subtotal = sums['subtotal__sum'] or 0
        self.tax = sums['tax__sum'] or 0
        self.total = sums['total__sum'] or 0

        payment_sum = FinanceInvoicePayment.objects.filter(
            finance_invoice=self
        ).aggregate(Sum('amount'))

        self.paid = payment_sum['amount__sum'] or 0
        self.balance = self.total - self.paid

        if self.balance <= 0:
            self.status = "PAID"

        self.save(update_fields=[
            "subtotal",
            "tax",
            "total",
            "paid",
            "balance",
            "status"
        ])

    def _first_invoice_in_group_this_year(self, year): 
        """
        This invoice has to be the first in the group this year if no other 
        invoices are found in this group in this year
        """
        year_start = datetime.date(year, 1, 1)
        year_end = datetime.date(year, 12, 31)

        return not FinanceInvoice.objects.filter(
            date_sent__gte = year_start,
            date_sent__lte = year_end,
            finance_invoice_group = self.finance_invoice_group
        ).exists()

    def _increment_group_next_id(self):
        # This code is here so the id is only +=1'd when an invoice is actually created 
        self.finance_invoice_group.next_id += 1
        self.finance_invoice_group.save()

    def save(self, *args, **kwargs):
        if self.pk is None:  # We know this is object creation when there is no pk / id yet.
            # Get relation info
            self.set_relation_info()

            # set dates
            if not self.date_sent:
                # Date is now if not supplied on creation
                self.date_sent = timezone.now().date()
            self.date_due = self.date_sent + datetime.timedelta(days=self.finance_invoice_group.due_after_days)
            
            # set invoice number
            # Check if this is the first invoice in this group
            # (Needed to check if we should reset the numbering for this year)
            year = self.date_sent.year
            first_invoice_in_group_this_year = self._first_invoice_in_group_this_year(year)
            self.invoice_number = self.finance_invoice_group.next_invoice_number(
                year, 
                first_invoice_this_year = first_invoice_in_group_this_year
            )

            # Increase next_id for invoice group
            self._increment_group_next_id()

        super(FinanceInvoice, self).save(*args, **kwargs)

    def _get_item_next_line_nr(self):
        """
        Returns the next item number for an invoice
        use to set sorting when adding an item
        """
        from .finance_invoice_item import FinanceInvoiceItem

        qs = FinanceInvoiceItem.objects.filter(finance_invoice = self)

        return qs.count()

    def items_contain_subscription(self):
        """
        Check if there is a subscription item in the items for this order
        :return:
        """
        from .finance_invoice_item import FinanceInvoiceItem

        qs = FinanceInvoiceItem.objects.filter(
            finance_invoice=self,
            account_subscription__isnull=False,
        )
        return qs.exists()


    def item_add_schedule_event_ticket(self, account_schedule_event_ticket):
        """
        Add account classpass invoice item
        """
        from .finance_invoice_item import FinanceInvoiceItem
        # add item to invoice
        schedule_event_ticket = account_schedule_event_ticket.schedule_event_ticket

        finance_invoice_item = FinanceInvoiceItem(
            finance_invoice=self,
            account_schedule_event_ticket=account_schedule_event_ticket,
            line_number=self._get_item_next_line_nr(),
            product_name=_('Event ticket'),
            description='%s\n[%s]' % (schedule_event_ticket.schedule_event.name, schedule_event_ticket.name),
            quantity=1,
            price=schedule_event_ticket.price,
            finance_tax_rate=schedule_event_ticket.finance_tax_rate,
            finance_glaccount=schedule_event_ticket.finance_glaccount,
            finance_costcenter=schedule_event_ticket.finance_costcenter,
        )

        finance_invoice_item.save()

        # Check if an earlybird discount should be added
        now = timezone.now()
        date = now.date()
        schedule_event_ticket = account_schedule_event_ticket.schedule_event_ticket
        earlybird_result = schedule_event_ticket.get_earlybird_discount_on_date(date)
        if earlybird_result.get('discount', 0):
            discount_percentage = earlybird_result['earlybird'].discount_percentage
            earlybird_finance_invoice_item = FinanceInvoiceItem(
                finance_invoice=self,
                line_number=self._get_item_next_line_nr(),
                product_name=_('Event ticket earlybird discount'),
                description=str(discount_percentage) + _('% discount'),
                quantity=1,
                price=earlybird_result['discount'] * -1,
                finance_tax_rate=schedule_event_ticket.finance_tax_rate,
                finance_glaccount=schedule_event_ticket.finance_glaccount,
                finance_costcenter=schedule_event_ticket.finance_costcenter,
            )
            earlybird_finance_invoice_item.save()

        # Check if a subscription group discount should be added
        subscription_group_discount_result = \
            schedule_event_ticket.get_highest_subscription_group_discount_on_date_for_account(
                self.account, date
            )
        if subscription_group_discount_result.get('discount', 0):
            discount_percentage = subscription_group_discount_result['subscription_group_discount'].discount_percentage
            subscription_group_discount_finance_invoice_item = FinanceInvoiceItem(
                finance_invoice=self,
                line_number=self._get_item_next_line_nr(),
                product_name=_('Event ticket subscription discount'),
                description=str(discount_percentage) + _('% discount'),
                quantity=1,
                price=subscription_group_discount_result['discount'] * -1,
                finance_tax_rate=schedule_event_ticket.finance_tax_rate,
                finance_glaccount=schedule_event_ticket.finance_glaccount,
                finance_costcenter=schedule_event_ticket.finance_costcenter,
            )
            subscription_group_discount_finance_invoice_item.save()

        self.update_amounts()

        return finance_invoice_item

    def item_add_classpass(self, account_classpass):
        """
        Add account classpass invoice item
        """
        from .finance_invoice_item import FinanceInvoiceItem
        # add item to invoice
        organization_classpass = account_classpass.organization_classpass
        # finance_invoice = FinanceInvoice.objects.get(pk=self.id)

        finance_invoice_item = FinanceInvoiceItem(
            finance_invoice=self,
            account_classpass=account_classpass,
            line_number=self._get_item_next_line_nr(),
            product_name=_('Class pass'),
            description=_('Class pass %s\n%s' % (str(account_classpass.pk), organization_classpass.name)),
            quantity=1,
            price=organization_classpass.price,
            finance_tax_rate=organization_classpass.finance_tax_rate,
            finance_glaccount=organization_classpass.finance_glaccount,
            finance_costcenter=organization_classpass.finance_costcenter,
        )

        finance_invoice_item.save()

        self.update_amounts()

        return finance_invoice_item

    def item_add_product(self, account_product):
        """
        Add account product invoice item
        """
        from .finance_invoice_item import FinanceInvoiceItem
        # add item to invoice
        organization_product = account_product.organization_product

        finance_invoice_item = FinanceInvoiceItem(
            finance_invoice=self,
            account_product=account_product,
            line_number=self._get_item_next_line_nr(),
            product_name=organization_product.name,
            description=organization_product.description,
            quantity=account_product.quantity,
            price=organization_product.price,
            finance_tax_rate=organization_product.finance_tax_rate,
            finance_glaccount=organization_product.finance_glaccount,
            finance_costcenter=organization_product.finance_costcenter,
        )

        finance_invoice_item.save()

        self.update_amounts()

        return finance_invoice_item

    def item_add_membership(self, account_membership):
        """
        Add account membership invoice item
        """
        from .finance_invoice_item import FinanceInvoiceItem
        # add item to invoice
        organization_membership = account_membership.organization_membership

        finance_invoice_item = FinanceInvoiceItem(
            finance_invoice=self,
            account_membership=account_membership,
            line_number=self._get_item_next_line_nr(),
            product_name=_('Membership'),
            description=organization_membership.name,
            quantity=1,
            price=organization_membership.price,
            finance_tax_rate=organization_membership.finance_tax_rate,
            finance_glaccount=organization_membership.finance_glaccount,
            finance_costcenter=organization_membership.finance_costcenter,
        )

        finance_invoice_item.save()

        self.update_amounts()

        return finance_invoice_item

    def item_add_subscription(self, account_subscription, year, month, description=''):
        """
        Add account subscription invoice item
        :param account_subscription: models.AccountSubscription object
        :param year: int YYYY
        :param month: int M or int MM
        :param description: string
        :return: models.FinanceInvoiceItem object
        """
        from ..dudes import AppSettingsDude, DateToolsDude

        from .account_subscription_alt_price import AccountSubscriptionAltPrice
        from .finance_invoice_item import FinanceInvoiceItem

        app_settings_dude = AppSettingsDude()
        date_tools_dude = DateToolsDude()

        first_day_month = datetime.date(year, month, 1)
        last_day_month = date_tools_dude.get_last_day_month(first_day_month)

        organization_subscription = account_subscription.organization_subscription
        finance_tax_rate = organization_subscription.get_finance_tax_rate_on_date(first_day_month)

        billable_period = account_subscription.get_billable_period_in_month(year, month)
        billing_period_start = billable_period['period_start']
        billing_period_end = billable_period['period_end']
        billable_days = billable_period['billable_days']

        # Fetch alt. price for this month (if any)
        qs = AccountSubscriptionAltPrice.objects.filter(
            account_subscription=account_subscription,
            subscription_year=year,
            subscription_month=month
        )

        if qs.exists():
            # alt. price overrides broken period calculation
            alt_price = qs.first()
            price = alt_price.amount
            description = alt_price.description
        else:
            # No alt. price: Calculate amount to be billed for this month
            month_days = (last_day_month - first_day_month).days + 1
            price = organization_subscription.get_price_on_date(first_day_month, raw_price=True)
            price = round(((float(billable_days) / float(month_days)) * float(price)), 2)

        finance_tax_rate = organization_subscription.get_finance_tax_rate_on_date(first_day_month)

        # Set default description
        if not description:
            description = "{subscription_name} [{p_start} - {p_end}]".format(
                subscription_name=organization_subscription.name,
                p_start=billing_period_start.strftime(app_settings_dude.date_format),
                p_end=billing_period_end.strftime(app_settings_dude.date_format)
            )

        finance_invoice_item = FinanceInvoiceItem(
            finance_invoice=self,
            line_number=self._get_item_next_line_nr(),
            account_subscription=account_subscription,
            subscription_year=year,
            subscription_month=month,
            product_name=_("Subscription %s") % account_subscription.id,
            description=description,
            quantity=1,
            price=price,
            finance_tax_rate=finance_tax_rate,
            finance_glaccount=organization_subscription.finance_glaccount,
            finance_costcenter=organization_subscription.finance_costcenter
        )
        finance_invoice_item.save()

        # Check if a registration fee has been paid
        self._item_add_subscription_registration_fee(
            account_subscription,
            finance_tax_rate
        )

        self.update_amounts()

        return finance_invoice_item

    def item_add_empty(self):
        """
        Add an empty invoice item
        """
        from .finance_invoice_item import FinanceInvoiceItem

        finance_invoice_item = FinanceInvoiceItem(
            finance_invoice=self,
            line_number=self._get_item_next_line_nr(),
            quantity=0,
            price=0
        )
        finance_invoice_item.save()

        return finance_invoice_item


    def _item_add_subscription_registration_fee(self, account_subscription, finance_tax_rate):
        """
        Check if a registration fee should be added to the invoice and if so, add it.
        :param account_subscription: models.AccountSubscription
        :param finance_tax_rate: models.FinanceTaxRate
        :return: models.FinanceInvoiceItem
        """
        from .account_subscription import AccountSubscription
        from .finance_invoice_item import FinanceInvoiceItem

        qs = AccountSubscription.objects.filter(
            account=account_subscription.account,  # Could also be self.account... same same
            registration_fee_paid=True
        )
        if qs.exists():
            return
        else:
            fee_to_be_paid = account_subscription.organization_subscription.registration_fee
            if fee_to_be_paid:
                # Add registration fee to invoice
                finance_invoice_item = FinanceInvoiceItem(
                    finance_invoice=self,
                    line_number=self._get_item_next_line_nr(),
                    product_name=_("Registration fee"),
                    description=_("One time registration fee"),
                    quantity=1,
                    price=fee_to_be_paid,
                    finance_tax_rate=finance_tax_rate
                )
                finance_invoice_item.save()

                # Mark registration fee as paid
                account_subscription.registration_fee_paid = True
                account_subscription.save()

                return finance_invoice_item

        ################# OpenStudio code below ####################

        # from general_helpers import get_last_day_month
        #
        # from .os_customer import Customer
        # from .os_customer_subscription import CustomerSubscription
        # from .os_school_subscription import SchoolSubscription
        # from .tools import OsTools
        #
        # db = current.db
        # os_tools = OsTools()
        # DATE_FORMAT = current.DATE_FORMAT
        #
        # next_sort_nr = self.get_item_next_sort_nr()
        #
        # date = datetime.date(int(SubscriptionYear),
        #                      int(SubscriptionMonth),
        #                      1)
        #
        #
        # cs = CustomerSubscription(csID)
        # ssuID = cs.ssuID
        # ssu = SchoolSubscription(ssuID)
        # row = ssu.get_tax_rates_on_date(date)
        # if row:
        #     tax_rates_id = row.school_subscriptions_price.tax_rates_id
        # else:
        #     tax_rates_id = None
        #
        # period_start = date
        # first_day_month = date
        # last_day_month = get_last_day_month(date)
        # period_end = last_day_month
        # glaccount = ssu.get_glaccount_on_date(date)
        # costcenter = ssu.get_costcenter_on_date(date)
        # price = 0
        #
        # # check for alt price
        # csap = db.customers_subscriptions_alt_prices
        # query = (csap.customers_subscriptions_id == csID) & \
        #         (csap.SubscriptionYear == SubscriptionYear) & \
        #         (csap.SubscriptionMonth == SubscriptionMonth)
        # csap_rows = db(query).select(csap.ALL)
        # if csap_rows:
        #     # alt. price overrides broken period
        #     csap_row = csap_rows.first()
        #     price    = csap_row.Amount
        #     description = csap_row.Description
        # else:
        #     price = ssu.get_price_on_date(date, False)
        #
        #     broken_period = False
        #     pause = False
        #
        #     # Check pause
        #     query = (db.customers_subscriptions_paused.customers_subscriptions_id == csID) & \
        #             (db.customers_subscriptions_paused.Startdate <= last_day_month) & \
        #             ((db.customers_subscriptions_paused.Enddate >= first_day_month) |
        #              (db.customers_subscriptions_paused.Enddate == None))
        #     rows = db(query).select(db.customers_subscriptions_paused.ALL)
        #     if rows:
        #         pause = rows.first()
        #
        #     # Calculate days to be paid
        #     if cs.startdate > first_day_month and cs.startdate <= last_day_month:
        #         # Start later in month
        #         broken_period = True
        #         period_start = cs.startdate
        #
        #
        #     if cs.enddate:
        #         if cs.enddate >= first_day_month and cs.enddate < last_day_month:
        #             # End somewhere in month
        #             broken_period = True
        #             period_end = cs.enddate
        #
        #
        #     Range = namedtuple('Range', ['start', 'end'])
        #     period_range = Range(start=period_start, end=period_end)
        #     period_days = (period_range.end - period_range.start).days + 1
        #
        #     if pause:
        #         # Set pause end date to period end if > period end
        #         pause_end = pause.Enddate
        #         if pause_end >= period_range.end:
        #             pause_end = period_range.end
        #
        #         pause_range = Range(start=pause.Startdate, end=pause_end)
        #         latest_start = max(period_range.start, pause_range.start)
        #         earliest_end = min(pause_range.end, pause_range.end)
        #         delta = (earliest_end - latest_start).days + 1
        #         overlap = max(0, delta)
        #
        #         # Subtract pause overlap from period to be paid
        #         period_days = period_days - overlap
        #
        #     month_days = (last_day_month - first_day_month).days + 1
        #
        #     price = round(((float(period_days) / float(month_days)) * float(price)), 2)
        #
        #     if not description:
        #         description = cs.name + ' ' + period_start.strftime(DATE_FORMAT) + ' - ' + period_end.strftime(DATE_FORMAT)
        #         if pause:
        #             description += '\n'
        #             description += "(" + T("Pause") + ": "
        #             description += pause.Startdate.strftime(DATE_FORMAT) + " - "
        #             description += pause.Enddate.strftime(DATE_FORMAT) + " | "
        #             description += T("Days paid this period: ")
        #             description += str(period_days)
        #             description += ")"
        #
        # iiID = db.invoices_items.insert(
        #     invoices_id = self.invoices_id,
        #     ProductName = current.T("Subscription") + ' ' + str(csID),
        #     Description = description,
        #     Quantity = 1,
        #     Price = price,
        #     Sorting = next_sort_nr,
        #     tax_rates_id = tax_rates_id,
        #     accounting_glaccounts_id = glaccount,
        #     accounting_costcenters_id = costcenter
        # )
        #
        # ## Check if we should bill the first 2 months
        # subscription_first_invoice_two_terms = os_tools.get_sys_property('subscription_first_invoice_two_terms')
        # subscription_first_invoice_two_terms_from_day = \
        #     int(os_tools.get_sys_property('subscription_first_invoice_two_terms_from_day') or 1)
        # if subscription_first_invoice_two_terms == "on":
        #     # Check if this is the first invoice for this subscription
        #     # AND we're on or past the 15th of the month
        #     query = (db.invoices_items_customers_subscriptions.customers_subscriptions_id == csID) & \
        #             (db.invoices_items.invoices_id != self.invoices_id)
        #     count = db(query).count()
        #
        #     start_day = cs.startdate.day
        #     if not count and start_day >= subscription_first_invoice_two_terms_from_day:
        #         # first invoice for this subscription... let's add the 2nd month as well.
        #         period_start = get_last_day_month(date) + datetime.timedelta(days=1)
        #         second_month_price = ssu.get_price_on_date(period_start, False)
        #         period_end = get_last_day_month(period_start)
        #         description = cs.name + ' ' + period_start.strftime(DATE_FORMAT) + ' - ' + period_end.strftime(DATE_FORMAT)
        #         next_sort_nr = self.get_item_next_sort_nr()
        #
        #         iiID2 = db.invoices_items.insert(
        #             invoices_id=self.invoices_id,
        #             ProductName=current.T("Subscription") + ' ' + str(csID),
        #             Description=description,
        #             Quantity=1,
        #             Price=second_month_price,
        #             Sorting=next_sort_nr,
        #             tax_rates_id=tax_rates_id,
        #             accounting_glaccounts_id=glaccount,
        #             accounting_costcenters_id=costcenter
        #         )
        #
        #         # Add 0 payment for 2nd month in alt. prices, to prevent duplicate payments
        #         db.customers_subscriptions_alt_prices.insert(
        #             customers_subscriptions_id = csID,
        #             SubscriptionYear=period_start.year,
        #             SubscriptionMonth = period_start.month,
        #             Amount = 0,
        #             Description = T("Paid in invoice ") + self.invoice.InvoiceID
        #         )
        #
        #         self.link_item_to_customer_subscription(csID, iiID2)
        # ##
        # # Check if a registration fee should be added
        # # ; Add fee if a registration fee has ever been paid
        # ##
        # customer = Customer(cs.auth_customer_id)
        # # query = ((db.customers_subscriptions.auth_customer_id == cs.auth_customer_id) &
        # #          (db.customers_subscriptions.RegistrationFeePaid == True))
        #
        # fee_paid_in_past = customer.has_paid_a_subscription_registration_fee()
        # ssu = db.school_subscriptions(ssuID)
        # if not fee_paid_in_past and ssu.RegistrationFee: # Registration fee not already paid and RegistrationFee defined?
        #     regfee_to_be_paid = ssu.RegistrationFee or 0
        #     if regfee_to_be_paid:
        #         db.invoices_items.insert(
        #             invoices_id = self.invoices_id,
        #             ProductName = current.T("Registration fee"),
        #             Description = current.T('One time registration fee'),
        #             Quantity = 1,
        #             Price = regfee_to_be_paid,
        #             Sorting = next_sort_nr,
        #             tax_rates_id = tax_rates_id,
        #         )
        #
        #         # Mark registration fee as paid for subscription
        #         db.customers_subscriptions[cs.csID] = dict(RegistrationFeePaid=True)
        #
        # ##
        # # Always call these
        # ##
        # # Link invoice item to subscription
        # self.link_item_to_customer_subscription(csID, iiID)
        # # This calls self.on_update()
        # self.set_amounts()
        #
        # return iiID

    def tax_rates_amounts(self, formatted=False):
        """
        Returns tax for each tax rate as list sorted by tax rate percentage
        format: [ [ tax_rate_obj, sum ] ]
        """
        from django.db.models import Sum
        from .finance_tax_rate import FinanceTaxRate

        amounts_tax = []

        tax_rates = FinanceTaxRate.objects.filter(
            invoice_items__finance_invoice=self,
        ).annotate(invoice_amount=Sum("invoice_items__tax"))

        return tax_rates

    def is_paid(self):
        """
        Check if the status should be changed to 'paid'
        """
        self.update_amounts()

        if self.paid >= self.total:
            self.status = "PAID"
            self.save()
            return True
        else:
            self.status = "SENT"
            self.save()
            return False

    def cancel(self):
        """
        Set status to cancelled
        :return:
        """
        self.status = "CANCELLED"
        self.save()

    def cancel_and_create_credit_invoice(self):
        """
        Cancel invoice and create a credit invoice, linked to this one
        :return: credit invoice object
        """
        from .finance_invoice_item import FinanceInvoiceItem

        self.cancel()

        credit_invoice = FinanceInvoice(
            account=self.account,
            business=self.business,
            finance_invoice_group=self.finance_invoice_group,
            finance_payment_method=self.finance_payment_method,
            instructor_payment=self.instructor_payment,
            employee_claim=self.employee_claim,
            status="SENT",
            summary=self.summary,
            note=self.note,
            credit_invoice_for=self.id,
        )
        credit_invoice.save()

        # Duplicate items with negative amount
        qs = FinanceInvoiceItem.objects.filter(finance_invoice=self)
        for finance_invoice_item in qs:
            credit_finance_invoice_item = FinanceInvoiceItem(
                finance_invoice=credit_invoice,
                account_schedule_event_ticket=finance_invoice_item.account_schedule_event_ticket,
                account_classpass=finance_invoice_item.account_classpass,
                account_subscription=finance_invoice_item.account_subscription,
                subscription_year=finance_invoice_item.subscription_year,
                subscription_month=finance_invoice_item.subscription_month,
                line_number=finance_invoice_item.line_number,
                product_name=finance_invoice_item.product_name,
                description=finance_invoice_item.description,
                quantity=finance_invoice_item.quantity,
                price=finance_invoice_item.price * -1,
                finance_tax_rate=finance_invoice_item.finance_tax_rate,
                finance_glaccount=finance_invoice_item.finance_glaccount,
                finance_costcenter=finance_invoice_item.finance_costcenter
            )
            credit_finance_invoice_item.save()
        # Set amounts on credit invoice
        credit_invoice = instance.cancel_and_create_credit_invoice()
        return credit_invoice

@receiver(post_save, sender='costasiella.FinanceInvoice')
def handle_invoice_notification(sender, instance, created, **kwargs):
    if created and instance.status == 'SENT':
        instance.send_notification_email()

