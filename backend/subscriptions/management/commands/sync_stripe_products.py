"""
Sync Stripe products to Django database
Run: python manage.py sync_stripe_products
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
from subscriptions.models import SubscriptionPlan

# Mapping of Stripe product names to Django tiers
TIER_MAPPING = {
    'Basic': 'basic',
    'Pro': 'pro',
    'Elite': 'elite',
}


class Command(BaseCommand):
    help = 'Sync Stripe products and prices to Django SubscriptionPlan model'

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        self.stdout.write('Fetching products from Stripe...')
        
        # Fetch all active products from Stripe
        products = stripe.Product.list(active=True, limit=100)
        
        synced_count = 0
        
        for product in products.auto_paging_iter():
            # Get the default price for this product
            if not product.default_price:
                self.stdout.write(
                    self.style.WARNING(f'Skipping {product.name} - no default price')
                )
                continue
            
            # Fetch price details
            price = stripe.Price.retrieve(product.default_price)
            
            # Skip if not recurring (one-time products)
            if price.type != 'recurring':
                self.stdout.write(
                    self.style.WARNING(f'Skipping {product.name} - not a subscription')
                )
                continue
            
            # Map product name to tier
            tier = TIER_MAPPING.get(product.name)
            if not tier:
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping {product.name} - not in TIER_MAPPING. '
                        f'Add it to sync_stripe_products.py'
                    )
                )
                continue
            
            # Calculate monthly price
            amount = price.unit_amount / 100  # Stripe uses cents
            
            # Convert to monthly if yearly
            if price.recurring.interval == 'year':
                monthly_price = amount / 12
            else:
                monthly_price = amount
            
            # Create or update in Django by stripe_price_id
            plan, created = SubscriptionPlan.objects.update_or_create(
                stripe_price_id=price.id,
                defaults={
                    'name': product.name,
                    'tier': tier,
                    'price_per_month': monthly_price,
                    'features': product.metadata or {},
                    'is_active': product.active,
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(
                    f'{action} {plan.name}: ${monthly_price:.2f}/mo (Price ID: {price.id})'
                )
            )
            synced_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully synced {synced_count} subscription plans!')
        )
