/**
 * API Service Layer for AI Chatbot Frontend
 * 
 * This module provides a comprehensive API service layer that handles all
 * communication with the FastAPI backend. It uses Axios for HTTP requests
 * and provides a clean, type-safe interface for all API operations.
 * 
 * Key Features:
 * - Automatic authentication token management
 * - Request/response interceptors for error handling
 * - Type-safe API methods with full TypeScript support
 * - Centralized error handling and logging
 * - Automatic token refresh handling
 * - Upload progress tracking for file operations
 * 
 * Organization:
 * - Base API client configuration
 * - Authentication and user management
 * - Conversation and messaging operations
 * - Document management and file uploads
 * - Search and vector operations
 * - Analytics and statistics
 * - MCP tools and server management
 * - LLM profiles and prompt management
 * - System administration
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import type {
  ApiResponse,
  PaginatedResponse,
  User,
  AuthToken,
  UserRegistration,
  UserLogin,
  Conversation,
  Message,
  ChatRequest,
  Document,
  DocumentUpload,
  SearchRequest,
  SearchResponse,
  SystemStats,
  UsageAnalytics,
  UserStats,
  McpServer,
  McpTool,
  ToolUsageStats,
  LlmProfile,
  PromptTemplate,
  HealthCheck,
  BackgroundTask,
  ApiError,
  UploadProgressCallback
} from '../types/api';

// =============================================================================
// API Configuration and Base Client Setup
// =============================================================================

/**
 * API configuration constants
 * These can be overridden via environment variables
 */
const API_CONFIG = {
  // Base URL for the FastAPI backend - defaults to development server
  baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  // Default request timeout in milliseconds
  timeout: 30000,
  // API version prefix
  apiVersion: 'v1'
};

/**
 * Main API client instance with interceptors
 * This is the core Axios instance used for all API requests
 */
class ApiClient {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    // Create the main Axios instance with base configuration
    this.client = axios.create({
      baseURL: `${API_CONFIG.baseUrl}/api/${API_CONFIG.apiVersion}`,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Set up request interceptor to add authentication token
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token to all requests if available
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        
        // Log outgoing requests in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
        }
        
        return config;
      },
      (error) => {
        console.error('❌ Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Set up response interceptor for error handling and logging
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log successful responses in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
        }
        return response;
      },
      (error: AxiosError) => {
        // Handle authentication errors
        if (error.response?.status === 401) {
          // Clear stored token and redirect to login
          this.clearAuthToken();
          window.location.href = '/login';
        }
        
        // Log errors for debugging
        console.error('❌ API Error:', {
          url: error.config?.url,
          method: error.config?.method,
          status: error.response?.status,
          data: error.response?.data,
        });
        
        return Promise.reject(this.formatError(error));
      }
    );

    // Try to restore authentication token from localStorage
    this.restoreAuthToken();
  }

  /**
   * Set authentication token for API requests
   * @param token - JWT token string
   */
  setAuthToken(token: string): void {
    this.authToken = token;
    // Persist token to localStorage for session restoration
    localStorage.setItem('auth_token', token);
  }

  /**
   * Clear authentication token and remove from storage
   */
  clearAuthToken(): void {
    this.authToken = null;
    localStorage.removeItem('auth_token');
  }

  /**
   * Restore authentication token from localStorage
   */
  private restoreAuthToken(): void {
    const stored = localStorage.getItem('auth_token');
    if (stored) {
      this.authToken = stored;
    }
  }

  /**
   * Format API errors into a consistent structure
   * @param error - Axios error object
   * @returns Formatted API error
   */
  private formatError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error status
      return {
        message: (error.response.data as any)?.message || 'Server error occurred',
        status_code: error.response.status,
        details: error.response.data as any,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        message: 'Network error - unable to reach server',
        status_code: 0,
      };
    } else {
      // Error in request configuration
      return {
        message: error.message || 'Unknown error occurred',
        status_code: 0,
      };
    }
  }

  /**
   * Get the underlying Axios instance for advanced usage
   */
  getClient(): AxiosInstance {
    return this.client;
  }
}

// Create singleton API client instance
const apiClient = new ApiClient();

// =============================================================================
// Authentication and User Management API
// =============================================================================

/**
 * Authentication service providing user login, registration, and profile management
 */
