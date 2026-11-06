# Stock Scoring Dashboard - Django Backend

Django REST Framework backend for a subscription-based stock scoring dashboard with JWT authentication and Stripe integration.

## Features

- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Stripe Integration**: Tiered subscription system (Free, Basic, Pro, Elite)
- **Subscription-Based Access Control**: Feature gating based on user subscription tier
- **Stock Scoring API**: Current and historical ML-based stock scores
- **User Watchlists**: Personal stock tracking
- **Webhook Support**: Real-time subscription status updates from Stripe

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (venv)

## Installation

1. **Clone the repository and navigate to backend folder**
   ```powershell
   cd backend
   ```

2. **Create and activate virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```powershell
   # Copy the example file
   copy .env.example .env
   
   # Edit .env with your actual values
   notepad .env
   ```

   **Required Configuration:**
   - `SECRET_KEY`: Generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
   - `STRIPE_SECRET_KEY`: From Stripe Dashboard > Developers > API keys
   - `STRIPE_PUBLISHABLE_KEY`: From Stripe Dashboard > Developers > API keys
   - `STRIPE_WEBHOOK_SECRET`: From Stripe Dashboard > Developers > Webhooks (after creating endpoint)

5. **Run migrations**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (admin)**
   ```powershell
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```powershell
   python manage.py runserver
   ```

   Server will start at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/token/` - Login (obtain JWT tokens)
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/me/` - Get current user info

### Subscriptions
- `GET /api/subscriptions/plans/` - List available subscription plans
- `GET /api/subscriptions/my-subscriptions/` - List user's subscriptions
- `POST /api/subscriptions/create-checkout-session/` - Create Stripe checkout
- `POST /api/subscriptions/webhook/` - Stripe webhook handler (for Stripe only)

### Stocks
- `GET /api/stocks/` - List all stocks
- `GET /api/stocks/current-scores/` - Get current stock scores (tier-based)
- `GET /api/stocks/historic-scores/` - Get historical scores (requires Basic+)
- `GET /api/stocks/watchlist/` - User's watchlist (CRUD operations)

## Subscription Tiers

| Tier | Current Scores | Historic Data | Premium Fields |
|------|----------------|---------------|----------------|
| Free | Top 10 stocks | ❌ | ❌ |
| Basic | Top 50 stocks | Last 30 days | ❌ |
| Pro | All stocks | Last 90 days | Limited |
| Elite | All stocks | Full history | ✅ |

## Setting Up Stripe Webhooks

1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Enter URL: `https://yourdomain.com/api/subscriptions/webhook/`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the webhook signing secret to `.env` as `STRIPE_WEBHOOK_SECRET`

## Admin Panel

Access Django admin at `http://localhost:8000/admin/`

Manage:
- Users and their subscription status
- Subscription plans
- Stock data
- User watchlists

## Security Features

- JWT token authentication with refresh tokens
- HTTPS enforcement in production
- CSRF protection
- CORS configuration
- SQL injection prevention (Django ORM)
- XSS protection
- Webhook signature verification
- Atomic transactions for payment processing
- Rate limiting ready (can be added with django-ratelimit)

## Production Deployment

1. **Set environment variables**
   ```
   DEBUG=False
   SECRET_KEY=<strong-random-key>
   ALLOWED_HOSTS=yourdomain.com
   ```

2. **Use PostgreSQL** (recommended)
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

3. **Collect static files**
   ```powershell
   python manage.py collectstatic
   ```

4. **Use a production WSGI server** (e.g., Gunicorn, uWSGI)
   ```powershell
   pip install gunicorn
   gunicorn config.wsgi:application
   ```

5. **Set up SSL/TLS certificate** (Let's Encrypt, Cloudflare, etc.)

6. **Configure reverse proxy** (Nginx, Apache)

## Development Notes

- SQLite is used by default for development
- CORS is configured for `localhost:5173` (Vite default)
- JWT access tokens expire after 15 minutes
- Refresh tokens expire after 7 days

## Troubleshooting

**Issue: Import errors**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Issue: Migration errors**
- Delete `db.sqlite3` and `*/migrations/` folders (except `__init__.py`)
- Run `python manage.py makemigrations` then `python manage.py migrate`

**Issue: Stripe webhook not working**
- Verify webhook secret matches `.env`
- Check webhook URL is publicly accessible
- Test with Stripe CLI: `stripe listen --forward-to localhost:8000/api/subscriptions/webhook/`

## License

Proprietary - All rights reserved
