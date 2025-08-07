/**
 * Profiles client for LLM profile registry management
 */

import { HttpClient } from '../http-client';
import { LlmProfile, LlmProfileCreate, PaginatedResponse, BaseResponse } from '../types';

export class ProfilesClient {
  constructor(private http: HttpClient) {}

  /**
   * List all LLM profiles with optional filtering
   */
  async list(options: {
    active_only?: boolean;
    search?: string;
  } = {}): Promise<PaginatedResponse<LlmProfile>> {
    const params = new URLSearchParams();
    
    if (options.active_only !== undefined) params.append('active_only', options.active_only.toString());
    if (options.search) params.append('search', options.search);

    const query = params.toString();
    return this.http.get<PaginatedResponse<LlmProfile>>(
      `/api/v1/profiles/${query ? '?' + query : ''}`
    );
  }

  /**
   * Get a specific LLM profile by name
   */
  async get(profileName: string): Promise<LlmProfile> {
    return this.http.get<LlmProfile>(`/api/v1/profiles/byname/${profileName}`);
  }

  /**
   * Create a new LLM profile
   */
  async create(data: LlmProfileCreate): Promise<LlmProfile> {
    return this.http.post<LlmProfile>('/api/v1/profiles/', data);
  }

  /**
   * Update an existing LLM profile
   */
  async update(profileName: string, data: Partial<LlmProfileCreate>): Promise<LlmProfile> {
    return this.http.put<LlmProfile>(`/api/v1/profiles/byname/${profileName}`, data);
  }

  /**
   * Delete an LLM profile
   */
  async delete(profileName: string): Promise<BaseResponse> {
    return this.http.delete<BaseResponse>(`/api/v1/profiles/byname/${profileName}`);
  }

  /**
   * Set a profile as the default
   */
  async setDefault(profileName: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/profiles/byname/${profileName}/set-default`);
  }

  /**
   * Activate a profile
   */
  async activate(profileName: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/profiles/byname/${profileName}/activate`);
  }

  /**
   * Deactivate a profile
   */
  async deactivate(profileName: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/profiles/byname/${profileName}/deactivate`);
  }

  /**
   * Get LLM profile usage statistics
   */
  async getStats(): Promise<any> {
    return this.http.get('/api/v1/profiles/stats');
  }

  /**
   * List active profiles (convenience method)
   */
  async listActive(): Promise<PaginatedResponse<LlmProfile>> {
    return this.list({ active_only: true });
  }

  /**
   * Get the default profile (convenience method)
   */
  async getDefault(): Promise<LlmProfile | null> {
    const profiles = await this.listActive();
    return profiles.items.find(p => p.is_default) || null;
  }
}