export const authApi = {
  /**
   * Register a new user account
   * @param userData - User registration information
   * @returns Promise with created user data
   */
  async register(userData: UserRegistration): Promise<User> {
    const response = await apiClient.getClient().post<ApiResponse<User>>('/auth/register', userData);
    return response.data.data!;
  },

  /**
   * Login with username/email and password
   * @param credentials - Login credentials
   * @returns Promise with authentication token
   */
  async login(credentials: UserLogin): Promise<AuthToken> {
    const response = await apiClient.getClient().post<AuthToken>('/auth/login', credentials);
    const token = response.data;
    
    // Store the token for future requests
    apiClient.setAuthToken(token.access_token);
    
    return token;
  },

  /**
   * Logout and clear authentication
   */
  async logout(): Promise<void> {
    // Clear the stored token
    apiClient.clearAuthToken();
    
    // Optional: call logout endpoint if implemented
    try {
      await apiClient.getClient().post('/auth/logout');
    } catch (error) {
      // Logout endpoint might not be implemented, ignore errors
      console.log('Logout endpoint not available or failed');
    }
  },

  /**
   * Get current user profile information
   * @returns Promise with current user data
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.getClient().get<ApiResponse<User>>('/auth/me');
    return response.data.data!;
  },

  /**
   * Update current user profile
   * @param updates - Partial user data to update
   * @returns Promise with updated user data
   */
  async updateProfile(updates: Partial<Pick<User, 'full_name' | 'email'>>): Promise<User> {
    const response = await apiClient.getClient().patch<ApiResponse<User>>('/auth/me', updates);
    return response.data.data!;
  },

  /**
   * Change user password
   * @param currentPassword - Current password for verification
   * @param newPassword - New password
   * @returns Promise that resolves when password is changed
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.getClient().post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};

// =============================================================================
// Conversation and Messaging API
// =============================================================================

/**
 * Conversation service for managing chat conversations and messages
 */
export const conversationApi = {
  /**
   * Get list of conversations for current user
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Promise with paginated conversations
   */
  async getConversations(page = 1, limit = 20): Promise<PaginatedResponse<Conversation>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<Conversation>>>(
      '/conversations/',
      { params: { page, limit } }
    );
    return response.data.data!;
  },

  /**
   * Get a specific conversation by ID
   * @param conversationId - Conversation ID
   * @returns Promise with conversation data
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await apiClient.getClient().get<ApiResponse<Conversation>>(
      `/conversations/${conversationId}`
    );
    return response.data.data!;
  },

  /**
   * Create a new conversation
   * @param title - Conversation title
   * @returns Promise with created conversation
   */
  async createConversation(title: string): Promise<Conversation> {
    const response = await apiClient.getClient().post<ApiResponse<Conversation>>('/conversations/', {
      title,
    });
    return response.data.data!;
  },

  /**
   * Update conversation metadata
   * @param conversationId - Conversation ID
   * @param updates - Updates to apply
   * @returns Promise with updated conversation
   */
  async updateConversation(
    conversationId: string,
    updates: Partial<Pick<Conversation, 'title' | 'is_active'>>
  ): Promise<Conversation> {
    const response = await apiClient.getClient().patch<ApiResponse<Conversation>>(
      `/conversations/${conversationId}`,
      updates
    );
    return response.data.data!;
  },

  /**
   * Delete a conversation and all its messages
   * @param conversationId - Conversation ID
   * @returns Promise that resolves when conversation is deleted
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.getClient().delete(`/conversations/${conversationId}`);
  },

  /**
   * Get messages for a conversation
   * @param conversationId - Conversation ID
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 50)
   * @returns Promise with paginated messages
   */
  async getMessages(conversationId: string, page = 1, limit = 50): Promise<PaginatedResponse<Message>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<Message>>>(
      `/conversations/${conversationId}/messages`,
      { params: { page, limit } }
    );
    return response.data.data!;
  },

  /**
   * Send a message and get AI response
   * @param chatRequest - Chat request with message and options
   * @returns Promise with AI response message
   */
  async sendMessage(chatRequest: ChatRequest): Promise<{ conversation: Conversation; message: Message }> {
    const response = await apiClient.getClient().post<ApiResponse<{ conversation: Conversation; message: Message }>>(
      '/conversations/chat',
      chatRequest
    );
    return response.data.data!;
  },

  /**
   * Search conversations by content
   * @param query - Search query
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Promise with matching conversations
   */
  async searchConversations(query: string, page = 1, limit = 20): Promise<PaginatedResponse<Conversation>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<Conversation>>>(
      '/conversations/search',
      { params: { query, page, limit } }
    );
    return response.data.data!;
  },
};

