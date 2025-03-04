// src/contexts/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import {
  signInApi,
  signUpApi,
  logoutApi,
} from '../mockApi';

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
    const response = await signInApi(email, password);
    setLoading(false);

    if (response.success) {
      setUser(response.user);
      setToken(response.token);
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const signUp = async (email, password) => {
    setLoading(true);
    const response = await signUpApi(email, password);
    setLoading(false);

    if (response.success) {
      setUser(response.user);
      setToken(response.token);
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const logout = async () => {
    setLoading(true);
    await logoutApi();
    setLoading(false);
    setUser(null);
    setToken(null);
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