/**
 * User management client for profile operations and user administration
 */

import { HttpClient } from '../http-client';
import { 
  User, 
  UserUpdate, 
  UserPasswordUpdate, 
  PaginatedResponse, 
  BaseResponse,
  UserStats
} from '../types';

export class UsersClient {
  constructor(private http: HttpClient) {}

  /**
   * Get current user's profile
   */
  async me(): Promise<User> {
    return this.http.get<User>('/api/v1/users/me');
  }

  /**
   * Update current user's profile
   */
  async updateMe(userData: UserUpdate): Promise<User> {
    return this.http.put<User>('/api/v1/users/me', userData);
  }

  /**
   * Change current user's password
   */
  async changePassword(passwordData: UserPasswordUpdate): Promise<BaseResponse> {
    return this.http.post<BaseResponse>('/api/v1/users/me/change-password', passwordData);
  }

  /**
   * List users with pagination and filtering
   */
  async list(options: {
    page?: number;
    size?: number;
    active_only?: boolean;
    superuser_only?: boolean;
  } = {}): Promise<PaginatedResponse<User>> {
    const params = new URLSearchParams();
    
    if (options.page) params.append('page', options.page.toString());
    if (options.size) params.append('size', options.size.toString());
    if (options.active_only !== undefined) params.append('active_only', options.active_only.toString());
    if (options.superuser_only !== undefined) params.append('superuser_only', options.superuser_only.toString());

    const query = params.toString();
    return this.http.get<PaginatedResponse<User>>(
      `/api/v1/users/${query ? '?' + query : ''}`
    );
  }

  /**
   * Get user by ID
   */
  async getById(userId: string): Promise<User> {
    return this.http.get<User>(`/api/v1/users/byid/${userId}`);
  }

  /**
   * Get user by username
   */
  async getByName(username: string): Promise<User> {
    return this.http.get<User>(`/api/v1/users/byname/${username}`);
  }

  /**
   * Update user by ID (admin operation)
   */
  async updateById(userId: string, userData: UserUpdate): Promise<User> {
    return this.http.put<User>(`/api/v1/users/byid/${userId}`, userData);
  }

  /**
   * Delete user by ID (admin operation)
   */
  async deleteById(userId: string): Promise<BaseResponse> {
    return this.http.delete<BaseResponse>(`/api/v1/users/byid/${userId}`);
  }

  /**
   * Get user statistics (admin operation)
   */
  async getStatistics(): Promise<UserStats> {
    return this.http.get<UserStats>('/api/v1/users/stats');
  }

  /**
   * Reset user password (admin operation)
   */
  async resetPassword(userId: string, newPassword?: string): Promise<BaseResponse> {
    const params: Record<string, string> = {};
    if (newPassword) {
      params.new_password = newPassword;
    }
    const query = new URLSearchParams(params).toString();
    
    return this.http.post<BaseResponse>(
      `/api/v1/users/byid/${userId}/reset-password${query ? '?' + query : ''}`
    );
  }

  /**
   * Activate user account (admin operation)
   */
  async activate(userId: string): Promise<User> {
    return this.updateById(userId, { is_active: true });
  }

  /**
   * Deactivate user account (admin operation)
   */
  async deactivate(userId: string): Promise<User> {
    return this.updateById(userId, { is_active: false });
  }

  /**
   * Promote user to superuser (admin operation)
   */
  async promote(userId: string): Promise<User> {
    return this.updateById(userId, { is_superuser: true });
  }

  /**
   * Demote user from superuser (admin operation)
   */
  async demote(userId: string): Promise<User> {
    return this.updateById(userId, { is_superuser: false });
  }
}