/**
 * Authentication Service
 * 
 * Handles all authentication-related API calls including login, register,
 * logout, and token management.
 */

import apiClient, { handleApiResponse, handleApiError, ApiResponse, ApiError } from './apiClient';
import { LoginRequest, RegisterRequest, Token, User } from '../types';

export class AuthService {
  /**
   * Login user with credentials
   */
  static async login(credentials: LoginRequest): Promise<ApiResponse<Token & { user: User }> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/auth/login', credentials);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Register new user
   */
  static async register(userData: RegisterRequest): Promise<ApiResponse<User> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/auth/register', userData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get current user info
   */
  static async getCurrentUser(): Promise<ApiResponse<User> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/auth/me');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Logout user
   */
  static async logout(): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/auth/logout');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Refresh authentication token
   */
  static async refreshToken(): Promise<ApiResponse<Token> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/auth/refresh');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Request password reset
   */
  static async requestPasswordReset(email: string): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/auth/password-reset', { email });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Confirm password reset
   */
  static async confirmPasswordReset(token: string, new_password: string): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/auth/password-reset/confirm', {
        token,
        new_password,
      });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }
}

export default AuthService;