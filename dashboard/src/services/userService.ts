/**
 * User Service
 * 
 * Handles all user-related API calls including profile management,
 * user statistics, and admin user management.
 */

import apiClient, { handleApiResponse, handleApiError, ApiResponse, ApiError } from './apiClient';
import { User, UserUpdate, UserPasswordUpdate, PaginatedResponse } from '../types';

export class UserService {
  /**
   * Get current user profile with statistics
   */
  static async getMyProfile(): Promise<ApiResponse<User> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/users/me');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Update current user profile
   */
  static async updateMyProfile(userData: UserUpdate): Promise<ApiResponse<User> | ApiError> {
    try {
      const response = await apiClient.put('/api/v1/users/me', userData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Change current user password
   */
  static async changePassword(passwordData: UserPasswordUpdate): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/users/me/change-password', passwordData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get list of all users (admin only)
   */
  static async listUsers(params?: {
    page?: number;
    size?: number;
    active_only?: boolean;
    superuser_only?: boolean;
  }): Promise<ApiResponse<PaginatedResponse<User>> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/users/', { params });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get user by ID (admin only)
   */
  static async getUser(userId: string): Promise<ApiResponse<User> | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/users/${userId}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Update user by ID (admin only)
   */
  static async updateUser(userId: string, userData: UserUpdate): Promise<ApiResponse<User> | ApiError> {
    try {
      const response = await apiClient.put(`/api/v1/users/${userId}`, userData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Delete user by ID (admin only)
   */
  static async deleteUser(userId: string): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.delete(`/api/v1/users/${userId}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }
}

export default UserService;