// =============================================================================
// Document Management API
// =============================================================================

/**
 * Document service for file upload, processing, and management
 */
export const documentApi = {
  /**
   * Get list of documents for current user
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Promise with paginated documents
   */
  async getDocuments(page = 1, limit = 20): Promise<PaginatedResponse<Document>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<Document>>>(
      '/documents/',
      { params: { page, limit } }
    );
    return response.data.data!;
  },

  /**
   * Get a specific document by ID
   * @param documentId - Document ID
   * @returns Promise with document data
   */
  async getDocument(documentId: string): Promise<Document> {
    const response = await apiClient.getClient().get<ApiResponse<Document>>(`/documents/${documentId}`);
    return response.data.data!;
  },

  /**
   * Upload a new document
   * @param upload - Document upload data
   * @param onProgress - Optional progress callback
   * @returns Promise with uploaded document
   */
  async uploadDocument(upload: DocumentUpload, onProgress?: UploadProgressCallback): Promise<Document> {
    const formData = new FormData();
    formData.append('file', upload.file);
    if (upload.title) {
      formData.append('title', upload.title);
    }
    if (upload.process_immediately !== undefined) {
      formData.append('process_immediately', upload.process_immediately.toString());
    }

    const response = await apiClient.getClient().post<ApiResponse<Document>>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress
        ? (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
            onProgress(progress);
          }
        : undefined,
    });

    return response.data.data!;
  },

  /**
   * Delete a document and all its chunks
   * @param documentId - Document ID
   * @returns Promise that resolves when document is deleted
   */
  async deleteDocument(documentId: string): Promise<void> {
    await apiClient.getClient().delete(`/documents/${documentId}`);
  },

  /**
   * Get document processing status
   * @param documentId - Document ID
   * @returns Promise with current document status
   */
  async getDocumentStatus(documentId: string): Promise<Document> {
    const response = await apiClient.getClient().get<ApiResponse<Document>>(
      `/documents/${documentId}/status`
    );
    return response.data.data!;
  },

  /**
   * Trigger document reprocessing
   * @param documentId - Document ID
   * @returns Promise that resolves when reprocessing starts
   */
  async reprocessDocument(documentId: string): Promise<void> {
    await apiClient.getClient().post(`/documents/${documentId}/reprocess`);
  },
};

// =============================================================================
// Search API
// =============================================================================

/**
 * Search service for document and content search operations
 */
export const searchApi = {
  /**
   * Search documents using various algorithms
   * @param searchRequest - Search parameters
   * @returns Promise with search results
   */
  async searchDocuments(searchRequest: SearchRequest): Promise<SearchResponse> {
    const response = await apiClient.getClient().post<ApiResponse<SearchResponse>>('/search/', searchRequest);
    return response.data.data!;
  },

  /**
   * Get search suggestions based on partial query
   * @param partialQuery - Partial search query
   * @param limit - Maximum number of suggestions (default: 5)
   * @returns Promise with suggested queries
   */
  async getSearchSuggestions(partialQuery: string, limit = 5): Promise<string[]> {
    const response = await apiClient.getClient().get<ApiResponse<string[]>>('/search/suggestions', {
      params: { query: partialQuery, limit },
    });
    return response.data.data!;
  },
};

// =============================================================================
// Analytics API
// =============================================================================

/**
 * Analytics service for system statistics and usage metrics
 */
export const analyticsApi = {
  /**
   * Get system overview statistics
   * @returns Promise with system stats
   */
  async getSystemStats(): Promise<SystemStats> {
    const response = await apiClient.getClient().get<ApiResponse<SystemStats>>('/analytics/overview');
    return response.data.data!;
  },

  /**
   * Get usage analytics over time period
   * @param days - Number of days to look back (default: 30)
   * @returns Promise with usage analytics
   */
  async getUsageAnalytics(days = 30): Promise<UsageAnalytics[]> {
    const response = await apiClient.getClient().get<ApiResponse<UsageAnalytics[]>>('/analytics/usage', {
      params: { period: `${days}d` },
    });
    return response.data.data!;
  },

  /**
   * Get user statistics
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Promise with paginated user stats
   */
  async getUserStats(page = 1, limit = 20): Promise<PaginatedResponse<UserStats>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<UserStats>>>(
      '/analytics/users',
      { params: { page, limit } }
    );
    return response.data.data!;
  },

  /**
   * Get performance metrics
   * @returns Promise with performance data
   */
  async getPerformanceMetrics(): Promise<any> {
    const response = await apiClient.getClient().get<ApiResponse<any>>('/analytics/performance');
    return response.data.data!;
  },
};

