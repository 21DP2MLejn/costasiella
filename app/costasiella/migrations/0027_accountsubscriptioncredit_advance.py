# Generated by Django 4.0.7 on 2022-12-22 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('costasiella', '0026_rename_credit_accumulation_days_organizationsubscription_credit_validity'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsubscriptioncredit',
            name='advance',
            field=models.BooleanField(default=False),
        ),
    ]
