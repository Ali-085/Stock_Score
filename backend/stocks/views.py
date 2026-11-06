from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from users.permissions import SubscriptionPermission
from .models import Stock, StockCurrentScore, StockHistoricScore, UserWatchlist
from .serializers import (
    StockSerializer, StockCurrentScoreSerializer,
    StockHistoricScoreSerializer, UserWatchlistSerializer
)


class StockCurrentScoreListView(generics.ListAPIView):
    """
    List current stock scores
    - Free tier: Top 10 stocks only, basic fields
    - Basic tier: Top 50 stocks, basic fields
    - Pro tier: All stocks, no probability fields
    - Elite tier: All stocks, all fields
    
    SECURITY: Tier validation happens at:
    1. Permission level (SubscriptionPermission)
    2. Queryset level (row limiting)
    3. Serializer level (field filtering)
    """
    
    serializer_class = StockCurrentScoreSerializer
    permission_classes = [IsAuthenticated, SubscriptionPermission]
    required_tier = 'free'  # Minimum tier (everyone can access, but with limits)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['stock__symbol']
    
    def get_queryset(self):
        user = self.request.user
        
        # Validate user has active subscription for paid tiers
        if user.subscription_tier != 'free':
            # Allow active, trialing, and past_due (grace period for payment retry)
            if user.subscription_status not in ['active', 'trialing', 'past_due']:
                # Downgrade to free tier limits if subscription expired/canceled
                return StockCurrentScore.objects.select_related('stock').order_by('ml_rank')[:10]
        
        # Apply tier-based row limiting at DATABASE level
        queryset = StockCurrentScore.objects.select_related('stock').order_by('ml_rank')
        
        if user.subscription_tier == 'free':
            return queryset[:10]
        elif user.subscription_tier == 'basic':
            return queryset[:50]
        # Pro and Elite get all rows
        return queryset


class StockHistoricScoreListView(generics.ListAPIView):
    """
    List historic stock scores
    - Free tier: NOT AVAILABLE (blocked by permission)
    - Basic tier: Last 30 days only
    - Pro tier: Last 90 days only  
    - Elite tier: All history
    
    SECURITY: SubscriptionPermission blocks free users entirely
    Queryset filtering enforces date limits at DATABASE level
    """
    
    serializer_class = StockHistoricScoreSerializer
    permission_classes = [IsAuthenticated, SubscriptionPermission]
    required_tier = 'basic'  # FREE USERS BLOCKED BY PERMISSION CLASS
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['stock__symbol', 'date']
    
    def get_queryset(self):
        user = self.request.user
        
        # Double-check subscription status (defense in depth)
        # Allow past_due for grace period (payment retry window)
        if user.subscription_tier == 'free' or user.subscription_status not in ['active', 'trialing', 'past_due']:
            # Return empty queryset if somehow permission was bypassed
            return StockHistoricScore.objects.none()
        
        # Start with base queryset
        queryset = StockHistoricScore.objects.select_related('stock').order_by('-date')
        
        # Apply tier-based date filtering at DATABASE level
        if user.subscription_tier == 'basic':
            cutoff_date = timezone.now().date() - timedelta(days=30)
            queryset = queryset.filter(date__gte=cutoff_date)
        elif user.subscription_tier == 'pro':
            cutoff_date = timezone.now().date() - timedelta(days=90)
            queryset = queryset.filter(date__gte=cutoff_date)
        # Elite tier gets all history (no filter)
        
        return queryset


class UserWatchlistViewSet(viewsets.ModelViewSet):
    """
    Manage user's watchlist
    - Available to all authenticated users
    - Only returns stock basic info, NO scores exposed here
    
    SECURITY: Watchlist only contains stock references, not score data
    Users must call /current-scores/ or /historic-scores/ separately (paywalled)
    """
    
    serializer_class = UserWatchlistSerializer
    permission_classes = [IsAuthenticated]
    required_tier = 'free'  # Available to all users
    
    def get_queryset(self):
        # Only return user's own watchlist (row-level security)
        return UserWatchlist.objects.filter(user=self.request.user).select_related('stock')
    
    def perform_create(self, serializer):
        # Automatically set user from request (prevent user spoofing)
        serializer.save(user=self.request.user)


class StockListView(generics.ListAPIView):
    """List all available stocks - basic info only, no scores"""
    
    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]  # No SubscriptionPermission - all users can see stock list
    required_tier = 'free'  # Explicit: available to all authenticated users
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['symbol', 'exchange']
    search_fields = ['symbol', 'name']
