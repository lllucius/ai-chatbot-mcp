/**
 * SDK-based API service for the frontend
 * 
 * This service provides a clean interface between the React frontend and the 
 * AI Chatbot MCP TypeScript SDK. It handles initialization, configuration,
 * and provides convenient methods for React components.
 */

import { AiChatbotSdk, ApiError } from '@ai-chatbot-mcp/sdk';
import type {
  User,
  LoginRequest,
  Token,
  Conversation,
  ConversationCreate,
  Message,
  ChatRequest,
  ChatResponse,
  Document,
  SearchRequest,
  SearchResponse,
  PaginatedResponse,
  BaseResponse,
  McpServer,
  McpTool,
  LlmProfile,
  PromptTemplate,
  HealthStatus,
  UsageAnalytics
} from '@ai-chatbot-mcp/sdk';

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT = 30000; // 30 seconds

/**
 * Singleton SDK instance
 */
class SdkService {
  private sdk: AiChatbotSdk;
  private isInitialized = false;

  constructor() {
    this.sdk = new AiChatbotSdk({
      baseUrl: API_BASE_URL,
      timeout: REQUEST_TIMEOUT,
      onError: (error: ApiError) => {
        console.error('API Error:', {
          status: error.status,
          statusText: error.statusText,
          url: error.url,
          response: error.response
        });

        // Handle authentication errors globally
        if (error.status === 401) {
          this.clearAuth();
          // Redirect to login or show auth modal
          window.dispatchEvent(new CustomEvent('auth:required'));
        }
      }
    });

    // Try to restore token from localStorage
    this.restoreAuth();
    this.isInitialized = true;
  }

  /**
   * Get the SDK instance
   */
  getSdk(): AiChatbotSdk {
    return this.sdk;
  }

  /**
   * Check if SDK is ready to use
   */
  isReady(): boolean {
    return this.isInitialized;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.sdk.isAuthenticated();
  }

  /**
   * Store authentication token
   */
  private storeAuth(token: string): void {
    localStorage.setItem('auth_token', token);
    this.sdk.setToken(token);
  }

