from django.core.management.base import BaseCommand
from costasiella.models import SystemMailTemplate
from pathlib import Path


class Command(BaseCommand):
    help = 'Updates the invoice notification template in the database'

    def handle(self, *args, **options):
        template_path = Path(__file__).parent.parent.parent / 'templates' / 'email' / 'invoice_notification_lv.html'
        template_content = template_path.read_text()

        template = SystemMailTemplate.objects.get(pk=60000)
        template.subject = 'Rēķins Nr. {{ invoice.invoice_number }}'
        template.title = 'Rēķins'
        template.description = 'Rēķins Nr. {{ invoice.invoice_number }}'
        template.content = template_content
        template.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated invoice template'))
