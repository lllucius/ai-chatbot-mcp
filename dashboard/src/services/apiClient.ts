/**
 * API Service Layer
 * 
 * This module provides a centralized API service layer for making HTTP requests
 * to the backend. It handles authentication, error handling, and response formatting.
 */

import axios, { AxiosResponse, AxiosError } from 'axios';

// Base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && !token.startsWith('demo-token-')) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login if unauthorized
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Generic API response wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  timestamp?: string;
}

// Generic API error
export interface ApiError {
  success: false;
  message: string;
  status?: number;
  details?: any;
}

// Helper function to handle API responses
export const handleApiResponse = <T>(response: AxiosResponse): ApiResponse<T> => {
  return {
    success: true,
    data: response.data,
    message: response.data?.message || 'Success',
    timestamp: new Date().toISOString(),
  };
};

// Helper function to handle API errors
export const handleApiError = (error: AxiosError): ApiError => {
  const message = (error.response?.data as any)?.detail || 
                 (error.response?.data as any)?.message || 
                 error.message || 
                 'An unexpected error occurred';
  
  return {
    success: false,
    message,
    status: error.response?.status,
    details: error.response?.data,
  };
};

export default apiClient;