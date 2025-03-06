from django.utils.translation import gettext as _
from django.db.models import Q
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from graphql_relay import to_global_id

import graphene
import logging
import traceback
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from mollie.api.client import Client
from mollie.api.error import Error as MollieError

from ..models import FinanceInvoice, SystemSetting
from ..modules.gql_tools import require_login_and_permission, get_rid
from ..modules.messages import Messages
from ..dudes.system_setting_dude import SystemSettingDude
from ..dudes.mollie_dude import MollieDude

m = Messages()


class SendInvoiceReminderResultType(graphene.ObjectType):
    """
    Result type for sending invoice reminders
    """
    count = graphene.Int()
    success = graphene.Boolean()
    message = graphene.String()


class SendInvoiceReminders(graphene.Mutation):
    """
    Mutation to send reminders for overdue invoices
    """
    class Arguments:
        pass  

    result = graphene.Field(SendInvoiceReminderResultType)

    @classmethod
    def mutate(self, root, info):
        # Initialize logging
        logger = logging.getLogger(__name__)
        
        # Check user authentication and permissions
        user = info.context.user
        if not user.is_authenticated:
            logger.error("User not authenticated when attempting to send invoice reminders")
            return SendInvoiceReminders(
                result=SendInvoiceReminderResultType(
                    count=0,
                    success=False,
                    message="Authentication required"
                )
            )
            
        try:
            require_login_and_permission(user, 'costasiella.view_financeinvoice')
            require_login_and_permission(user, 'costasiella.change_financeinvoice')
            logger.info(f"User {user.username} authorized to send invoice reminders")
        except GraphQLError as e:
            logger.error(f"Permission error: {str(e)}")
            return SendInvoiceReminders(
                result=SendInvoiceReminderResultType(
                    count=0,
                    success=False,
                    message=f"Permission error: {str(e)}"
                )
            )

        host = info.context.get_host()
        
        # Get all overdue invoices
        overdue_invoices = FinanceInvoice.objects.filter(status='OVERDUE')
        
        # Initialize counter for successful reminders
        successful_reminders = 0
        
        # Get organization name from system settings
        system_setting_dude = SystemSettingDude()
        organization_name = system_setting_dude.get('system_organization_name') or 'Costasiella'
        
        # Initialize Mollie client
        
        mollie_dude = MollieDude()
        mollie = Client()
        mollie_api_key = mollie_dude.get_api_key()
        payment_links_enabled = True
        
        if not mollie_api_key:
            payment_links_enabled = False
            logger.warning("Mollie API key not configured or invalid. Continuing without payment links.")
            
        # Log the API key format (masked for security)
        if mollie_api_key:
            masked_key = "*" * (len(mollie_api_key) - 4) + mollie_api_key[-4:]
            logger.info(f"Using Mollie API key format: {masked_key}")
            
        # Try to set the API key in the Mollie client if payment links are enabled
        if payment_links_enabled and mollie_api_key:
            try:
                mollie.set_api_key(mollie_api_key)
                # Test API key validity with a simple API call
                mollie.methods.list()
                logger.info("Mollie API key validated successfully")
            except MollieError as e:
                # Handle Mollie API errors but continue without payment links
                error_message = f"Mollie API authentication error: {str(e)}"
                logger.warning(f"{error_message} - Continuing without payment links.")
                payment_links_enabled = False
        
        # Process each overdue invoice
        for invoice in overdue_invoices:
            try:
                # Initialize payment_link variable
                payment_link = None
                
                # Only generate payment link if payment links are enabled
                if payment_links_enabled:
                    try:
                        # Generate payment link
                        amount = invoice.balance
                        description = _("Invoice #") + str(invoice.invoice_number)
                        
                        # Prepare redirect URL
                        redirect_url = 'https://' + host + '/#/shop/account/invoice_payment_status/' + to_global_id("FinanceInvoiceNode", invoice.id)
                        # For development
                        if "localhost" in redirect_url:
                            redirect_url = redirect_url.replace("localhost:8000", "dev.costasiella.com:8000")
                        
                        # Get customer ID
                        mollie_customer_id = mollie_dude.get_account_mollie_customer_id(
                            invoice.account,
                            mollie
                        )
                        
                        # Get webhook URL
                        webhook_url = mollie_dude.get_webhook_url_from_request(info.context)
                        # For development
                        if "localhost" in webhook_url:
                            webhook_url = webhook_url.replace("localhost:8000", "dev.costasiella.com:8000")
                        
                        # Check if invoice contains subscription
                        invoice_contains_subscription = invoice.items_contain_subscription()
                        sequence_type = None
                        if invoice_contains_subscription:
                            # Check if we have a mandate
                            mandates = mollie_dude.get_account_mollie_mandates(invoice.account, mollie)
                            # set default sequence type, change to recurring if a valid mandate is found.
                            sequence_type = 'first'
                            if mandates['count'] > 0:
                                # background payment
                                valid_mandate = False
                                for mandate in mandates['_embedded']['mandates']:
                                    if mandate['status'] == 'valid':
                                        valid_mandate = True
                                        break

                                if valid_mandate:
                                    # Do a normal payment, probably an automatic payment failed somewhere in the process
                                    # and customer should pay manually now
                                    sequence_type = None
                        
                        # Fetch currency eg. EUR or USD, etc.
                        from ..modules.finance_tools import get_currency
                        currency = get_currency() or "EUR"
                        
                        # Create payment
                        payment = mollie.payments.create({
                            'amount': {
                                'currency': currency,
                                'value': str(amount)
                            },
                            'description': description,
                            'sequenceType': sequence_type,
                            'customerId': mollie_customer_id,
                            'redirectUrl': redirect_url,
                            'webhookUrl': webhook_url,
                            'metadata': {
                                'invoice_id': invoice.pk
                            }
                        })
                        
                        # Get payment link
                        payment_link = payment.checkout_url
                        
                        # Log payment info
                        from ..models import IntegrationLogMollie
                        log = IntegrationLogMollie(
                            log_source="INVOICE_REMINDER",
                            mollie_payment_id=payment['id'],
                            recurring_type=sequence_type,
                            webhook_url=webhook_url,
                            finance_invoice=invoice,
                        )
                        log.save()
                        
                        logger.info(f"Created payment link for invoice #{invoice.invoice_number}")
                    except Exception as e:
                        logger.error(f"Error creating payment link for invoice #{invoice.invoice_number}: {str(e)}")
                        payment_link = None
                else:
                    logger.info(f"Skipping payment link generation for invoice #{invoice.invoice_number} - Mollie integration disabled")
                

                
                # Get bank transfer details from system settings
                # These are especially important when payment links are disabled
                try:
                    bank_name = system_setting_dude.get('finance_bank_name')
                    account_holder = system_setting_dude.get('finance_bank_account_holder')
                    iban = system_setting_dude.get('finance_bank_iban')
                    bic = system_setting_dude.get('finance_bank_bic')
                except Exception as e:
                    # If there's an error accessing system settings, use fallback values
                    logger.warning(f"Error accessing bank transfer system settings: {str(e)}")
                    bank_name = None
                    account_holder = None
                    iban = None
                    bic = None
                
                # Use fallback values if settings are not found
                bank_name = bank_name or 'Your Bank'
                account_holder = account_holder or organization_name
                iban = iban or 'IBAN number not configured'
                bic = bic or 'BIC/SWIFT code not configured'
                
                # Prepare email context
                context = {
                    'invoice': invoice,
                    'payment_link': payment_link,  # This will be None if payment links are disabled
                    'organization_name': organization_name,
                    # Include bank transfer details
                    'bank_name': bank_name,
                    'account_holder': account_holder,
                    'iban': iban,
                    'bic': bic
                }
                
                # Determine which email template to use based on payment link availability
                if payment_link:
                    template_name = 'email/invoice_reminder_with_payment_link.html'
                    logger.info(f"Using payment link template for invoice #{invoice.invoice_number}")
                else:
                    template_name = 'email/invoice_reminder_without_payment_link.html'
                    logger.info(f"Using bank transfer template for invoice #{invoice.invoice_number}")
                
                # Render email template
                email_content = render_to_string(template_name, context)
                
                # Send email
                subject = f'Reminder: Invoice #{invoice.invoice_number} is Overdue'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [invoice.account.email]
                
                email = EmailMessage(
                    subject,
                    email_content,
                    from_email,
                    recipient_list,
                    headers={'Content-Type': 'text/html'}
                )
                email.content_subtype = "html"  # Main content is now text/html
                email.send()
                
                successful_reminders += 1
                
            except MollieError as me:
                # Log specific Mollie errors with detailed information
                logger.error(f"Mollie error for invoice #{invoice.invoice_number}: {str(me)}")
                
                # Check for API key related errors
                error_message = str(me).lower()
                if 'invalid api key' in error_message or 'unauthorized' in error_message or 'authentication' in error_message:
                    logger.error("Mollie API key appears to be invalid or unauthorized. Please check your API key configuration.")
                    # Add a system notification or alert here if needed
                
                # Print more details about the request that caused the error
                if hasattr(me, 'request') and me.request:
                    logger.error(f"Request details: {me.request.url}, Method: {me.request.method}")
                    logger.error(f"Request headers: {me.request.headers}")
                    
            except Exception as e:
                # Log other errors but continue processing other invoices
                logger.error(f"Error sending reminder for invoice #{invoice.invoice_number}: {str(e)}")
                # Print stack trace for debugging
                logger.error(f"Stack trace: {traceback.format_exc()}")
        
        # Return result
        return SendInvoiceReminders(
            result=SendInvoiceReminderResultType(
                count=successful_reminders,
                success=successful_reminders > 0,
                message=f"Successfully sent {successful_reminders} reminder(s) out of {overdue_invoices.count()} overdue invoice(s)"
            )
        )


class FinanceInvoiceReminderMutation(graphene.ObjectType):
    send_invoice_reminders = SendInvoiceReminders.Field()


# Add the following import at the top of the file
from graphql_relay import to_global_id
