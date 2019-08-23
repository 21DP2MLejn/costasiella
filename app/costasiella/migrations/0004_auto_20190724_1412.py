# Generated by Django 2.2.2 on 2019-07-24 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('costasiella', '0003_auto_20190723_1702'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinanceInvoiceGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('display_public', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('next_id', models.PositiveIntegerField()),
                ('due_after_days', models.PositiveSmallIntegerField()),
                ('prefix', models.CharField(default='', max_length=255)),
                ('prefix_year', models.BooleanField(default=True)),
                ('auto_reset_prefix_year', models.BooleanField(default=True)),
                ('terms', models.TextField(default='')),
                ('footer', models.TextField(default='')),
                ('code', models.CharField(default='', help_text='Journal code in your accounting software.', max_length=255)),
            ],
        ),
        migrations.AlterField(
            model_name='financecostcenter',
            name='code',
            field=models.CharField(default='', help_text='Cost center code in your accounting software.', max_length=255),
        ),
    ]
