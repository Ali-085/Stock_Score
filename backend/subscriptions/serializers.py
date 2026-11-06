from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Subscription plan serializer"""
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'tier', 'price_per_month', 'features', 'stripe_price_id']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User subscription serializer"""
    
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'plan_details', 'status', 'current_period_start', 
                  'current_period_end', 'cancel_at_period_end', 'created_at']
        read_only_fields = ['id', 'status', 'current_period_start', 
                            'current_period_end', 'created_at']