  /**
   * Restore authentication from storage
   */
  private restoreAuth(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.sdk.setToken(token);
    }
  }

  /**
   * Clear authentication
   */
  private clearAuth(): void {
    localStorage.removeItem('auth_token');
    this.sdk.clearToken();
  }

  // ==========================================================================
  // Authentication Methods
  // ==========================================================================

  async login(credentials: LoginRequest): Promise<Token> {
    const token = await this.sdk.auth.login(credentials);
    if (token.access_token) {
      this.storeAuth(token.access_token);
    }
    return token;
  }

  async logout(): Promise<BaseResponse> {
    try {
      const response = await this.sdk.auth.logout();
      this.clearAuth();
      return response;
    } catch (error) {
      // Clear local auth even if server logout fails
      this.clearAuth();
      throw error;
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.sdk.auth.me();
  }

  async refreshToken(): Promise<Token> {
    const token = await this.sdk.auth.refresh();
    if (token.access_token) {
      this.storeAuth(token.access_token);
    }
    return token;
  }

  // ==========================================================================
  // Conversation Methods
  // ==========================================================================

  async getConversations(page = 1, size = 20): Promise<PaginatedResponse<Conversation>> {
    return this.sdk.conversations.list({ page, size, active_only: true });
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    return this.sdk.conversations.get(conversationId);
  }

  async createConversation(data: ConversationCreate): Promise<Conversation> {
    return this.sdk.conversations.create(data);
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.sdk.conversations.chat(request);
  }

  async sendMessageStream(request: ChatRequest): Promise<AsyncIterableIterator<string>> {
    return this.sdk.conversations.chatStream(request);
  }

  async getMessages(conversationId: string, page = 1, size = 50): Promise<PaginatedResponse<Message>> {
    return this.sdk.conversations.getMessages(conversationId, { page, size });
  }

  async searchConversations(query: string, options: {
    search_messages?: boolean;
    limit?: number;
  } = {}): Promise<SearchResponse> {
    return this.sdk.conversations.search({
      query,
      search_messages: options.search_messages ?? true,
      limit: options.limit ?? 20,
      active_only: true
    });
  }

  async deleteConversation(conversationId: string): Promise<BaseResponse> {
    return this.sdk.conversations.delete(conversationId);
  }

  // ==========================================================================
  // Document Methods
  // ==========================================================================

  async uploadDocument(file: File, options: {
    title?: string;
    process_immediately?: boolean;
  } = {}): Promise<Document> {
    return this.sdk.documents.upload(file, {
      title: options.title,
      process_immediately: options.process_immediately ?? true
    });
  }

  async getDocuments(page = 1, size = 20, filters: {
    file_type?: string;
    status?: string;
  } = {}): Promise<PaginatedResponse<Document>> {
    return this.sdk.documents.list({ page, size, ...filters });
  }

  async getDocument(documentId: string): Promise<Document> {
    return this.sdk.documents.get(documentId);
  }

  async deleteDocument(documentId: string): Promise<BaseResponse> {
    return this.sdk.documents.delete(documentId);
  }

  async getDocumentStatus(documentId: string): Promise<any> {
    return this.sdk.documents.getStatus(documentId);
  }

  async downloadDocument(documentId: string): Promise<Blob> {
    return this.sdk.documents.download(documentId);
  }

  // ==========================================================================
  // Search Methods
  // ==========================================================================

  async searchDocuments(request: SearchRequest): Promise<SearchResponse> {
    return this.sdk.search.search(request);
  }

  async vectorSearch(query: string, limit = 20): Promise<SearchResponse> {
    return this.sdk.search.vectorSearch(query, limit);
  }

  async keywordSearch(query: string, limit = 20): Promise<SearchResponse> {
    return this.sdk.search.keywordSearch(query, limit);
  }

  async hybridSearch(query: string, limit = 20): Promise<SearchResponse> {
    return this.sdk.search.hybridSearch(query, limit);
  }

  // ==========================================================================
  // Health & System Methods
  // ==========================================================================

  async getHealth(): Promise<BaseResponse> {
    return this.sdk.health.basic();
  }

  async getDetailedHealth(): Promise<any> {
    return this.sdk.health.detailed();
  }

  async getSystemMetrics(): Promise<any> {
    return this.sdk.health.metrics();
  }

  async getSystemStatus(): Promise<any> {
    return this.sdk.health.comprehensive();
  }

  // ==========================================================================
  // Analytics Methods
  // ==========================================================================

  async getAnalyticsOverview(): Promise<any> {
    return this.sdk.analytics.getOverview();
  }

  async getUsageAnalytics(period?: string): Promise<UsageAnalytics> {
    return this.sdk.analytics.getUsage({ period });
  }

  async getPerformanceAnalytics(): Promise<any> {
    return this.sdk.analytics.getPerformance();
  }

  // ==========================================================================
  // MCP Methods
  // ==========================================================================

  async getMcpServers(): Promise<McpServer[]> {
    return this.sdk.mcp.listServers({ enabled_only: true });
  }

  async getMcpTools(): Promise<McpTool[]> {
    return this.sdk.mcp.listTools({ enabled_only: true });
  }

  async getMcpStats(): Promise<any> {
    return this.sdk.mcp.getStats();
  }

  // ==========================================================================
  // Profile & Prompt Methods
  // ==========================================================================

  async getLlmProfiles(): Promise<PaginatedResponse<LlmProfile>> {
    return this.sdk.profiles.list({ active_only: true });
  }

  async getPrompts(): Promise<PaginatedResponse<PromptTemplate>> {
    return this.sdk.prompts.list({ active_only: true });
  }

  async getPromptCategories(): Promise<any> {
    return this.sdk.prompts.getCategories();
  }

  // ==========================================================================
  // User Management
  // ==========================================================================

  async updateUserProfile(data: {
    email?: string;
    full_name?: string;
  }): Promise<User> {
    return this.sdk.users.updateMe(data);
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
  }): Promise<BaseResponse> {
    return this.sdk.users.changePassword(data);
  }
}

// Create singleton instance
const sdkService = new SdkService();

// Export the service instance and types
export default sdkService;

// Re-export types for convenience
export type {
  User,
  LoginRequest,
  Token,
  Conversation,
  ConversationCreate,
  Message,
  ChatRequest,
  ChatResponse,
  Document,
  SearchRequest,
  SearchResponse,
  PaginatedResponse,
  BaseResponse,
  McpServer,
  McpTool,
  LlmProfile,
  PromptTemplate,
  HealthStatus,
  UsageAnalytics,
  ApiError
};

// Export SDK class for direct access if needed
export { AiChatbotSdk };