from django.db import models
from django.conf import settings


class SubscriptionPlan(models.Model):
    """Subscription plan/tier definitions"""
    
    TIER_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('elite', 'Elite'),
    ]
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    features = models.JSONField(default=dict, help_text="JSON object of features for this plan")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (${self.price_per_month}/mo)"
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['price_per_month']


class UserSubscription(models.Model):
    """Track user subscriptions"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='user_subscriptions')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive', db_index=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    class Meta:
        db_table = 'user_subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'current_period_end']),
        ]


class APIUsageLog(models.Model):
    """Optional: Track API usage per user"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_usage_logs')
    endpoint = models.CharField(max_length=255)
    request_count = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} at {self.timestamp}"
    
    class Meta:
        db_table = 'api_usage_logs'
        ordering = ['-timestamp']
