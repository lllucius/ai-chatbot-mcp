/**
 * Prompts client for prompt registry management
 */

import { HttpClient } from '../http-client';
import { PromptTemplate, PromptCreate, PaginatedResponse, BaseResponse } from '../types';

export class PromptsClient {
  constructor(private http: HttpClient) {}

  /**
   * List all prompts with optional filtering
   */
  async list(options: {
    active_only?: boolean;
    category?: string;
    search?: string;
  } = {}): Promise<PaginatedResponse<PromptTemplate>> {
    const params = new URLSearchParams();
    
    if (options.active_only !== undefined) params.append('active_only', options.active_only.toString());
    if (options.category) params.append('category', options.category);
    if (options.search) params.append('search', options.search);

    const query = params.toString();
    return this.http.get<PaginatedResponse<PromptTemplate>>(
      `/api/v1/prompts/${query ? '?' + query : ''}`
    );
  }

  /**
   * Get a specific prompt by name
   */
  async get(promptName: string): Promise<PromptTemplate> {
    return this.http.get<PromptTemplate>(`/api/v1/prompts/byname/${promptName}`);
  }

  /**
   * Create a new prompt
   */
  async create(data: PromptCreate): Promise<PromptTemplate> {
    return this.http.post<PromptTemplate>('/api/v1/prompts/', data);
  }

  /**
   * Update an existing prompt
   */
  async update(promptName: string, data: Partial<PromptCreate>): Promise<PromptTemplate> {
    return this.http.put<PromptTemplate>(`/api/v1/prompts/byname/${promptName}`, data);
  }

  /**
   * Delete a prompt
   */
  async delete(promptName: string): Promise<BaseResponse> {
    return this.http.delete<BaseResponse>(`/api/v1/prompts/byname/${promptName}`);
  }

  /**
   * Activate a prompt
   */
  async activate(promptName: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/prompts/byname/${promptName}/activate`);
  }

  /**
   * Deactivate a prompt
   */
  async deactivate(promptName: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/prompts/byname/${promptName}/deactivate`);
  }

  /**
   * Set a prompt as the default
   */
  async setDefault(promptName: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/prompts/byname/${promptName}/set-default`);
  }

  /**
   * Get prompt usage statistics
   */
  async getStats(): Promise<any> {
    return this.http.get('/api/v1/prompts/stats');
  }

  /**
   * Get prompt categories
   */
  async getCategories(): Promise<any> {
    return this.http.get('/api/v1/prompts/categories/');
  }

  /**
   * List active prompts (convenience method)
   */
  async listActive(): Promise<PaginatedResponse<PromptTemplate>> {
    return this.list({ active_only: true });
  }

  /**
   * Search prompts by category (convenience method)
   */
  async listByCategory(category: string): Promise<PaginatedResponse<PromptTemplate>> {
    return this.list({ category, active_only: true });
  }
}