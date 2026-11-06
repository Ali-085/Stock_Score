/**
 * Centralized error handler for API calls
 * Provides consistent, secure error messages across the app
 */

export const handleApiError = (error, context = 'operation') => {
  // Development logging
  if (import.meta.env.DEV) {
    console.error(`${context} error:`, error);
  }

  // Handle different error types
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        return data?.detail || data?.error || 'Invalid request. Please check your input.';
      case 401:
        // Different message for login vs expired session
        if (context === 'login') {
          return 'Invalid username or password.';
        }
        return 'Your session has expired. Please login again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        // Sanitize error message - only show safe fields
        if (typeof data?.detail === 'string' && data.detail.length < 200) {
          return data.detail;
        }
        if (typeof data?.error === 'string' && data.error.length < 200) {
          return data.error;
        }
        return `Failed to ${context}. Please try again.`;
    }
  } else if (error.request) {
    return 'Network error. Please check your connection.';
  } else {
    return error.message || `An error occurred during ${context}.`;
  }
};

/**
 * Sanitize registration errors - only show whitelisted fields
 */
export const handleRegistrationError = (error) => {
  const errorData = error.response?.data;
  // Check for thrown string errors (from authService)
  if (typeof error === 'string') {
    if (error.toLowerCase().includes('username') && error.toLowerCase().includes('3')) {
      return 'Username must be at least 3 characters.';
    }
    return error;
  }
  // Check for thrown Error objects with message
  if (error instanceof Error && error.message) {
    if (error.message.toLowerCase().includes('username') && error.message.toLowerCase().includes('3')) {
      return 'Username must be at least 3 characters.';
    }
    return error.message;
  }
  if (errorData && typeof errorData === 'object') {
    // Whitelist known safe fields
    const safeFields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name'];
    const errorMessages = Object.entries(errorData)
      .filter(([key]) => safeFields.includes(key))
      .map(([key, value]) => {
        const msg = Array.isArray(value) ? value.join(', ') : value;
        // Special case: username too short
        if (key === 'username' && String(msg).toLowerCase().includes('3')) {
          return 'Username must be at least 3 characters.';
        }
        // Sanitize - only show first 200 chars
        return `${key}: ${String(msg).substring(0, 200)}`;
      })
      .join('\n');
    return errorMessages || 'Registration failed. Please check your input.';
  }
  return 'Registration failed. Please try again.';
};
