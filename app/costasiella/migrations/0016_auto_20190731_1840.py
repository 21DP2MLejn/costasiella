# Generated by Django 2.2.2 on 2019-07-31 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('costasiella', '0015_financeinvoiceitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeinvoiceitem',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='financeinvoiceitem',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='financeinvoiceitem',
            name='vat',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
    ]
