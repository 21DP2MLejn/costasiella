from django.template.loader import render_to_string
from datetime import date, timedelta
import os
import sys

# Add the project path to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django
django.setup()

# Create a mock context with all the data needed for the template
context = {
    "account_subscription": {
        "organization_subscription": {
            "name": "Monthly Unlimited"
        },
        "date_start": date.today(),
        "date_end": date.today() + timedelta(days=365),
        "finance_payment_method": {
            "name": "Direct Debit"
        }
    },
    "account": {
        "full_name": "Test User"
    },
    "organization": "Your Studio Name",
    "site_url": "http://localhost:3000",
    "credits_total": 10,
    "subscription_price": "€50.00",
    "next_payment_date": date.today() + timedelta(days=30),
    "related_invoice": {
        "invoice_number": "INV-2025-001",
        "date_due": date.today() + timedelta(days=14),
        "id": 123
    }
}

# Render the template with the mock context
html_message = render_to_string('email/subscription_activated.html', context)

# Save the rendered HTML to a file for inspection
with open('subscription_email_test.html', 'w') as f:
    f.write(html_message)

print("Template rendered successfully. Check subscription_email_test.html")
