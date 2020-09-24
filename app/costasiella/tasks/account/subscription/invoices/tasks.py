import datetime

from celery import shared_task
from django.utils.translation import gettext as _
from django.db.models import Q

from .....models import AccountSubscription, AccountSubscriptionCredit
from .....dudes import DateToolsDude

@shared_task
def account_subscription_invoices_add_for_month(year, month, description='', invoice_date="today"):
    """
    Add subscription credits for a given month
    :param year: YYYY
    :param month: 1 ... 2
    :return:
    """
    date_dude = DateToolsDude()

    # print("###############")
    # print("Start adding credits")

    first_day_month = datetime.date(year, month, 1)
    last_day_month = date_dude.get_last_day_month(first_day_month)

    invoices_found = 0

    qs = AccountSubscription.objects.filter(
        Q(date_start__lte=last_day_month) &
        (Q(date_end__gte=first_day_month) |
         Q(date_end__isnull=True))
    )

    for account_subscription in qs:
        result = account_subscription.create_invoice_for_month(
            year, month, description=description, invoice_date=invoice_date
        )

        if result:
            invoices_found += 1

    return _("There are %s subscription invoices in %s-%s") % (invoices_found, year, month)



    ########### OpenStudio reference code below ###########

    from .os_customer_subscription import CustomerSubscription
    from general_helpers import get_last_day_month
    from .os_invoice import Invoice

    T = current.T
    db = current.db
    DATE_FORMAT = current.DATE_FORMAT

    year = int(year)
    month = int(month)

    firstdaythismonth = datetime.date(year, month, 1)
    lastdaythismonth = get_last_day_month(firstdaythismonth)

    invoices_count = 0

    # get all active subscriptions in month
    query = (db.customers_subscriptions.Startdate <= lastdaythismonth) & \
            ((db.customers_subscriptions.Enddate >= firstdaythismonth) |
             (db.customers_subscriptions.Enddate == None))

    rows = db(query).select(db.customers_subscriptions.ALL)
    for row in rows:
        cs = CustomerSubscription(row.id)
        cs.create_invoice_for_month(year, month, description, invoice_date)

        invoices_count += 1

    ##
    # For scheduled tasks db connection has to be committed manually
    ##
    db.commit()

    return T("Invoices in month") + ': ' + str(invoices_count)


