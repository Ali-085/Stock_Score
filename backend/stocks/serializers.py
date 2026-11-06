from rest_framework import serializers
from .models import Stock, StockCurrentScore, StockHistoricScore, UserWatchlist


class StockSerializer(serializers.ModelSerializer):
    """Stock basic info serializer"""
    
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name', 'exchange']


class StockCurrentScoreSerializer(serializers.ModelSerializer):
    """Current stock score serializer - dynamically filters fields by tier"""
    
    stock = StockSerializer(read_only=True)
    
    class Meta:
        model = StockCurrentScore
        fields = ['id', 'stock', 'ml_rank', 'vol_rank', 'value_rank', 
                  'risk_score', 'confidence_score', 'next_day_up_prob', 
                  'next_week_up_prob', 'last_updated']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get subscription tier from context (set by view)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_tier = getattr(request.user, 'subscription_tier', 'free')
            
            # Remove premium fields for lower tiers AT SERIALIZATION TIME
            if user_tier in ['free', 'basic']:
                # Only these fields allowed for free/basic
                allowed_fields = {'id', 'stock', 'ml_rank', 'vol_rank', 'value_rank', 'risk_score', 'last_updated'}
                # Remove all other fields
                for field_name in list(self.fields.keys()):
                    if field_name not in allowed_fields:
                        self.fields.pop(field_name)
            
            elif user_tier == 'pro':
                # Pro gets more but not probabilities
                self.fields.pop('next_day_up_prob', None)
                self.fields.pop('next_week_up_prob', None)


class StockHistoricScoreSerializer(serializers.ModelSerializer):
    """Historic stock score serializer - dynamically filters fields by tier"""
    
    stock = StockSerializer(read_only=True)
    
    class Meta:
        model = StockHistoricScore
        fields = ['id', 'stock', 'date', 'ml_rank', 'vol_rank', 'value_rank',
                  'risk_score', 'confidence_score', 'next_day_up_prob',
                  'next_week_up_prob']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get subscription tier from context (set by view)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_tier = getattr(request.user, 'subscription_tier', 'free')
            
            # Remove premium fields for lower tiers AT SERIALIZATION TIME
            if user_tier in ['free', 'basic']:
                # Only these fields allowed for free/basic
                allowed_fields = {'id', 'stock', 'date', 'ml_rank', 'vol_rank', 'value_rank', 'risk_score'}
                # Remove all other fields
                for field_name in list(self.fields.keys()):
                    if field_name not in allowed_fields:
                        self.fields.pop(field_name)
            
            elif user_tier == 'pro':
                # Pro gets more but not probabilities
                self.fields.pop('next_day_up_prob', None)
                self.fields.pop('next_week_up_prob', None)


class UserWatchlistSerializer(serializers.ModelSerializer):
    """User watchlist serializer"""
    
    stock = StockSerializer(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(
        queryset=Stock.objects.all(), 
        source='stock', 
        write_only=True
    )
    
    class Meta:
        model = UserWatchlist
        fields = ['id', 'stock', 'stock_id', 'added_at', 'notes']
        read_only_fields = ['id', 'added_at']
