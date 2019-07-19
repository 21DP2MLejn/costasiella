# Generated by Django 2.2.2 on 2019-07-19 10:00

import costasiella.modules.encrypted_fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('costasiella', '0016_organizationappointmentprice'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountTeacherProfile',
            fields=[
                ('account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('classes', models.BooleanField(default=True)),
                ('appointments', models.BooleanField(default=False)),
                ('events', models.BooleanField(default=False)),
                ('role', costasiella.modules.encrypted_fields.EncryptedTextField(default='')),
                ('education', costasiella.modules.encrypted_fields.EncryptedTextField(default='')),
                ('bio', costasiella.modules.encrypted_fields.EncryptedTextField(default='')),
                ('url_bio', costasiella.modules.encrypted_fields.EncryptedTextField(default='')),
                ('url_website', costasiella.modules.encrypted_fields.EncryptedTextField(default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
