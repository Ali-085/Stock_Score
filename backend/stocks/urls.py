from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StockCurrentScoreListView,
    StockHistoricScoreListView,
    UserWatchlistViewSet,
    StockListView
)

router = DefaultRouter()
router.register(r'watchlist', UserWatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('current-scores/', StockCurrentScoreListView.as_view(), name='stock-current-scores'),
    path('historic-scores/', StockHistoricScoreListView.as_view(), name='stock-historic-scores'),
    path('', include(router.urls)),
    path('', StockListView.as_view(), name='stock-list'),  # This should be last to avoid conflicts
]
