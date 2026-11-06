import React, { createContext, useState, useEffect, useContext, useMemo, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user on mount
  useEffect(() => {
    loadUser();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUser = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      setUser(null);
      
      // Log only in development
      if (import.meta.env.DEV) {
        console.error('Failed to load user:', error);
      }
      
      // In production, you could send to error tracking
      // e.g., Sentry.captureException(error);
    } finally {
      setLoading(false);
    }
  };

  const login = useCallback(async (username, password) => {
    await authService.login(username, password);
    await loadUser();
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const register = useCallback(async (userData) => {
    await authService.register(userData);
    // After registration, user needs to login
  }, []);

  const contextValue = useMemo(() => ({
    user,
    loading,
    login,
    logout,
    register,
    loadUser
  }), [user, loading, login, logout, register]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
