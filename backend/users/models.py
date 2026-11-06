from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with subscription fields"""
    
    SUBSCRIPTION_TIERS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('elite', 'Elite'),
    ]
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    ]
    
    # Make email required and unique
    email = models.EmailField('email address', unique=True, blank=False, db_index=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    subscription_tier = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_TIERS, 
        default='free',
        db_index=True
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS,
        default='inactive',
        db_index=True
    )
    
    # Required fields for createsuperuser command
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['subscription_tier', 'subscription_status']),
        ]