// =============================================================================
// MCP Tools and Server Management API
// =============================================================================

/**
 * MCP service for managing Model Context Protocol servers and tools
 */
export const mcpApi = {
  /**
   * Get list of MCP servers
   * @returns Promise with MCP servers
   */
  async getServers(): Promise<McpServer[]> {
    const response = await apiClient.getClient().get<ApiResponse<McpServer[]>>('/mcp/servers');
    return response.data.data!;
  },

  /**
   * Add a new MCP server
   * @param serverData - Server configuration
   * @returns Promise with created server
   */
  async addServer(serverData: Omit<McpServer, 'id' | 'created_at' | 'updated_at' | 'status' | 'last_connected'>): Promise<McpServer> {
    const response = await apiClient.getClient().post<ApiResponse<McpServer>>('/mcp/servers', serverData);
    return response.data.data!;
  },

  /**
   * Update MCP server configuration
   * @param serverId - Server ID
   * @param updates - Server updates
   * @returns Promise with updated server
   */
  async updateServer(serverId: string, updates: Partial<McpServer>): Promise<McpServer> {
    const response = await apiClient.getClient().patch<ApiResponse<McpServer>>(`/mcp/servers/${serverId}`, updates);
    return response.data.data!;
  },

  /**
   * Delete MCP server
   * @param serverId - Server ID
   * @returns Promise that resolves when server is deleted
   */
  async deleteServer(serverId: string): Promise<void> {
    await apiClient.getClient().delete(`/mcp/servers/${serverId}`);
  },

  /**
   * Get list of available tools
   * @returns Promise with MCP tools
   */
  async getTools(): Promise<McpTool[]> {
    const response = await apiClient.getClient().get<ApiResponse<McpTool[]>>('/tools/');
    return response.data.data!;
  },

  /**
   * Enable/disable a specific tool
   * @param toolId - Tool ID
   * @param enabled - Whether to enable the tool
   * @returns Promise with updated tool
   */
  async toggleTool(toolId: string, enabled: boolean): Promise<McpTool> {
    const endpoint = enabled ? 'enable' : 'disable';
    const response = await apiClient.getClient().post<ApiResponse<McpTool>>(`/tools/${toolId}/${endpoint}`);
    return response.data.data!;
  },

  /**
   * Get tool usage statistics
   * @returns Promise with tool usage stats
   */
  async getToolStats(): Promise<ToolUsageStats[]> {
    const response = await apiClient.getClient().get<ApiResponse<ToolUsageStats[]>>('/tools/stats');
    return response.data.data!;
  },
};

// =============================================================================
// LLM Profile Management API
// =============================================================================

/**
 * Profile service for managing LLM parameter profiles
 */
export const profileApi = {
  /**
   * Get list of LLM profiles
   * @returns Promise with LLM profiles
   */
  async getProfiles(): Promise<LlmProfile[]> {
    const response = await apiClient.getClient().get<ApiResponse<LlmProfile[]>>('/profiles/');
    return response.data.data!;
  },

  /**
   * Get a specific profile by name
   * @param profileName - Profile name
   * @returns Promise with profile data
   */
  async getProfile(profileName: string): Promise<LlmProfile> {
    const response = await apiClient.getClient().get<ApiResponse<LlmProfile>>(`/profiles/${profileName}`);
    return response.data.data!;
  },

  /**
   * Create a new LLM profile
   * @param profileData - Profile configuration
   * @returns Promise with created profile
   */
  async createProfile(profileData: Omit<LlmProfile, 'id' | 'created_at' | 'updated_at' | 'usage_count'>): Promise<LlmProfile> {
    const response = await apiClient.getClient().post<ApiResponse<LlmProfile>>('/profiles/', profileData);
    return response.data.data!;
  },

  /**
   * Update LLM profile
   * @param profileName - Profile name
   * @param updates - Profile updates
   * @returns Promise with updated profile
   */
  async updateProfile(profileName: string, updates: Partial<LlmProfile>): Promise<LlmProfile> {
    const response = await apiClient.getClient().patch<ApiResponse<LlmProfile>>(`/profiles/${profileName}`, updates);
    return response.data.data!;
  },

  /**
   * Delete LLM profile
   * @param profileName - Profile name
   * @returns Promise that resolves when profile is deleted
   */
  async deleteProfile(profileName: string): Promise<void> {
    await apiClient.getClient().delete(`/profiles/${profileName}`);
  },

  /**
   * Set default profile
   * @param profileName - Profile name
   * @returns Promise that resolves when default is set
   */
  async setDefaultProfile(profileName: string): Promise<void> {
    await apiClient.getClient().post(`/profiles/${profileName}/set-default`);
  },
};

