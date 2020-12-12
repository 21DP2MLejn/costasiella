# Generated by Django 3.0.8 on 2020-12-12 13:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('costasiella', '0056_financeinvoiceitem_schedule_event_ticket'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleitemattendance',
            name='account_schedule_event_ticket',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='costasiella.AccountScheduleEventTicket'),
        ),
        migrations.AlterField(
            model_name='accountscheduleeventticket',
            name='schedule_event_ticket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='costasiella.ScheduleEventTicket'),
        ),
        migrations.AlterField(
            model_name='financeorderitem',
            name='attendance_type',
            field=models.CharField(choices=[['CLASSPASS', 'Classpass'], ['SUBSCRIPTION', 'Subscription'], ['COMPLEMENTARY', 'Complementary'], ['REVIEW', 'To be reviewed'], ['RECONCILE_LATER', 'Reconcile later'], ['SCHEDULE_EVENT_TICKET', 'Schedule event ticket']], max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='scheduleitemattendance',
            name='attendance_type',
            field=models.CharField(choices=[['CLASSPASS', 'Classpass'], ['SUBSCRIPTION', 'Subscription'], ['COMPLEMENTARY', 'Complementary'], ['REVIEW', 'To be reviewed'], ['RECONCILE_LATER', 'Reconcile later'], ['SCHEDULE_EVENT_TICKET', 'Schedule event ticket']], max_length=255),
        ),
    ]
