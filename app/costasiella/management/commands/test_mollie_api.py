import logging
import sys
from django.core.management.base import BaseCommand
from mollie.api.client import Client
from mollie.api.error import Error as MollieError

from costasiella.dudes.system_setting_dude import SystemSettingDude
from costasiella.dudes.mollie_dude import MollieDude

class Command(BaseCommand):
    help = 'Test Mollie API key and connection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key',
            dest='api_key',
            help='Provide a Mollie API key to test (overrides system settings)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger(__name__)

        # Get API key from arguments or system settings
        api_key = options.get('api_key')
        verbose = options.get('verbose', False)
        
        if not api_key:
            self.stdout.write("No API key provided as argument. Checking system settings...")
            mollie_dude = MollieDude()
            api_key = mollie_dude.get_api_key()
            
            if not api_key:
                self.stdout.write(self.style.ERROR("❌ No Mollie API key found in system settings"))
                self.stdout.write("\nTo configure a Mollie API key:")
                self.stdout.write("1. Go to System Settings")
                self.stdout.write("2. Add a setting with key 'integration_mollie_api_key'")
                self.stdout.write("3. Set the value to your Mollie API key")
                return
        
        # Check if it's a test or live key
        is_test = api_key.startswith('test_')
        key_type = "TEST" if is_test else "LIVE"
        
        self.stdout.write(f"Testing {key_type} Mollie API key: {api_key[:6]}...{api_key[-4:]}")
        
        # Initialize Mollie client
        mollie = Client()
        
        try:
            # Set API key
            mollie.set_api_key(api_key)
            
            # Test API key by making a simple request
            methods = mollie.methods.list()
            
            # If we get here, the API key is valid
            self.stdout.write(self.style.SUCCESS(f"✅ Mollie API key is valid ({key_type} mode)"))
            
            if verbose:
                self.stdout.write("\nAvailable payment methods:")
                for method in methods:
                    self.stdout.write(f"- {method.description} ({method.id})")
                
                # Get organization info
                org = mollie.organizations.get('me')
                self.stdout.write("\nOrganization details:")
                self.stdout.write(f"Name: {org.name}")
                self.stdout.write(f"Email: {org.email}")
                self.stdout.write(f"Address: {org.address.city}, {org.address.country}")
                
                # Get balance if available (only for live keys)
                if not is_test:
                    try:
                        balance = mollie.balances.get('primary')
                        self.stdout.write(f"\nCurrent balance: {balance.amount['value']} {balance.amount['currency']}")
                    except MollieError as me:
                        if "has no access to balances" in str(me):
                            self.stdout.write("Balance information not available (requires different permissions)")
                        else:
                            self.stdout.write(f"Could not retrieve balance: {str(me)}")
            
        except MollieError as me:
            self.stdout.write(self.style.ERROR(f"❌ Mollie API key validation failed: {str(me)}"))
            
            # Provide more specific guidance based on the error
            error_message = str(me).lower()
            if 'invalid api key' in error_message:
                self.stdout.write("\nPossible issues:")
                self.stdout.write("- The API key format is incorrect")
                self.stdout.write("- The API key has been revoked")
                self.stdout.write("- You're using a test key in live mode or vice versa")
                
                self.stdout.write("\nRecommended actions:")
                self.stdout.write("1. Verify the API key in your Mollie Dashboard")
                self.stdout.write("2. Generate a new API key if necessary")
                self.stdout.write("3. Make sure you're using the correct key type (test/live)")
                
            elif 'unauthorized' in error_message or 'authentication' in error_message:
                self.stdout.write("\nPossible issues:")
                self.stdout.write("- The API key doesn't have sufficient permissions")
                self.stdout.write("- Your Mollie account may have restrictions")
                
                self.stdout.write("\nRecommended actions:")
                self.stdout.write("1. Check your Mollie account status")
                self.stdout.write("2. Verify API key permissions in your Mollie Dashboard")
                self.stdout.write("3. Contact Mollie support if the issue persists")
            
            # Print request details if available
            if hasattr(me, 'request') and me.request and verbose:
                self.stdout.write("\nRequest details:")
                self.stdout.write(f"URL: {me.request.url}")
                self.stdout.write(f"Method: {me.request.method}")
                self.stdout.write(f"Headers: {me.request.headers}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {str(e)}"))
            
        # Provide general guidance
        self.stdout.write("\nFor more information about Mollie API keys:")
        self.stdout.write("- Documentation: https://docs.mollie.com/overview/authentication")
        self.stdout.write("- Dashboard: https://www.mollie.com/dashboard/developers/api-keys")
