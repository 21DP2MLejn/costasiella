"""
Simple test script for subscription activation email template
This script doesn't use Django models or any database access
"""
import os
import sys
from datetime import date, timedelta
from django.template import Template, Context

# Sample HTML template content - copy of the actual template with minimal modifications
TEMPLATE_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header" style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #333; margin-bottom: 10px;">Jūsu abonements ir aktivizēts</h1>
            <p style="color: #666;">{{ organization }}</p>
        </div>
        
        <div class="subscription-info" style="margin-bottom: 25px;">
            <p>Labdien, {{ account.full_name }}!</p>
            <p>Mēs ar prieku paziņojam, ka jūsu abonements ir veiksmīgi aktivizēts.</p>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #333;">Abonementa informācija</h3>
                <p><strong>Abonementa tips:</strong> {{ account_subscription.organization_subscription.name }}</p>
                <p><strong>Cena:</strong> {{ subscription_price }}</p>
                <p><strong>Sākuma datums:</strong> {{ account_subscription.date_start|date:"d.m.Y" }}</p>
                {% if account_subscription.date_end %}
                <p><strong>Beigu datums:</strong> {{ account_subscription.date_end|date:"d.m.Y" }}</p>
                {% endif %}
                <p><strong>Kredīti:</strong> {{ credits_total }}</p>
            </div>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #f0f7ff; border-radius: 5px; border-left: 4px solid #0078d7;">
                <h3 style="margin-top: 0; color: #333;">Maksājuma informācija</h3>
                <p><strong>Nākamais maksājums:</strong> {{ next_payment_date|date:"d.m.Y" }}</p>
                <p><strong>Maksājuma summa:</strong> {{ subscription_price }}</p>
                {% if account_subscription.finance_payment_method %}
                <p><strong>Maksājuma metode:</strong> {{ account_subscription.finance_payment_method.name }}</p>
                {% endif %}
                
                {% if related_invoice %}
                <p style="margin-top: 15px;">Jūsu rēķins ir sagatavots un nosūtīts uz jūsu e-pastu.</p>
                <p><strong>Rēķina numurs:</strong> {{ related_invoice.invoice_number }}</p>
                <p><strong>Apmaksas termiņš:</strong> {{ related_invoice.date_due|date:"d.m.Y" }}</p>
                {% endif %}
            </div>
        </div>
        
        <p>Jūs varat apskatīt savu abonementu un rezervēt nodarbības mūsu mājaslapā:</p>
        
        <div style="margin: 20px 0; text-align: center;">
            <a href="{{ site_url }}/#/shop/account/subscriptions" style="display: inline-block; background-color: #4CAF50; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">Apskatīt abonementu</a>
            
            {% if related_invoice %}
            <a href="{{ site_url }}/#/shop/account/invoice/{{ related_invoice.id }}" style="display: inline-block; background-color: #FF9800; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Apskatīt rēķinu</a>
            {% endif %}
        </div>
        
        <div class="footer" style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; color: #666; font-size: 0.9em;">
            <p>Ja jums ir kādi jautājumi par jūsu abonementu vai maksājumiem, lūdzu, sazinieties ar mums.</p>
            <p>Paldies par sadarbību!</p>
            <p>Ar cieņu,<br>{{ organization }}</p>
        </div>
    </div>
</body>
</html>
"""

# Create a context with sample data
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

# Create a Django template from our template content
template = Template(TEMPLATE_CONTENT)

# Render the template with our context
rendered_html = template.render(Context(context))

# Save the rendered HTML to a file
with open('subscription_email_preview.html', 'w') as f:
    f.write(rendered_html)

print("Email template rendered successfully!")
print("Preview saved to: subscription_email_preview.html")
