import api from './api';
import { sanitizeUsername, sanitizeEmail, isValidEmail, isValidUsername } from '../utils/security';

export const authService = {
  // Login - tokens stored in HttpOnly cookies automatically
  async login(username, password) {
    // Input validation
    if (!username || !password) {
      throw new Error('Username and password are required');
    }
    // Sanitize username
    const sanitizedUsername = sanitizeUsername(username);
    
    const response = await api.post('/auth/login/', {
      username: sanitizedUsername,
      password: password, // Don't modify password
    });
    return response.data;
  },

  // Register new user
  async register(userData) {
    // Input validation
    if (!userData.username || !userData.email || !userData.password) {
      throw new Error('Username, email, and password are required');
    }
    
    // Sanitize inputs
    const sanitizedUsername = sanitizeUsername(userData.username);
    const sanitizedEmail = sanitizeEmail(userData.email);
    
    // Validate username format
    if (!isValidUsername(sanitizedUsername)) {
      throw new Error('Username must be 3-150 characters and contain only letters, numbers, and underscores');
    }
    
    // Validate email format
    if (!isValidEmail(sanitizedEmail)) {
      throw new Error('Invalid email format');
    }
    
    const sanitizedData = {
      username: sanitizedUsername,
      email: sanitizedEmail,
      password: userData.password, // Don't modify password
      password2: userData.password2,
      first_name: (userData.first_name || '').trim().substring(0, 150),
      last_name: (userData.last_name || '').trim().substring(0, 150),
    };
    
    const response = await api.post('/auth/register/', sanitizedData);
    return response.data;
  },

  // Logout - clears cookies on backend
  async logout() {
    await api.post('/auth/logout/');
  },

  // Get current user info
  async getCurrentUser() {
    const response = await api.get('/auth/me/');
    return response.data;
  },

  // Refresh token (happens automatically in interceptor)
  async refreshToken() {
    await api.post('/auth/refresh/');
  },
};
