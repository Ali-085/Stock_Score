from django.contrib import admin
from .models import Stock, StockCurrentScore, StockHistoricScore, UserWatchlist


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'exchange', 'is_active', 'updated_at']
    list_filter = ['is_active', 'exchange']
    search_fields = ['symbol', 'name']


@admin.register(StockCurrentScore)
class StockCurrentScoreAdmin(admin.ModelAdmin):
    list_display = ['stock', 'ml_rank', 'vol_rank', 'value_rank', 'risk_score', 'confidence_score', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['stock__symbol', 'stock__name']
    ordering = ['ml_rank']


@admin.register(StockHistoricScore)
class StockHistoricScoreAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'ml_rank', 'vol_rank', 'value_rank', 'risk_score']
    list_filter = ['date']
    search_fields = ['stock__symbol', 'stock__name']
    date_hierarchy = 'date'
    ordering = ['-date', 'ml_rank']


@admin.register(UserWatchlist)
class UserWatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'stock__symbol']
    date_hierarchy = 'added_at'
