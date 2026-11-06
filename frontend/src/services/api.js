import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance with credentials enabled (for HttpOnly cookies)
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // CRITICAL: Sends cookies with requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper to create cancellable requests
export const createCancellableRequest = () => {
  const controller = new AbortController();
  return {
    signal: controller.signal,
    cancel: () => controller.abort(),
  };
};

// Response interceptor to handle 401 errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Ignore cancelled requests
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    const originalRequest = error.config;

    // Don't try to refresh on auth endpoints (prevents infinite loop)
    const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || 
                          originalRequest.url?.includes('/auth/register') || 
                          originalRequest.url?.includes('/auth/refresh') ||
                          originalRequest.url?.includes('/auth/logout');

    // If 401 and not already retried and not an auth endpoint, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh token (cookie is sent automatically)
        await api.post('/auth/refresh/');
        
        // Retry original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login ONLY if not already on auth pages
        const currentPath = window.location.pathname;
        if (currentPath !== '/login' && currentPath !== '/register') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
