import axios from 'axios';

// Base URL for API requests
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // This allows cookies to be sent and received
});

// Add authorization token to requests if it exists
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication APIs
export const authApi = {
  signUp: async (fullName, email, password) => {
    try {
      const response = await apiClient.post('/signup', {
        full_name: fullName,
        email,
        password,
      });
      return {
        success: true,
        message: response.data.message,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Sign up failed',
      };
    }
  },

  signIn: async (email, password) => {
    try {
      const response = await apiClient.post('/signin', {
        email,
        password,
      });
      return {
        success: true,
        user: response.data.user,
        message: response.data.message,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Sign in failed',
      };
    }
  },

  logout: async () => {
    try {
      await apiClient.get('/logout');
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: 'Logout failed' };
    }
  },
};

export default apiClient; 