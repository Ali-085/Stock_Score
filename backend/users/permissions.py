from rest_framework import permissions


class SubscriptionPermission(permissions.BasePermission):
    """
    Permission class to check subscription tier access
    SECURITY: Always validates tier AND status - no trust in frontend
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
        
        # Get required tier from view (defaults to 'free' for public endpoints)
        required_tier = getattr(view, 'required_tier', 'free')
        
        # Define tier hierarchy
        tier_levels = {
            'free': 0,
            'basic': 1,
            'pro': 2,
            'elite': 3,
        }
        
        user_tier_level = tier_levels.get(request.user.subscription_tier, 0)
        required_tier_level = tier_levels.get(required_tier, 0)
        
        # CRITICAL: For ANY paid tier requirement, validate subscription status
        if required_tier_level > 0:  # Any paid tier required
            # User must have active, trialing, or past_due (grace period) subscription
            if request.user.subscription_status not in ['active', 'trialing', 'past_due']:
                return False
            
            # User's tier must be sufficient
            if user_tier_level < required_tier_level:
                return False
        
        # For free tier endpoints, no status check needed
        return True
