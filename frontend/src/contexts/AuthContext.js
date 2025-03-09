// src/contexts/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import { authApi } from '../api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setToken(storedToken);
    }
  }, []);

  useEffect(() => {
    if (user && token) {
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    }
  }, [user, token]);

  const signIn = async (email, password) => {
    setLoading(true);
    const response = await authApi.signIn(email, password);
    setLoading(false);

    if (response.success && response.user) {
      setUser(response.user);
      setToken(response.user.id ? response.user.id.toString() : null);
      return { success: true };
    } else {
      return { success: false, error: response.error || 'Sign in failed' };
    }
  };

  const signUp = async (email, password, fullName) => {
    setLoading(true);
    const response = await authApi.signUp(fullName, email, password);
    setLoading(false);

    if (response.success) {
      // After successful signup, redirect to sign in page
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const logout = async () => {
    setLoading(true);
    const response = await authApi.logout();
    setLoading(false);
    
    // Clear application state regardless of API response
    setUser(null);
    setToken(null);
    
    // Explicitly remove localStorage items
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('selectedConversationId');
    
    return response;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        signIn,
        signUp,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};