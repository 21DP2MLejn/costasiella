# Mollie Payment Integration

This document provides information about the Mollie payment integration in Costasiella, specifically for the invoice reminder system.

## Overview

The invoice reminder system can generate payment links for overdue invoices using the Mollie payment API. This integration is optional, and the system will fall back to providing bank transfer details if Mollie integration is not configured or if there are issues with the API key.

## Configuration

### Setting up the Mollie API Key

1. Create a Mollie account at [mollie.com](https://www.mollie.com/)
2. In your Mollie Dashboard, go to Developers > API keys
3. Copy either your Test API key (starts with `test_`) or Live API key (starts with `live_`)
4. In Costasiella, go to System Settings
5. Add or update the setting with key `integration_mollie_api_key` and set the value to your Mollie API key

### Bank Transfer Details

When payment links are disabled or unavailable, the system will include bank transfer details in the invoice reminder emails. Configure these settings:

- `finance_bank_name`: Your bank's name
- `finance_bank_account_holder`: Account holder name
- `finance_bank_iban`: IBAN number
- `finance_bank_bic`: BIC/SWIFT code

## Testing the Mollie API Key

You can test your Mollie API key using the provided management command:

```bash
# Test using the API key from system settings
python manage.py test_mollie_api

# Test with a specific API key
python manage.py test_mollie_api --key your_api_key

# Show detailed information
python manage.py test_mollie_api --verbose
```

## Troubleshooting

### Common Issues

1. **Invalid API Key**
   - Ensure the API key is correctly copied from the Mollie Dashboard
   - Check that you're using the right key type (test or live)
   - Verify the API key hasn't been revoked in your Mollie Dashboard

2. **Unauthorized Errors**
   - Your Mollie account may have restrictions or insufficient permissions
   - Contact Mollie support if the issue persists

3. **Network Issues**
   - Ensure your server can connect to the Mollie API (api.mollie.com)
   - Check firewall settings if necessary

### Logs

The system logs detailed information about Mollie API interactions. Check the logs for error messages and troubleshooting information:

- API key validation issues
- Payment link generation errors
- Specific error messages from the Mollie API

## Email Templates

The system uses two different email templates for invoice reminders:

1. `invoice_reminder_with_payment_link.html`: Used when a Mollie payment link is available
2. `invoice_reminder_without_payment_link.html`: Used when payment links are disabled or unavailable

Both templates include bank transfer details, but the first one prominently displays the payment link button.

## Optional Integration

The Mollie integration is designed to be optional. If no valid API key is configured, the system will:

1. Log appropriate warning messages
2. Skip payment link generation
3. Use the bank transfer template for reminder emails
4. Continue to function normally for sending reminders

This ensures that the invoice reminder system remains operational even without a valid Mollie account or API key.
