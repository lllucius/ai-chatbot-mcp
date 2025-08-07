/**
 * Authentication client for user registration, login, and token management
 */

import { HttpClient } from '../http-client';
import { 
  User, 
  UserCreate, 
  LoginRequest, 
  Token, 
  PasswordResetRequest, 
  PasswordResetConfirm,
  BaseResponse 
} from '../types';

export class AuthClient {
  constructor(private http: HttpClient) {}

  /**
   * Register a new user account
   */
  async register(userData: UserCreate): Promise<User> {
    return this.http.post<User>('/api/v1/auth/register', userData);
  }

  /**
   * Login with username/email and password
   */
  async login(credentials: LoginRequest): Promise<Token> {
    const token = await this.http.post<Token>('/api/v1/auth/login', credentials);
    
    // Automatically set the token for future requests
    if (token.access_token) {
      this.http.setToken(token.access_token);
    }
    
    return token;
  }

  /**
   * Login with username and password (convenience method)
   */
  async loginWithCredentials(username: string, password: string): Promise<Token> {
    return this.login({ username, password });
  }

  /**
   * Get current user profile
   */
  async me(): Promise<User> {
    return this.http.get<User>('/api/v1/users/me');
  }

  /**
   * Logout current user and invalidate token
   */
  async logout(): Promise<BaseResponse> {
    const response = await this.http.post<BaseResponse>('/api/v1/auth/logout');
    
    // Clear the token from the client
    this.http.clearToken();
    
    return response;
  }

  /**
   * Refresh authentication token
   */
  async refresh(): Promise<Token> {
    const token = await this.http.post<Token>('/api/v1/auth/refresh');
    
    // Update the token for future requests
    if (token.access_token) {
      this.http.setToken(token.access_token);
    }
    
    return token;
  }

  /**
   * Request password reset for a user
   */
  async requestPasswordReset(request: PasswordResetRequest): Promise<BaseResponse> {
    return this.http.post<BaseResponse>('/api/v1/users/password-reset', request);
  }

  /**
   * Confirm password reset with token
   */
  async confirmPasswordReset(confirmation: PasswordResetConfirm): Promise<BaseResponse> {
    return this.http.post<BaseResponse>('/api/v1/users/password-reset/confirm', confirmation);
  }

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated(): boolean {
    return !!this.http.getToken();
  }

  /**
   * Set authentication token manually
   */
  setToken(token: string): void {
    this.http.setToken(token);
  }

  /**
   * Get current authentication token
   */
  getToken(): string | undefined {
    return this.http.getToken();
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.http.clearToken();
  }
}