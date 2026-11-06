from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, APIUsageLog


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'price_per_month', 'is_active', 'created_at']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'stripe_price_id']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_start', 'current_period_end', 'cancel_at_period_end']
    list_filter = ['status', 'plan', 'cancel_at_period_end']
    search_fields = ['user__username', 'user__email', 'stripe_subscription_id']
    date_hierarchy = 'created_at'
    
    # Make subscription data read-only - only webhooks should modify
    readonly_fields = ['user', 'plan', 'stripe_subscription_id', 'status', 
                       'current_period_start', 'current_period_end', 
                       'cancel_at_period_end', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Prevent manual creation - only webhooks create subscriptions
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion - let Stripe webhooks handle lifecycle
        return False


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint', 'request_count', 'timestamp']
    list_filter = ['endpoint', 'timestamp']
    search_fields = ['user__username', 'endpoint']
    date_hierarchy = 'timestamp'