// =============================================================================
// Prompt Management API
// =============================================================================

/**
 * Prompt service for managing prompt templates
 */
export const promptApi = {
  /**
   * Get list of prompt templates
   * @returns Promise with prompt templates
   */
  async getPrompts(): Promise<PromptTemplate[]> {
    const response = await apiClient.getClient().get<ApiResponse<PromptTemplate[]>>('/prompts/');
    return response.data.data!;
  },

  /**
   * Get a specific prompt by name
   * @param promptName - Prompt name
   * @returns Promise with prompt data
   */
  async getPrompt(promptName: string): Promise<PromptTemplate> {
    const response = await apiClient.getClient().get<ApiResponse<PromptTemplate>>(`/prompts/${promptName}`);
    return response.data.data!;
  },

  /**
   * Create a new prompt template
   * @param promptData - Prompt configuration
   * @returns Promise with created prompt
   */
  async createPrompt(promptData: Omit<PromptTemplate, 'id' | 'created_at' | 'updated_at' | 'usage_count'>): Promise<PromptTemplate> {
    const response = await apiClient.getClient().post<ApiResponse<PromptTemplate>>('/prompts/', promptData);
    return response.data.data!;
  },

  /**
   * Update prompt template
   * @param promptName - Prompt name
   * @param updates - Prompt updates
   * @returns Promise with updated prompt
   */
  async updatePrompt(promptName: string, updates: Partial<PromptTemplate>): Promise<PromptTemplate> {
    const response = await apiClient.getClient().patch<ApiResponse<PromptTemplate>>(`/prompts/${promptName}`, updates);
    return response.data.data!;
  },

  /**
   * Delete prompt template
   * @param promptName - Prompt name
   * @returns Promise that resolves when prompt is deleted
   */
  async deletePrompt(promptName: string): Promise<void> {
    await apiClient.getClient().delete(`/prompts/${promptName}`);
  },

  /**
   * Set default prompt
   * @param promptName - Prompt name
   * @returns Promise that resolves when default is set
   */
  async setDefaultPrompt(promptName: string): Promise<void> {
    await apiClient.getClient().post(`/prompts/${promptName}/set-default`);
  },
};

// =============================================================================
// System Administration API
// =============================================================================

/**
 * Admin service for system administration and monitoring
 */
export const adminApi = {
  /**
   * Get system health status
   * @returns Promise with health check results
   */
  async getHealth(): Promise<HealthCheck> {
    const response = await apiClient.getClient().get<ApiResponse<HealthCheck>>('/health/detailed');
    return response.data.data!;
  },

  /**
   * Get list of background tasks
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Promise with paginated background tasks
   */
  async getBackgroundTasks(page = 1, limit = 20): Promise<PaginatedResponse<BackgroundTask>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<BackgroundTask>>>(
      '/tasks/',
      { params: { page, limit } }
    );
    return response.data.data!;
  },

  /**
   * Get all users (admin only)
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Promise with paginated users
   */
  async getAllUsers(page = 1, limit = 20): Promise<PaginatedResponse<User>> {
    const response = await apiClient.getClient().get<ApiResponse<PaginatedResponse<User>>>(
      '/users/',
      { params: { page, limit } }
    );
    return response.data.data!;
  },

  /**
   * Update user (admin only)
   * @param userId - User ID
   * @param updates - User updates
   * @returns Promise with updated user
   */
  async updateUser(userId: string, updates: Partial<User>): Promise<User> {
    const response = await apiClient.getClient().patch<ApiResponse<User>>(`/users/${userId}`, updates);
    return response.data.data!;
  },

  /**
   * Delete user (admin only)
   * @param userId - User ID
   * @returns Promise that resolves when user is deleted
   */
  async deleteUser(userId: string): Promise<void> {
    await apiClient.getClient().delete(`/users/${userId}`);
  },
};

// =============================================================================
// Export the API client instance for advanced usage
// =============================================================================

/**
 * Export the underlying API client for direct access when needed
 * This allows consumers to make custom requests not covered by the service methods
 */
export { apiClient };