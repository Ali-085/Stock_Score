import api from './api';
import { isValidStripePriceId, sanitizeUrl } from '../utils/security';

export const subscriptionService = {
  // Get available plans
  async getPlans() {
    const response = await api.get('/subscriptions/plans/');
    return response.data;
  },

  // Get user's subscriptions
  async getMySubscriptions() {
    const response = await api.get('/subscriptions/my-subscriptions/');
    return response.data;
  },

  // Create Stripe Checkout Session (Stripe Hosted Checkout)
  async createCheckoutSession(priceId) {
    // Validate price ID format
    if (!isValidStripePriceId(priceId)) {
      throw new Error('Invalid Stripe price ID format');
    }
    
    // Backend controls redirect URLs - no need to send them
    const response = await api.post('/subscriptions/create-checkout-session/', {
      price_id: priceId,
    });
    return response.data; // { sessionId, url }
  },

  // Cancel subscription
  async cancelSubscription() {
    const response = await api.post('/subscriptions/cancel-subscription/');
    return response.data;
  },

  // Preview subscription change (get proration amount)
  async previewSubscriptionChange(priceId) {
    if (!isValidStripePriceId(priceId)) {
      throw new Error('Invalid Stripe price ID format');
    }
    const response = await api.post('/subscriptions/preview-change/', {
      price_id: priceId,
    });
    return response.data;
  },

  // Confirm subscription change after preview
  async confirmSubscriptionChange(priceId) {
    if (!isValidStripePriceId(priceId)) {
      throw new Error('Invalid Stripe price ID format');
    }
    const response = await api.post('/subscriptions/confirm-change/', {
      price_id: priceId,
    });
    return response.data;
  },
};
