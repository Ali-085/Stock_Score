from django.db import models
from django.conf import settings


class Stock(models.Model):
    """Stock symbol and basic info"""
    
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    class Meta:
        db_table = 'stocks'
        ordering = ['symbol']


class StockCurrentScore(models.Model):
    """Latest ML scores for each stock"""
    
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE, related_name='current_score')
    ml_rank = models.IntegerField(null=True, blank=True, help_text="ML-based rank")
    vol_rank = models.IntegerField(null=True, blank=True, help_text="Volatility rank")
    value_rank = models.IntegerField(null=True, blank=True, help_text="Value rank")
    risk_score = models.FloatField(null=True, blank=True, help_text="Risk score (0-100)")
    confidence_score = models.FloatField(null=True, blank=True, help_text="Confidence score (0-1)")
    next_day_up_prob = models.FloatField(null=True, blank=True, help_text="Probability of next day up (%)")
    next_week_up_prob = models.FloatField(null=True, blank=True, help_text="Probability of next week up (%)")
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.stock.symbol} - Current Score"
    
    class Meta:
        db_table = 'stock_current_scores'
        ordering = ['ml_rank']


class StockHistoricScore(models.Model):
    """Historical daily ML scores for each stock"""
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='historic_scores')
    date = models.DateField(db_index=True)
    ml_rank = models.IntegerField(null=True, blank=True)
    vol_rank = models.IntegerField(null=True, blank=True)
    value_rank = models.IntegerField(null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    next_day_up_prob = models.FloatField(null=True, blank=True)
    next_week_up_prob = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.date}"
    
    class Meta:
        db_table = 'stock_historic_scores'
        ordering = ['-date', 'ml_rank']
        unique_together = ['stock', 'date']
        indexes = [
            models.Index(fields=['stock', '-date']),
            models.Index(fields=['date']),
        ]


class UserWatchlist(models.Model):
    """Optional: User's watchlist of stocks"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='watched_by')
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}"
    
    class Meta:
        db_table = 'user_watchlist'
        unique_together = ['user', 'stock']
        ordering = ['-added_at']
