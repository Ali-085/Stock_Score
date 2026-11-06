import stripe
import logging
from datetime import timedelta
from urllib.parse import urlparse
from django.conf import settings

# Pin Stripe API version to prevent breaking changes
stripe.api_version = '2024-11-20.acacia'
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionPlanListView(generics.ListAPIView):
    """List all available subscription plans"""
    
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class UserSubscriptionListView(generics.ListAPIView):
    """List current user's subscriptions"""
    
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """Create Stripe checkout session for subscription or update existing subscription"""
    
    from users.models import User
    
    try:
        price_id = request.data.get('price_id')
        if not price_id:
            return Response(
                {'error': 'price_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that the price_id belongs to an active plan
        plan = SubscriptionPlan.objects.filter(
            stripe_price_id=price_id,
            is_active=True
        ).first()
        
        if not plan:
            return Response(
                {'error': 'Invalid or inactive subscription plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Construct redirect URLs from settings - simpler and more secure
        if settings.DEBUG:
            base_url = 'http://localhost:5173'
        else:
            # Get first allowed origin from CORS settings
            base_url = settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'https://yourdomain.com'
        
        # Backend controls the redirect URLs - no need for frontend input
        success_url = f"{base_url}/dashboard?subscription=success"
        cancel_url = f"{base_url}/pricing?subscription=canceled"
        
        # Get user
        user = request.user
        
        # Check if user already has an active subscription
        active_subscription = UserSubscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).first()
        
        # If user has active subscription, check if same plan
        if active_subscription:
            # Check if trying to subscribe to the same plan
            if active_subscription.plan.stripe_price_id == price_id:
                return Response(
                    {'error': 'You are already subscribed to this plan'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if downgrading to free tier (cancel subscription instead)
            if plan.tier == 'free':
                return Response(
                    {'error': 'To downgrade to free tier, please cancel your subscription using the Cancel Plan button.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # For upgrades/downgrades, return a flag to trigger preview dialog
            # Frontend will call preview endpoint, show confirmation, then call confirm endpoint
            return Response({
                'requires_confirmation': True,
                'message': 'Please confirm subscription change',
                'current_plan': active_subscription.plan.tier,
                'new_plan': plan.tier,
            })
        
        # For new subscriptions (no active subscription), create Stripe customer if needed
        if not user.stripe_customer_id:
            # Create customer in Stripe FIRST (fail-early)
            try:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={'user_id': user.id}
                )
            except stripe.StripeError as e:
                logger.error(f"Failed to create Stripe customer: {str(e)}")
                return Response(
                    {'error': 'Failed to create customer account. Please try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Only update DB if Stripe succeeded
            with transaction.atomic():
                user_obj = User.objects.select_for_update().get(id=user.id)
                # Double-check in case another request already created it
                if not user_obj.stripe_customer_id:
                    user_obj.stripe_customer_id = customer.id
                    user_obj.save(update_fields=['stripe_customer_id'])
                # Update the reference
                user = user_obj
        
        # SECURITY: Strict URL validation has been done above
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        
        return Response({
            'sessionId': checkout_session.id,
            'url': checkout_session.url
        })
    
    except stripe.StripeError as e:
        logger.error(f"Stripe error in checkout: {str(e)}")
        return Response(
            {'error': 'Payment processing error. Please try again.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Log the error but don't expose internal details to client
        logger.error(f"Checkout session error: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt  # CSRF exempt - Stripe webhooks use signature verification instead
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.warning("Webhook received without signature header")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except stripe.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    # Log webhook event for debugging and auditing
    logger.info(f"Received Stripe webhook: {event['type']} - {event['id']}")
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    else:
        logger.info(f"Unhandled webhook event type: {event['type']}")
    
    return Response({'status': 'success'})


def handle_checkout_session_completed(session):
    """Handle successful checkout"""
    
    from users.models import User
    
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    if not customer_id or not subscription_id:
        logger.error(f"Missing customer_id or subscription_id in webhook: {session}")
        return
    
    try:
        user = User.objects.get(stripe_customer_id=customer_id)
        
        # Get subscription details from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        price_id = subscription['items']['data'][0]['price']['id']
        
        # Find the plan
        plan = SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()
        if not plan:
            logger.warning(f"No plan found for price_id: {price_id}")
            return
        
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Lock the user record to prevent race conditions
            user = User.objects.select_for_update().get(id=user.id)
            
            # Update user tier
            user.subscription_tier = plan.tier
            user.subscription_status = 'active'
            user.save(update_fields=['subscription_tier', 'subscription_status'])
            
            # Convert Unix timestamps to timezone-aware datetime
            period_start = timezone.datetime.fromtimestamp(subscription['current_period_start'], tz=timezone.utc)
            period_end = timezone.datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc)
            
            # Create or update UserSubscription
            UserSubscription.objects.update_or_create(
                stripe_subscription_id=subscription_id,
                defaults={
                    'user': user,
                    'plan': plan,
                    'status': 'active',
                    'current_period_start': period_start,
                    'current_period_end': period_end,
                }
            )
            
        logger.info(f"Successfully activated subscription for user {user.id}")
        
    except User.DoesNotExist:
        logger.error(f"User not found for stripe_customer_id: {customer_id}")
    except Exception as e:
        logger.error(f"Error processing checkout completion: {str(e)}")


def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    
    try:
        with transaction.atomic():
            user_sub = UserSubscription.objects.select_for_update().get(
                stripe_subscription_id=subscription['id']
            )
            
            # Convert Unix timestamps to timezone-aware datetime
            period_start = timezone.datetime.fromtimestamp(subscription['current_period_start'], tz=timezone.utc)
            period_end = timezone.datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc)
            
            user_sub.status = subscription['status']
            user_sub.current_period_start = period_start
            user_sub.current_period_end = period_end
            user_sub.cancel_at_period_end = subscription.get('cancel_at_period_end', False)
            user_sub.save()
            
            # Update user status
            user_sub.user.subscription_status = subscription['status']
            user_sub.user.save(update_fields=['subscription_status'])
            
        logger.info(f"Updated subscription {subscription['id']} to status {subscription['status']}")
        
    except UserSubscription.DoesNotExist:
        logger.warning(f"UserSubscription not found for stripe_subscription_id: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    
    try:
        with transaction.atomic():
            user_sub = UserSubscription.objects.select_for_update().get(
                stripe_subscription_id=subscription['id']
            )
            user_sub.status = 'canceled'
            user_sub.save(update_fields=['status'])
            
            # Downgrade user to free tier
            user = user_sub.user
            user.subscription_tier = 'free'
            user.subscription_status = 'inactive'
            user.save(update_fields=['subscription_tier', 'subscription_status'])
            
        logger.info(f"Canceled subscription {subscription['id']} for user {user.id}")
        
    except UserSubscription.DoesNotExist:
        logger.warning(f"UserSubscription not found for stripe_subscription_id: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error deleting subscription: {str(e)}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preview_subscription_change(request):
    """Preview proration amount for subscription change"""
    
    from users.models import User
    
    try:
        price_id = request.data.get('price_id')
        if not price_id:
            return Response(
                {'error': 'price_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate plan
        plan = SubscriptionPlan.objects.filter(
            stripe_price_id=price_id,
            is_active=True
        ).first()
        
        if not plan:
            return Response(
                {'error': 'Invalid or inactive subscription plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Check if user has active subscription
        active_subscription = UserSubscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).first()
        
        if not active_subscription:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if same plan
        if active_subscription.plan.stripe_price_id == price_id:
            return Response(
                {'error': 'You are already on this plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if downgrading to free
        if plan.tier == 'free':
            return Response(
                {'error': 'To downgrade to free tier, please cancel your subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get current subscription
            stripe_sub = stripe.Subscription.retrieve(active_subscription.stripe_subscription_id)
            
            # Preview the upcoming invoice with proration
            # Pass subscription as a top-level parameter, not inside subscription_details
            upcoming_invoice = stripe.Invoice.create_preview(
                customer=user.stripe_customer_id,
                subscription=active_subscription.stripe_subscription_id,
                subscription_details={
                    'items': [{
                        'id': stripe_sub['items']['data'][0].id,
                        'price': price_id,
                    }],
                    'proration_behavior': 'create_prorations',
                },
            )
            
            # Calculate proration amount
            proration_amount = 0
            for line in upcoming_invoice.get('lines', {}).get('data', []):
                if line.get('proration'):
                    proration_amount += line.get('amount', 0)
            
            # Convert from cents to dollars
            proration_amount_dollars = proration_amount / 100
            
            # Determine if upgrade or downgrade
            current_price = active_subscription.plan.price_per_month
            new_price = plan.price_per_month
            is_upgrade = new_price > current_price
            
            return Response({
                'current_plan': {
                    'name': active_subscription.plan.name,
                    'tier': active_subscription.plan.tier,
                    'price': float(current_price),
                },
                'new_plan': {
                    'name': plan.name,
                    'tier': plan.tier,
                    'price': float(new_price),
                },
                'proration': {
                    'amount': proration_amount_dollars,
                    'is_charge': proration_amount > 0,
                    'is_credit': proration_amount < 0,
                },
                'is_upgrade': is_upgrade,
                'period_end': active_subscription.current_period_end.isoformat(),
                'immediate_charge': proration_amount_dollars if proration_amount > 0 else 0,
                'credit_applied': abs(proration_amount_dollars) if proration_amount < 0 else 0,
            })
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error previewing change: {str(e)}")
            return Response(
                {'error': 'Failed to calculate proration. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error previewing subscription change: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_subscription_change(request):
    """Confirm and execute subscription change after preview"""
    
    from users.models import User
    
    try:
        price_id = request.data.get('price_id')
        if not price_id:
            return Response(
                {'error': 'price_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate plan
        plan = SubscriptionPlan.objects.filter(
            stripe_price_id=price_id,
            is_active=True
        ).first()
        
        if not plan:
            return Response(
                {'error': 'Invalid or inactive subscription plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Check if user has active subscription
        active_subscription = UserSubscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).first()
        
        if not active_subscription:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Get the Stripe subscription
            stripe_sub = stripe.Subscription.retrieve(active_subscription.stripe_subscription_id)
            
            # Update Stripe subscription to new plan (fail-early)
            updated_sub = stripe.Subscription.modify(
                active_subscription.stripe_subscription_id,
                cancel_at_period_end=False,
                proration_behavior='create_prorations',
                items=[{
                    'id': stripe_sub['items']['data'][0].id,
                    'price': price_id,
                }]
            )
            
            # Only update DB if Stripe succeeded
            with transaction.atomic():
                # Lock records to prevent race conditions
                user_obj = User.objects.select_for_update().get(id=user.id)
                active_sub = UserSubscription.objects.select_for_update().get(id=active_subscription.id)
                
                # Update user tier
                user_obj.subscription_tier = plan.tier
                user_obj.subscription_status = updated_sub['status']
                user_obj.save(update_fields=['subscription_tier', 'subscription_status'])
                
                # Update subscription record
                period_start = timezone.datetime.fromtimestamp(updated_sub['current_period_start'], tz=timezone.utc)
                period_end = timezone.datetime.fromtimestamp(updated_sub['current_period_end'], tz=timezone.utc)
                
                active_sub.plan = plan
                active_sub.status = updated_sub['status']
                active_sub.current_period_start = period_start
                active_sub.current_period_end = period_end
                active_sub.save()
            
            logger.info(f"Successfully updated subscription for user {user.id} from {active_subscription.plan.tier} to {plan.tier}")
            
            return Response({
                'message': 'Subscription updated successfully',
                'new_tier': plan.tier,
            })
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error confirming change: {str(e)}")
            return Response(
                {'error': f'Failed to update subscription: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error confirming subscription change: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """Cancel user's active subscription immediately"""
    
    from users.models import User
    
    try:
        user = request.user
        
        # Use atomic transaction with locking to prevent race conditions
        with transaction.atomic():
            # Find and lock active subscription
            active_subscription = UserSubscription.objects.select_for_update().filter(
                user=user,
                status__in=['active', 'trialing']
            ).first()
            
            if not active_subscription:
                return Response(
                    {'error': 'No active subscription found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Store subscription ID before canceling
            stripe_subscription_id = active_subscription.stripe_subscription_id
            
            # Cancel in Stripe first (fail early if Stripe error)
            try:
                stripe.Subscription.delete(stripe_subscription_id)
            except stripe.InvalidRequestError as e:
                # Subscription might already be canceled in Stripe
                if 'No such subscription' in str(e):
                    logger.warning(f"Subscription {stripe_subscription_id} already deleted in Stripe")
                else:
                    raise
            except stripe.StripeError as e:
                logger.error(f"Stripe error canceling subscription: {str(e)}")
                return Response(
                    {'error': 'Failed to cancel subscription. Please try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update local records (within same transaction, locked)
            user_obj = User.objects.select_for_update().get(id=user.id)
            user_obj.subscription_tier = 'free'
            user_obj.subscription_status = 'inactive'
            user_obj.save(update_fields=['subscription_tier', 'subscription_status'])
            
            active_subscription.status = 'canceled'
            active_subscription.save(update_fields=['status'])
            
            logger.info(f"User {user.id} canceled subscription {stripe_subscription_id} immediately")
            
            return Response({
                'message': 'Subscription canceled successfully. Your account has been downgraded to the free plan.'
            })
            
    except stripe.StripeError as e:
        # Catch any Stripe errors not handled above
        logger.error(f"Unexpected Stripe error: {str(e)}")
        return Response(
            {'error': 'Failed to cancel subscription. Please try again.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        return Response(
            {'error': 'An error occurred. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handle_payment_failed(invoice):
    """Handle failed payment"""
    
    from users.models import User
    
    customer_id = invoice.get('customer')
    if not customer_id:
        logger.error(f"Missing customer_id in payment failed webhook: {invoice}")
        return
        
    try:
        user = User.objects.get(stripe_customer_id=customer_id)
        user.subscription_status = 'past_due'
        user.save(update_fields=['subscription_status'])
        logger.warning(f"Payment failed for user {user.id}, marked as past_due")
    except User.DoesNotExist:
        logger.error(f"User not found for stripe_customer_id: {customer_id}")
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")


