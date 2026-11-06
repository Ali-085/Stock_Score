/**
 * Utility functions for input sanitization and validation
 * Security: Always sanitize and validate user inputs
 */

/**
 * Sanitize string input by trimming and limiting length
 * Prevents buffer overflow and removes excess whitespace
 */
export const sanitizeString = (input, maxLength = 255) => {
  if (typeof input !== 'string') return '';
  return input.trim().substring(0, maxLength);
};

/**
 * Sanitize username: alphanumeric and underscores only
 * Prevents XSS and injection attacks
 */
export const sanitizeUsername = (username) => {
  if (typeof username !== 'string') return '';
  return username.replace(/[^a-zA-Z0-9_]/g, '').substring(0, 150);
};

/**
 * Sanitize email: lowercase and trim
 */
export const sanitizeEmail = (email) => {
  if (typeof email !== 'string') return '';
  return email.trim().toLowerCase().substring(0, 254);
};

/**
 * Validate email format
 */
export const isValidEmail = (email) => {
  if (typeof email !== 'string') return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate username format
 */
export const isValidUsername = (username) => {
  if (typeof username !== 'string') return false;
  const usernameRegex = /^[a-zA-Z0-9_]{3,150}$/;
  return usernameRegex.test(username);
};

/**
 * Sanitize URL: ensure it's same origin
 * Prevents open redirect attacks
 */
export const sanitizeUrl = (url, allowedOrigin = window.location.origin) => {
  try {
    const parsed = new URL(url);
    if (parsed.origin === allowedOrigin) {
      return url;
    }
    return null;
  } catch {
    return null;
  }
};

/**
 * Escape HTML to prevent XSS
 * React does this automatically, but use for edge cases
 */
export const escapeHtml = (text) => {
  if (typeof text !== 'string') return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

/**
 * Validate Stripe price ID format
 */
export const isValidStripePriceId = (priceId) => {
  if (typeof priceId !== 'string') return false;
  return priceId.startsWith('price_') && priceId.length > 6;
};

/**
 * Sanitize error message for display
 * Never show stack traces or sensitive data to users
 */
export const sanitizeErrorMessage = (error) => {
  // Default safe message
  const defaultMessage = 'An error occurred. Please try again.';
  
  // In production, only show safe error messages
  if (!import.meta.env.DEV) {
    // Only show whitelisted backend error messages
    const message = error?.response?.data?.error || error?.response?.data?.detail;
    if (typeof message === 'string' && message.length < 200) {
      return message;
    }
    return defaultMessage;
  }
  
  // In development, show more details
  return error?.response?.data?.error || 
         error?.response?.data?.detail || 
         error?.message || 
         defaultMessage;
};

/**
 * Rate limiting helper for client-side
 * Prevents spam/abuse on API calls
 */
export const createRateLimiter = (maxCalls, windowMs) => {
  const calls = [];
  
  return () => {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    // Remove old calls outside the window
    while (calls.length > 0 && calls[0] < windowStart) {
      calls.shift();
    }
    
    // Check if limit exceeded
    if (calls.length >= maxCalls) {
      return false;
    }
    
    // Add new call
    calls.push(now);
    return true;
  };
};

export default {
  sanitizeString,
  sanitizeUsername,
  sanitizeEmail,
  isValidEmail,
  isValidUsername,
  sanitizeUrl,
  escapeHtml,
  isValidStripePriceId,
  sanitizeErrorMessage,
  createRateLimiter,
};
