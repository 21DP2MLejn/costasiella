import io

from django.utils.translation import gettext as _
from django.http import Http404, HttpResponse, FileResponse
from django.template.loader import get_template, render_to_string

from ..models import AppSettings, FinanceInvoice, FinanceInvoiceItem, Organization
from ..modules.gql_tools import require_login_and_permission, get_rid

from django.utils.translation import gettext as _

from ..modules.graphql_jwt_tools import get_user_from_cookie


def _verifiy_permission_or_account(request, finance_invoice, **kwargs):
    """
    :param request:
    :param finance_invoice:
    :return:
    """
    user = get_user_from_cookie(request, **kwargs)

    if not user:
        return False

    if user.has_perm('costasiella.view_financeinvoice') or finance_invoice.account == user:
        return True
    else:
        return False


def invoice_html(node_id):
    """
    Return rendered invoice html template
    """
    from ..dudes import SystemSettingDude

    rid = get_rid(node_id)
    finance_invoice = FinanceInvoice.objects.get(id=rid.id)

    if not finance_invoice:
        raise Http404(_("Invoice not found..."))

    system_settings_dude = SystemSettingDude()
    currency_symbol = system_settings_dude.get("finance_currency_symbol") or "€"

    app_settings = AppSettings.objects.get(id=1)
    organization = Organization.objects.get(id=100)
    logo_url = organization.logo_invoice.url if organization.logo_invoice else ""
    items = FinanceInvoiceItem.objects.filter(
        finance_invoice=finance_invoice
    )
    tax_rates = finance_invoice.tax_rates_amounts()

    # Try to use the template, but provide a fallback if it's not found
    template_path = 'system/invoices/export_invoice_pdf.html'
    
    try:
        t = get_template(template_path)
        
        rendered_template = render_to_string(
            template_path,
            {
                "currency_symbol": currency_symbol,
                "logo_url": logo_url,
                "studio": {
                    "name": "studio name",
                },
                "invoice": finance_invoice,
                "date_sent": finance_invoice.date_sent,
                "organization": organization,
                "items": items,
                "tax_rates": tax_rates,
            }
        )
    except Exception as e:
        # If template is not found, create a simple HTML invoice
        rendered_template = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invoice #{finance_invoice.invoice_number}</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .invoice-header {{ margin-bottom: 20px; }}
                .invoice-details {{ margin: 20px 0; padding: 15px; background-color: #f9f9f9; }}
                .invoice-items {{ width: 100%; border-collapse: collapse; }}
                .invoice-items th, .invoice-items td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .invoice-total {{ margin-top: 20px; text-align: right; }}
            </style>
        </head>
        <body>
            <div class="invoice-header">
                <h1>Invoice #{finance_invoice.invoice_number}</h1>
                <p><strong>Organization:</strong> {organization.name}</p>
            </div>
            
            <div class="invoice-details">
                <p><strong>Invoice Number:</strong> {finance_invoice.invoice_number}</p>
                <p><strong>Date Created:</strong> {finance_invoice.date_created}</p>
                <p><strong>Date Due:</strong> {finance_invoice.date_due}</p>
                <p><strong>Status:</strong> {finance_invoice.status}</p>
                <p><strong>Customer:</strong> {finance_invoice.account.full_name if finance_invoice.account else 'N/A'}</p>
            </div>
            
            <table class="invoice-items">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td>{item.product_name}</td><td>{item.description}</td><td>{item.quantity}</td><td>{currency_symbol}{item.price_display}</td><td>{currency_symbol}{item.total_display}</td></tr>" for item in items])}
                </tbody>
            </table>
            
            <div class="invoice-total">
                <p><strong>Subtotal:</strong> {currency_symbol}{finance_invoice.subtotal_display}</p>
                <p><strong>Tax:</strong> {currency_symbol}{finance_invoice.tax_display}</p>
                <p><strong>Total:</strong> {currency_symbol}{finance_invoice.total_display}</p>
                <p><strong>Balance:</strong> {currency_symbol}{finance_invoice.balance_display}</p>
            </div>
        </body>
        </html>
        '''

    return [finance_invoice, rendered_template]


# Create your views here.
def invoice_pdf(request, node_id, **kwargs):
    """
    Export invoice as PDF

    :param: POST: node_id - FinanceInvoiceNode ID
    """
    import weasyprint

    finance_invoice, html = invoice_html(node_id)
    if not _verifiy_permission_or_account(request, finance_invoice, **kwargs):
        raise Http404(_("Invoice not found..."))

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    pdf = weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(buffer)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)

    filename = _('invoice') + '_' + finance_invoice.invoice_number + '.pdf'

    return FileResponse(buffer, as_attachment=True, filename=filename)


def invoice_pdf_preview(request, node_id):
    """
    Preview for invoice_pdf

    :param: POST: node_id - FinanceInvoiceNode ID
    """

    finance_invoice, html = invoice_html(node_id)
    if not _verifiy_permission_or_account(request, finance_invoice):
        raise Http404(_("Invoice not found..."))

    return HttpResponse(html)
