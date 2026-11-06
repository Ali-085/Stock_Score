"""
Management command to create 100 dummy stock entries for testing
Usage: python manage.py create_dummy_stocks
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from stocks.models import Stock, StockCurrentScore, StockHistoricScore
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create 100 dummy stocks with current and historic scores for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating 100 dummy stocks...')
        
        # Popular tech/finance company names for realistic dummy data
        company_prefixes = [
            'Advanced', 'Global', 'United', 'American', 'Pacific', 'National', 'International',
            'Digital', 'Tech', 'Quantum', 'Cyber', 'Cloud', 'Data', 'Smart', 'Future',
            'Alpha', 'Beta', 'Gamma', 'Delta', 'Omega', 'Prime', 'Elite', 'Premium',
            'First', 'Central', 'Capital', 'Investment', 'Financial', 'Trading', 'Holdings'
        ]
        
        company_suffixes = [
            'Systems', 'Solutions', 'Technologies', 'Industries', 'Corporation', 'Group',
            'Enterprises', 'Holdings', 'Partners', 'Capital', 'Ventures', 'Labs', 'Dynamics',
            'Networks', 'Media', 'Financial', 'Bank', 'Insurance', 'Pharmaceuticals', 'Energy'
        ]
        
        exchanges = ['NYSE', 'NASDAQ', 'AMEX']
        
        created_count = 0
        
        for i in range(1, 101):
            # Generate stock symbol (3-4 letters)
            symbol = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.choice([3, 4])))
            
            # Skip if symbol already exists
            if Stock.objects.filter(symbol=symbol).exists():
                continue
            
            # Generate company name
            name = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)}"
            exchange = random.choice(exchanges)
            
            # Create stock
            stock = Stock.objects.create(
                symbol=symbol,
                name=name,
                exchange=exchange,
                is_active=True
            )
            
            # Create current score
            ml_rank = i  # Sequential rank for testing
            StockCurrentScore.objects.create(
                stock=stock,
                ml_rank=ml_rank,
                vol_rank=random.randint(1, 100),
                value_rank=random.randint(1, 100),
                risk_score=round(random.uniform(0, 100), 2),
                confidence_score=round(random.uniform(0.5, 1.0), 2),
                next_day_up_prob=round(random.uniform(30, 70), 2),
                next_week_up_prob=round(random.uniform(40, 60), 2)
            )
            
            # Create historic scores for last 30 days
            today = timezone.now().date()
            for days_ago in range(30):
                date = today - timedelta(days=days_ago)
                
                StockHistoricScore.objects.create(
                    stock=stock,
                    date=date,
                    ml_rank=random.randint(1, 100),
                    vol_rank=random.randint(1, 100),
                    value_rank=random.randint(1, 100),
                    risk_score=round(random.uniform(0, 100), 2),
                    confidence_score=round(random.uniform(0.5, 1.0), 2),
                    next_day_up_prob=round(random.uniform(30, 70), 2),
                    next_week_up_prob=round(random.uniform(40, 60), 2)
                )
            
            created_count += 1
            
            if created_count % 10 == 0:
                self.stdout.write(f'Created {created_count} stocks...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} stocks with current and 30-day historic scores'
            )
        )
