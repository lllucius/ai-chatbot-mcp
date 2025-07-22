import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Demo mode check
      if (token.startsWith('demo-token-')) {
        const username = token.includes('admin') ? 'admin' : 'demo';
        const demoUser = {
          id: 1,
          username: username,
          email: `${username}@example.com`,
          full_name: username === 'admin' ? 'Administrator' : 'Demo User',
          is_superuser: username === 'admin',
          is_active: true,
          created_at: new Date().toISOString(),
        };
        setUser(demoUser);
        setLoading(false);
        return;
      }
      
      // Verify token is still valid with real API
      axios.get('/api/v1/auth/me')
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    try {
      // Demo mode for showcase - remove in production
      if ((username === 'admin' && password === 'admin') || (username === 'demo' && password === 'demo')) {
        const demoUser = {
          id: 1,
          username: username,
          email: `${username}@example.com`,
          full_name: username === 'admin' ? 'Administrator' : 'Demo User',
          is_superuser: username === 'admin',
          is_active: true,
          created_at: new Date().toISOString(),
        };
        
        localStorage.setItem('token', 'demo-token-' + Date.now());
        setUser(demoUser);
        
        return { success: true };
      }

      // Send credentials as JSON instead of FormData
      const credentials = { username, password };

      const response = await axios.post('/api/v1/auth/login', credentials, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
