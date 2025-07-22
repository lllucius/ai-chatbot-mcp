/**
 * Conversation Service
 * 
 * Handles all conversation and chat-related API calls including
 * conversation management, messaging, and chat functionality.
 */

import apiClient, { handleApiResponse, handleApiError, ApiResponse, ApiError } from './apiClient';
import { 
  Conversation, 
  ConversationCreate, 
  ConversationUpdate,
  Message,
  ChatRequest,
  ChatResponse,
  PaginatedResponse 
} from '../types';

export class ConversationService {
  /**
   * Create a new conversation
   */
  static async createConversation(conversationData: ConversationCreate): Promise<ApiResponse<Conversation> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/conversations/', conversationData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * List user's conversations
   */
  static async listConversations(params?: {
    page?: number;
    size?: number;
    active_only?: boolean;
  }): Promise<ApiResponse<PaginatedResponse<Conversation>> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/conversations/', { params });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get conversation by ID
   */
  static async getConversation(conversationId: string): Promise<ApiResponse<Conversation> | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/conversations/${conversationId}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Update conversation
   */
  static async updateConversation(
    conversationId: string, 
    updateData: ConversationUpdate
  ): Promise<ApiResponse<Conversation> | ApiError> {
    try {
      const response = await apiClient.put(`/api/v1/conversations/${conversationId}`, updateData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Delete conversation
   */
  static async deleteConversation(conversationId: string): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.delete(`/api/v1/conversations/${conversationId}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get messages in a conversation
   */
  static async getMessages(
    conversationId: string,
    params?: {
      page?: number;
      size?: number;
    }
  ): Promise<ApiResponse<PaginatedResponse<Message>> | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/conversations/${conversationId}/messages`, { params });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Send a chat message and get AI response
   */
  static async chat(chatRequest: ChatRequest): Promise<ApiResponse<ChatResponse> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/conversations/chat', chatRequest);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Stream chat response (for real-time messaging)
   */
  static async streamChat(chatRequest: ChatRequest): Promise<ApiResponse<ChatResponse> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/conversations/chat/stream', chatRequest);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get conversation statistics
   */
  static async getConversationStats(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/conversations/stats');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }
}

export default ConversationService;