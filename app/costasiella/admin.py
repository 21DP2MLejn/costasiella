from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from . import models
from .forms import AccountCreationForm, AccountChangeForm
from django.contrib import messages

# Organization Settings
@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone')

# Subscription related
@admin.register(models.OrganizationSubscriptionGroup)
class OrganizationSubscriptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(models.OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_public', 'display_shop', 'classes', 'subscription_unit', 'unlimited', 'archived')
    search_fields = ('name', 'description')
    list_filter = ('subscription_unit', 'display_public', 'display_shop', 'unlimited', 'archived')

@admin.register(models.OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(models.FinanceGLAccount)
class FinanceGLAccountAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(models.FinanceCostCenter)
class FinanceCostCenterAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(models.FinanceTaxRate)
class FinanceTaxRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'rate_type')
    list_filter = ('rate_type',)

# Account related
@admin.register(models.Account)
class AccountAdmin(UserAdmin):
    add_form = AccountCreationForm
    form = AccountChangeForm
    model = get_user_model()
    list_display = ['email', 'full_name', 'is_active']
    search_fields = ('full_name', 'email')

@admin.register(models.Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(models.AccountSubscription)
class AccountSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('account', 'organization_subscription', 'date_start', 'date_end')

@admin.register(models.FinanceInvoiceItem)
class FinanceInvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('finance_invoice', 'product_name', 'quantity', 'price', 'subtotal', 'tax')
    search_fields = ('product_name', 'finance_invoice__invoice_number')

@admin.register(models.FinanceInvoice)
class FinanceInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'account', 'date_sent', 'date_due', 'status', 'total')
    list_filter = ('status', 'date_sent')
    search_fields = ('invoice_number', 'account__email', 'account__full_name')
    date_hierarchy = 'date_sent'
    actions = ['send_invoice_notifications']

    def send_invoice_notifications(self, request, queryset):
        success_count = 0
        for invoice in queryset:
            try:
                invoice.send_notification_email()
                success_count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f"Error sending invoice #{invoice.invoice_number}: {str(e)}", 
                    level=messages.ERROR
                )
        
        if success_count:
            self.message_user(
                request,
                f"Successfully sent {success_count} invoice notifications",
                level=messages.SUCCESS
            )
    send_invoice_notifications.short_description = "Send invoice notifications"