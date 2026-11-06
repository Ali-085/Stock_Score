from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'subscription_tier', 'subscription_status', 'is_staff']
    list_filter = ['subscription_tier', 'subscription_status', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'stripe_customer_id']
    
    # Make subscription fields read-only - only webhooks should modify these
    readonly_fields = ['stripe_customer_id', 'subscription_tier', 'subscription_status']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Subscription Info (Read-Only - Modified by Stripe Webhooks)', {
            'fields': ('stripe_customer_id', 'subscription_tier', 'subscription_status')
        }),
    )
