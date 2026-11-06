from django.urls import path
from .views import (
    SubscriptionPlanListView,
    UserSubscriptionListView,
    create_checkout_session,
    preview_subscription_change,
    confirm_subscription_change,
    cancel_subscription,
    stripe_webhook
)

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('my-subscriptions/', UserSubscriptionListView.as_view(), name='my-subscriptions'),
    path('create-checkout-session/', create_checkout_session, name='create-checkout-session'),
    path('preview-change/', preview_subscription_change, name='preview-subscription-change'),
    path('confirm-change/', confirm_subscription_change, name='confirm-subscription-change'),
    path('cancel-subscription/', cancel_subscription, name='cancel-subscription'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]