@shared_task
def account_subscription_invoices_add_for_month_mollie_collection(year, month):
    """

    :param year:
    :param month:
    :return:
    """
    #TODO: Add function to send mail for failed payment collection
    from mollie.api.client import Client
    from mollie.api.error import Error as MollieError

    from .....models import AccountSubscription, IntegrationLogMollie
    from .....modules.finance_tools import get_currency
    from .....dudes import MollieDude, date_tools_dude


    date_tools_dude = DateToolsDude()
    mollie_dude = MollieDude()

    # Create mollie instance
    mollie = Client()
    mollie_api_key = mollie_dude.get_api_key()
    mollie.set_api_key(mollie_api_key)

    first_day_month = datetime.date(year, month, 1)
    last_day_month = date_tools_dude.get_last_day_month(first_day_month)

    # find active subscriptions with payment method mollie (100)
    qs = AccountSubscription.objects.filter(
        Q(finance_payment_method=100) &
        Q(date_start__lte=last_day_month) &
        (
            Q(date_end__gte=first_day_month) |
            Q(date_end__isnull=True)
        )
    )

    success = 0
    failed = 0

    for i, account_subscription in qs:
        finance_invoice_item = account_subscription.create_invoice_for_month(year, month)
        # Check if an invoice (item) was created
        if not finance_invoice_item:
            continue

        finance_invoice = finance_invoice_item.finance_invoice
        # Only continue when the invoice status == SENT
        if not finance_invoice.status == 'SENT':
            continue

        # Check if the amount of the invoice > 0:
        if not finance_invoice.total:
            continue

        # Create mollie recurring payment
        account = finance_invoice.account
        mollie_customer_id = account.mollie_customer_id
        mandates = mollie_dude.get_account_mollie_mandates(account, mollie)

        valid_mandate = False
        # set default recurring type, change to recurring if a valid mandate is found.
        if mandates['count'] > 0:
            # background payment
            for mandate in mandates['_embedded']['mandates']:
                if mandate['status'] == 'valid':
                    valid_mandate = True
                    break

            if valid_mandate:
                # Create recurring payment
                try:
                    webhook_url = mollie_dude.get_webhook_url_from_db()
                    description = finance_invoice.summary + ' - ' + finance_invoice.invoice_number
                    payment = mollie.payments.create({
                        'amount': {
                            'currency': get_currency(),
                            'value': str(finance_invoice.total)
                        },
                        'customerId': mollie_customer_id,
                        'sequenceType': 'recurring',  # important
                        'description': description,
                        'webhookUrl': webhook_url,
                        'metadata': {
                            'invoice_id': finance_invoice.pk,
                        }
                    })

                    #  Log payment info
                    log = IntegrationLogMollie(
                        log_source="TASK_ACCOUNT_SUBSCRIPTION_MOLLIE_COLLECT",
                        mollie_payment_id=payment['id'],
                        recurring_type='recurring',
                        webhook_url=webhook_url,
                        finance_invoice=finance_invoice
                    )
                    log.save()

                    success += 1

                except MollieError as e:
                    print(e)
                    # send mail to ask customer to pay manually
                    send_mail_failed(cs.auth_customer_id)

                    failed += 1
                    # return error
                    # return 'API call failed: ' + e.message
        else:
            # send mail to ask customer to pay manually
            send_mail_failed(cs.auth_customer_id)

            failed +=1


    ########## OpenStudio example code begin ###############
    #
    # def send_mail_failed(cuID):
    #     """
    #         When a recurring payment fails, mail customer with request to pay manually
    #     """
    #     os_mail = OsMail()
    #     msgID = os_mail.render_email_template('payment_recurring_failed')
    #     os_mail.send_and_archive(msgID, cuID)
    #
    # from openstudio.os_customer import Customer
    #
    # # hostname
    # sys_hostname = get_sys_property('sys_hostname')
    # # set up Mollie
    # mollie = Client()
    # mollie_api_key = get_sys_property('mollie_website_profile')
    # mollie.set_api_key(mollie_api_key)
    # # set dates
    # today = datetime.date.today()
    # firstdaythismonth = datetime.date(today.year, today.month, 1)
    # lastdaythismonth = get_last_day_month(firstdaythismonth)
    #
    # # call some function to do stuff
    #
    # # find all active subscriptions with payment method 100 (Mollie)
    # query = (db.customers_subscriptions.payment_methods_id == 100) & \
    #         (db.customers_subscriptions.Startdate <= lastdaythismonth) & \
    #         ((db.customers_subscriptions.Enddate >= firstdaythismonth) |
    #          (db.customers_subscriptions.Enddate == None))
    # rows = db(query).select(db.customers_subscriptions.ALL)
    #
    # success = 0
    # failed = 0
    #
    # # create invoices
    # for i, row in enumerate(rows):
    #     cs = CustomerSubscription(row.id)
    #     # This function returns the invoice id if it already exists
    #     iID = cs.create_invoice_for_month(TODAY_LOCAL.year, TODAY_LOCAL.month)
    #
    #     #print 'invoice created'
    #     #print iID
    #
    #     # Do we have an invoice?
    #     if not iID:
    #         continue
    #
    #     invoice = Invoice(iID)
    #     # Only do something if the invoice status is sent
    #     if not invoice.invoice.Status == 'sent':
    #         continue
    #
    #     # We're good, continue processing
    #     invoice_amounts = invoice.get_amounts()
    #     #print invoice.invoice.InvoiceID
    #     description = invoice.invoice.Description + ' - ' + invoice.invoice.InvoiceID
    #     db.commit()
    #
    #     #create recurring payments using mandates
    #     #subscription invoice
    #     customer = Customer(row.auth_customer_id)
    #     mollie_customer_id = customer.row.mollie_customer_id
    #     mandates = customer.get_mollie_mandates()
    #     valid_mandate = False
    #     # set default recurring type, change to recurring if a valid mandate is found.
    #     if mandates['count'] > 0:
    #         # background payment
    #         for mandate in mandates['_embedded']['mandates']:
    #             if mandate['status'] == 'valid':
    #                 valid_mandate = True
    #                 break
    #
    #         if valid_mandate:
    #             # Create recurring payment
    #             try:
    #                 webhook_url = URL('mollie', 'webhook', scheme='https', host=sys_hostname)
    #                 payment = mollie.payments.create({
    #                     'amount': {
    #                         'currency': CURRENCY,
    #                         'value': str(invoice_amounts.TotalPriceVAT)
    #                     },
    #                     'customerId': mollie_customer_id,
    #                     'sequenceType': 'recurring',  # important
    #                     'description': description,
    #                     'webhookUrl': webhook_url,
    #                     'metadata': {
    #                         'invoice_id': invoice.invoice.id,
    #                         'customers_orders_id': 'invoice' # This lets the webhook function know it's dealing with an invoice
    #                     }
    #                 })
    #
    #                 # link invoice to mollie_payment_id
    #                 db.invoices_mollie_payment_ids.insert(
    #                     invoices_id=invoice.invoice.id,
    #                     mollie_payment_id=payment['id'],
    #                     RecurringType='recurring',
    #                     WebhookURL=webhook_url
    #                 )
    #
    #                 success += 1
    #
    #             except MollieError as e:
    #                 print(e)
    #                 # send mail to ask customer to pay manually
    #                 send_mail_failed(cs.auth_customer_id)
    #
    #                 failed += 1
    #                 # return error
    #                 # return 'API call failed: ' + e.message
    #     else:
    #         # send mail to ask customer to pay manually
    #         send_mail_failed(cs.auth_customer_id)
    #
    #         failed +=1
    #
    # # For scheduled tasks, db has to be committed manually
    # db.commit()
    #
    # return T("Payments collected") + ': ' + str(success) + '<br>' + \
    #     T("Payments failed to collect") + ': ' + str(failed)

    ############ OpenStudio example code end #######################