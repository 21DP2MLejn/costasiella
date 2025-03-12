from django.utils.translation import gettext as _
from mollie.api.error import Error as MollieError
import logging

from .system_setting_dude import SystemSettingDude


class MollieDude:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_mollie_enabled(self):
        """
        Check if Mollie integration is enabled by verifying if a valid API key exists
        
        Returns:
            bool: True if Mollie integration is enabled, False otherwise
        """
        api_key = self.get_api_key()
        return api_key is not None
        
    def get_mollie_client(self):
        """
        Get a configured Mollie client instance
        
        Returns:
            mollie.api.client.Client: Configured Mollie client or None if API key is invalid
        
        Raises:
            Exception: If Mollie client initialization fails
        """
        from mollie.api.client import Client
        
        # Get API key
        api_key = self.get_api_key()
        if not api_key:
            raise Exception("No valid Mollie API key found")
            
        # Initialize client
        mollie = Client()
        mollie.set_api_key(api_key)
        
        return mollie
    
    def is_payment_links_enabled(self):
        """
        Check if payment links are enabled in system settings
        
        Returns:
            bool: True if payment links are enabled, False otherwise
        """
        system_setting_dude = SystemSettingDude()
        payment_links_enabled = system_setting_dude.get("integration_mollie_payment_links_enabled")
        
        # If the setting doesn't exist, default to True for backward compatibility
        if payment_links_enabled is None:
            return True
            
        # Convert string values to boolean
        if isinstance(payment_links_enabled, str):
            return payment_links_enabled.lower() in ['true', 'yes', '1', 'on']
            
        return bool(payment_links_enabled)
    
    def get_api_key(self):
        """
        Fetch & return mollie api key, if any
        """
        system_setting_dude = SystemSettingDude()
        mollie_api_key = system_setting_dude.get("integration_mollie_api_key")
        
        if not mollie_api_key:
            self.logger.error("No Mollie API key found in system settings")
            return None
            
        # Check if the API key is a placeholder value
        if 'your_mollie_api_key_here' in mollie_api_key:
            self.logger.error("Mollie API key appears to be a placeholder value")
            return None
            
        # For development/testing, if the API key doesn't start with 'live_' or 'test_',
        # prefix it with 'test_' to ensure it works in test mode
        if not (mollie_api_key.startswith('live_') or mollie_api_key.startswith('test_')):
            self.logger.info("Adding 'test_' prefix to Mollie API key")
            mollie_api_key = 'test_' + mollie_api_key
        
        # Basic validation of API key format
        if len(mollie_api_key) < 10:  # Mollie API keys are typically much longer
            self.logger.error(f"Mollie API key appears to be invalid (too short)")
            return None
        
        # Log API key format (masked for security)
        key_type = "live" if mollie_api_key.startswith('live_') else "test"
        masked_key = mollie_api_key[:5] + "*" * (len(mollie_api_key) - 9) + mollie_api_key[-4:]
        self.logger.info(f"Using {key_type} Mollie API key: {masked_key}")
        
        # Validate the API key by making a simple API call
        try:
            from mollie.api.client import Client
            mollie = Client()
            mollie.set_api_key(mollie_api_key)
            
            # Make a simple API call to verify the key is valid
            # This will catch authentication issues early
            try:
                # Try to list payment methods - a lightweight API call
                mollie.methods.list()
                self.logger.info(f"✅ Mollie API key validated successfully ({key_type} mode)")
            except MollieError as me:
                # Check for specific API key related errors
                error_message = str(me).lower()
                if 'invalid api key' in error_message:
                    self.logger.error(f"❌ Invalid Mollie API key: {str(me)}")
                    self.logger.error("Please check your API key in the Mollie Dashboard")
                    return None
                elif 'unauthorized' in error_message or 'authentication' in error_message:
                    self.logger.error(f"❌ Unauthorized Mollie API key: {str(me)}")
                    self.logger.error("Your API key may not have sufficient permissions")
                    return None
                else:
                    # Other API errors might not be related to the key itself
                    self.logger.warning(f"⚠️ Mollie API warning: {str(me)}")
                    self.logger.warning("The API key may be valid, but there was an error with the test request")
                    # Still return the key as it might work for other operations
        except Exception as e:
            self.logger.error(f"❌ Error initializing Mollie client: {str(e)}")
            self.logger.error("Check your network connection and Mollie API status")
            # Return None to indicate the API key is not usable
            return None
            
        return mollie_api_key

    def get_webhook_url_from_request(self, request):
        """
        :param request: Django request
        """
        host = request.get_host()
        webhook_url = "https://" + host + "/d/mollie/webhook/"

        return webhook_url

    def get_webhook_url_from_db(self):
        """
        get_webhook_url is preferred as it doesn't depend on a database entry.
        :return:
        """
        system_setting_dude = SystemSettingDude()
        host = system_setting_dude.get("system_hostname")

        webhook_url = "https://" + host + "/d/mollie/webhook/"

        return webhook_url

    def get_account_mollie_customer_id(self, account, mollie):
        """
        :param account: models.Account object
        :param mollie: mollie api client object
        :return: 
        """
        is_valid_account = self._mollie_customer_check_valid(account, mollie)

        if not is_valid_account:
            mollie_customer = mollie.customers.create({
                'name': account.full_name,
                'email': account.email
            })
            mollie_customer_id = mollie_customer['id']
            account.mollie_customer_id = mollie_customer_id
            account.save()
        else:
            mollie_customer_id = account.mollie_customer_id

        return mollie_customer_id

    def _mollie_customer_check_valid(self, account, mollie):
        """
        :param account: models.Account object
        :return: Boolean - True if there is a valid mollie customer for this Costasiella customer
        """
        if not account.mollie_customer_id:
            return False
        else:
            try:
                mollie_customer = mollie.customers.get(account.mollie_customer_id)
                return True
            except Exception as e:
                return False

    def get_account_mollie_mandates(self, account, mollie):
        """
        Get mollie mandates for account
        :param account: Account object
        :param mollie: mollie client object
        :return:
        """

        # check if we have a mollie customer id
        if not account.mollie_customer_id:
            return

        mandates = None
        try:
            mandates = mollie.customer_mandates.with_parent_id(account.mollie_customer_id).list()
        except MollieError as e:
            print(e)

        return mandates
        
    def create_payment_for_invoice(self, invoice):
        """
        Create a Mollie payment for an invoice
        
        Args:
            invoice: The invoice object to create a payment for
            
        Returns:
            str: The payment URL for the customer to complete the payment
            
        Raises:
            MollieError: If there's an error creating the payment
        """
        # Get Mollie client
        mollie_client = self.get_mollie_client()
        
        # Get organization details for payment description
        from ..dudes.system_setting_dude import SystemSettingDude
        system_setting_dude = SystemSettingDude()
        organization_name = system_setting_dude.get('organization_name') or 'Costasiella'
        
        # Create payment
        payment = mollie_client.payments.create({
            'amount': {
                'currency': invoice.currency,
                'value': str(invoice.total),  # Convert to string with 2 decimal places
            },
            'description': f'{organization_name} - Invoice #{invoice.invoice_number}',
            'redirectUrl': f'{system_setting_dude.get("system_hostname")}/invoices',
            'webhookUrl': f'{system_setting_dude.get("system_hostname")}/d/mollie/webhook/',
            'metadata': {
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
            },
        })
        
        # Return the payment URL
        return payment.checkout_url
