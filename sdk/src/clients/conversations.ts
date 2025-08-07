/**
 * Conversations client for chat and message management
 */

import { HttpClient } from '../http-client';
import { 
  Conversation,
  ConversationCreate,
  ConversationUpdate,
  Message,
  ChatRequest,
  ChatResponse,
  PaginatedResponse,
  BaseResponse,
  SearchResponse
} from '../types';

export class ConversationsClient {
  constructor(private http: HttpClient) {}

  /**
   * Create a new conversation
   */
  async create(data: ConversationCreate): Promise<Conversation> {
    return this.http.post<Conversation>('/api/v1/conversations/', data);
  }

  /**
   * List conversations with pagination and filtering
   */
  async list(options: {
    page?: number;
    size?: number;
    active_only?: boolean;
  } = {}): Promise<PaginatedResponse<Conversation>> {
    const params = new URLSearchParams();
    
    if (options.page) params.append('page', options.page.toString());
    if (options.size) params.append('size', options.size.toString());
    if (options.active_only !== undefined) params.append('active_only', options.active_only.toString());

    const query = params.toString();
    return this.http.get<PaginatedResponse<Conversation>>(
      `/api/v1/conversations/${query ? '?' + query : ''}`
    );
  }

  /**
   * Get conversation by ID
   */
  async get(conversationId: string): Promise<Conversation> {
    return this.http.get<Conversation>(`/api/v1/conversations/byid/${conversationId}`);
  }

  /**
   * Update conversation
   */
  async update(conversationId: string, data: ConversationUpdate): Promise<Conversation> {
    return this.http.put<Conversation>(`/api/v1/conversations/byid/${conversationId}`, data);
  }

  /**
   * Delete conversation
   */
  async delete(conversationId: string): Promise<BaseResponse> {
    return this.http.delete<BaseResponse>(`/api/v1/conversations/byid/${conversationId}`);
  }

  /**
   * Get messages from a conversation
   */
  async getMessages(conversationId: string, options: {
    page?: number;
    size?: number;
  } = {}): Promise<PaginatedResponse<Message>> {
    const params = new URLSearchParams();
    
    if (options.page) params.append('page', options.page.toString());
    if (options.size) params.append('size', options.size.toString());

    const query = params.toString();
    return this.http.get<PaginatedResponse<Message>>(
      `/api/v1/conversations/byid/${conversationId}/messages${query ? '?' + query : ''}`
    );
  }

  /**
   * Send a chat message and get AI response
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.http.post<ChatResponse>('/api/v1/conversations/chat', request);
  }

  /**
   * Send a chat message with streaming response
   */
  async chatStream(request: ChatRequest): Promise<AsyncIterableIterator<string>> {
    const stream = await this.http.stream('/api/v1/conversations/chat/stream', request);
    
    return this.parseEventStream(stream);
  }

  /**
   * Search conversations and messages
   */
  async search(options: {
    query: string;
    search_messages?: boolean;
    user_filter?: string;
    date_from?: string;
    date_to?: string;
    active_only?: boolean;
    limit?: number;
  }): Promise<SearchResponse> {
    const params = new URLSearchParams();
    
    params.append('query', options.query);
    if (options.search_messages !== undefined) params.append('search_messages', options.search_messages.toString());
    if (options.user_filter) params.append('user_filter', options.user_filter);
    if (options.date_from) params.append('date_from', options.date_from);
    if (options.date_to) params.append('date_to', options.date_to);
    if (options.active_only !== undefined) params.append('active_only', options.active_only.toString());
    if (options.limit) params.append('limit', options.limit.toString());

    const query = params.toString();
    return this.http.get<SearchResponse>(
      `/api/v1/conversations/search${query ? '?' + query : ''}`
    );
  }

  /**
   * Get conversation statistics
   */
  async getStats(): Promise<any> {
    return this.http.get('/api/v1/conversations/stats');
  }

  /**
   * Get registry statistics (prompts, profiles, tools usage)
   */
  async getRegistryStats(): Promise<any> {
    return this.http.get('/api/v1/conversations/registry-stats');
  }

  /**
   * Export conversation to various formats
   */
  async export(conversationId: string, format: string = 'json'): Promise<any> {
    return this.http.get(`/api/v1/conversations/byid/${conversationId}/export?format=${format}`);
  }

  /**
   * Archive old conversations
   */
  async archive(olderThanDays?: number): Promise<BaseResponse> {
    const params = new URLSearchParams();
    if (olderThanDays) params.append('older_than_days', olderThanDays.toString());
    params.append('dry_run', 'false');

    const query = params.toString();
    return this.http.post<BaseResponse>(
      `/api/v1/conversations/archive${query ? '?' + query : ''}`
    );
  }

  /**
   * Parse Server-Sent Events stream for chat streaming
   */
  private async *parseEventStream(stream: ReadableStream): AsyncIterableIterator<string> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove "data: " prefix
            
            if (data.trim() === '[DONE]') {
              return;
            }
            
            if (data.trim()) {
              yield data;
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}