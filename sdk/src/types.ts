/**
 * Type definitions for the AI Chatbot MCP API
 * 
 * These types correspond to the FastAPI backend models and ensure type safety
 * throughout the TypeScript SDK.
 */

// =============================================================================
// Base API Response Types
// =============================================================================

/**
 * Standard API response wrapper for all endpoints
 */
export interface ApiResponse<T = any> {
  /** Indicates if the operation was successful */
  success: boolean;
  /** The actual response data */
  data?: T;
  /** Error message if success is false */
  message?: string;
  /** Additional error details for debugging */
  error?: {
    code?: string;
    details?: Record<string, any>;
  };
  /** Request correlation ID for tracking */
  request_id?: string;
  /** Response timestamp */
  timestamp?: string;
}

/**
 * Pagination metadata for list endpoints
 */
export interface PaginationMeta {
  /** Current page number (1-based) */
  page: number;
  /** Number of items per page */
  per_page: number;
  /** Total number of items across all pages */
  total: number;
  /** Total number of pages */
  pages: number;
  /** Whether there's a next page */
  has_next: boolean;
  /** Whether there's a previous page */
  has_prev: boolean;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T = any> {
  /** Array of items for the current page */
  items: T[];
  /** Pagination metadata */
  pagination: PaginationMeta;
}

/**
 * Base response for simple operations
 */
export interface BaseResponse {
  /** Success status */
  success: boolean;
  /** Response message */
  message: string;
  /** Additional data if any */
  data?: Record<string, any>;
}

// =============================================================================
// Authentication & User Types
// =============================================================================

export interface User {
  /** User ID */
  id: string;
  /** Username */
  username: string;
  /** Email address */
  email: string;
  /** Full name */
  full_name?: string;
  /** Whether the user is active */
  is_active: boolean;
  /** Whether the user is a superuser */
  is_superuser: boolean;
  /** Account creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at?: string;
}

export interface UserCreate {
  /** Username */
  username: string;
  /** Email address */
  email: string;
  /** Password */
  password: string;
  /** Full name (optional) */
  full_name?: string;
}

export interface UserUpdate {
  /** Email address */
  email?: string;
  /** Full name */
  full_name?: string;
  /** Whether the user is active */
  is_active?: boolean;
  /** Whether the user is a superuser */
  is_superuser?: boolean;
}

export interface UserPasswordUpdate {
  /** Current password */
  current_password: string;
  /** New password */
  new_password: string;
}

export interface LoginRequest {
  /** Username or email */
  username: string;
  /** Password */
  password: string;
}

export interface Token {
  /** JWT access token */
  access_token: string;
  /** Token type (usually "bearer") */
  token_type: string;
  /** Token expiration time in seconds */
  expires_in?: number;
}

export interface PasswordResetRequest {
  /** Email address for password reset */
  email: string;
}

export interface PasswordResetConfirm {
  /** Reset token */
  token: string;
  /** New password */
  new_password: string;
}

// =============================================================================
// Conversation & Message Types
// =============================================================================

export interface Conversation {
  /** Conversation ID */
  id: string;
  /** Conversation title */
  title: string;
  /** User ID who owns this conversation */
  user_id: string;
  /** Whether the conversation is active */
  is_active: boolean;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
  /** Last message timestamp */
  last_message_at?: string;
  /** Total number of messages */
  message_count: number;
  /** Conversation metadata */
  metadata?: Record<string, any>;
}

export interface ConversationCreate {
  /** Conversation title */
  title: string;
  /** Optional metadata */
  metadata?: Record<string, any>;
}

export interface ConversationUpdate {
  /** New title */
  title?: string;
  /** Whether the conversation is active */
  is_active?: boolean;
  /** Updated metadata */
  metadata?: Record<string, any>;
}

export interface Message {
  /** Message ID */
  id: string;
  /** Conversation ID */
  conversation_id: string;
  /** Message content */
  content: string;
  /** Message role (user, assistant, system) */
  role: 'user' | 'assistant' | 'system';
  /** Message timestamp */
  created_at: string;
  /** Message metadata */
  metadata?: Record<string, any>;
  /** Token usage for this message */
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ChatRequest {
  /** Conversation ID (optional for new conversations) */
  conversation_id?: string;
  /** User message content */
  message: string;
  /** Conversation title (for new conversations) */
  conversation_title?: string;
  /** LLM profile to use */
  profile_name?: string;
  /** System prompt to use */
  prompt_name?: string;
  /** Whether to use RAG (document search) */
  use_rag?: boolean;
  /** Whether to enable tool calling */
  enable_tools?: boolean;
  /** Additional context or metadata */
  context?: Record<string, any>;
}

export interface ChatResponse {
  /** Response message */
  message: Message;
  /** Conversation information */
  conversation: Conversation;
  /** Token usage statistics */
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  /** Whether RAG was used */
  used_rag?: boolean;
  /** Tools that were called */
  tools_called?: string[];
  /** Response generation time in milliseconds */
  response_time_ms?: number;
}

// =============================================================================
// Document Types
// =============================================================================

export interface Document {
  /** Document ID */
  id: string;
  /** Original filename */
  filename: string;
  /** Document title */
  title: string;
  /** File type/extension */
  file_type: string;
  /** File size in bytes */
  file_size: number;
  /** Processing status */
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  /** Number of processed chunks */
  chunk_count: number;
  /** User ID who uploaded the document */
  user_id: string;
  /** Upload timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
  /** Processing completion timestamp */
  processed_at?: string;
  /** Error message if processing failed */
  error_message?: string;
  /** Document metadata */
  metadata?: Record<string, any>;
}

export interface DocumentUpload {
  /** File to upload */
  file: File | Blob;
  /** Optional title (defaults to filename) */
  title?: string;
  /** Whether to process immediately */
  process_immediately?: boolean;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

export interface DocumentUpdate {
  /** New title */
  title?: string;
  /** Updated metadata */
  metadata?: Record<string, any>;
}

export interface ProcessingStatus {
  /** Document ID */
  document_id: string;
  /** Current status */
  status: string;
  /** Processing progress (0-100) */
  progress: number;
  /** Number of chunks processed */
  chunks_processed: number;
  /** Total number of chunks */
  total_chunks: number;
  /** Error message if any */
  error_message?: string;
  /** Processing start time */
  started_at?: string;
  /** Processing completion time */
  completed_at?: string;
}

// =============================================================================
// Search Types
// =============================================================================

export interface SearchRequest {
  /** Search query */
  query: string;
  /** Search algorithm to use */
  algorithm?: 'vector' | 'bm25' | 'hybrid';
  /** Maximum number of results */
  limit?: number;
  /** Minimum similarity score */
  min_score?: number;
  /** Document type filter */
  document_type?: string;
  /** User filter */
  user_filter?: string;
  /** Additional filters */
  filters?: Record<string, any>;
}

export interface SearchResult {
  /** Chunk ID */
  chunk_id: number;
  /** Document ID */
  document_id: string;
  /** Document title */
  document_title: string;
  /** Chunk content */
  content: string;
  /** Relevance score */
  score: number;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  /** Search results */
  results: SearchResult[];
  /** Total number of results found */
  total_results: number;
  /** Query processing time in milliseconds */
  query_time_ms: number;
  /** Search algorithm used */
  algorithm_used: string;
}

// =============================================================================
// MCP (Model Context Protocol) Types
// =============================================================================

export interface McpServer {
  /** Server name */
  name: string;
  /** Server URL */
  url: string;
  /** Server description */
  description: string;
  /** Whether the server is enabled */
  enabled: boolean;
  /** Transport protocol */
  transport: string;
  /** Connection status */
  status: 'connected' | 'disconnected' | 'error';
  /** Last connection check */
  last_check?: string;
  /** Available tools count */
  tools_count?: number;
}

export interface McpTool {
  /** Tool name */
  name: string;
  /** Tool description */
  description: string;
  /** Server that provides this tool */
  server: string;
  /** Whether the tool is enabled */
  enabled: boolean;
  /** Tool schema */
  schema?: Record<string, any>;
}

// =============================================================================
// LLM Profile & Prompt Types
// =============================================================================

export interface LlmProfile {
  /** Profile name */
  name: string;
  /** Profile description */
  description: string;
  /** LLM model name */
  model: string;
  /** Model parameters */
  parameters: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    [key: string]: any;
  };
  /** Whether this is the default profile */
  is_default: boolean;
  /** Whether the profile is active */
  is_active: boolean;
  /** Creation timestamp */
  created_at: string;
}

export interface LlmProfileCreate {
  /** Profile name */
  name: string;
  /** Profile description */
  description: string;
  /** LLM model name */
  model: string;
  /** Model parameters */
  parameters: Record<string, any>;
  /** Whether this should be the default profile */
  is_default?: boolean;
}

export interface PromptTemplate {
  /** Prompt name */
  name: string;
  /** Prompt description */
  description: string;
  /** Prompt template content */
  template: string;
  /** Prompt category */
  category: string;
  /** Whether this is the default prompt */
  is_default: boolean;
  /** Whether the prompt is active */
  is_active: boolean;
  /** Template variables */
  variables?: string[];
  /** Creation timestamp */
  created_at: string;
}

export interface PromptCreate {
  /** Prompt name */
  name: string;
  /** Prompt description */
  description: string;
  /** Prompt template content */
  template: string;
  /** Prompt category */
  category: string;
  /** Whether this should be the default prompt */
  is_default?: boolean;
}

// =============================================================================
// Analytics & Statistics Types
// =============================================================================

export interface SystemMetrics {
  /** CPU usage percentage */
  cpu_usage: number;
  /** Memory usage in MB */
  memory_usage: number;
  /** Total memory in MB */
  memory_total: number;
  /** Disk usage percentage */
  disk_usage: number;
  /** Active connections count */
  active_connections: number;
  /** Database connection pool status */
  db_pool_status: {
    active: number;
    idle: number;
    total: number;
  };
}

export interface UsageAnalytics {
  /** Total number of users */
  total_users: number;
  /** Active users (last 30 days) */
  active_users: number;
  /** Total conversations */
  total_conversations: number;
  /** Total messages */
  total_messages: number;
  /** Total documents */
  total_documents: number;
  /** Messages per day (last 7 days) */
  messages_per_day: number[];
  /** Most used LLM profiles */
  popular_profiles: Array<{
    name: string;
    usage_count: number;
  }>;
}

export interface UserStats {
  /** Total registered users */
  total_users: number;
  /** Active users (last 30 days) */
  active_users_30d: number;
  /** New users (last 7 days) */
  new_users_7d: number;
  /** Superuser count */
  superuser_count: number;
}

// =============================================================================
// Health & System Types
// =============================================================================

export interface HealthStatus {
  /** Overall status */
  status: 'healthy' | 'degraded' | 'unhealthy';
  /** Status message */
  message: string;
  /** Timestamp */
  timestamp: string;
  /** Additional details */
  details?: Record<string, any>;
}

export interface DatabaseHealth {
  /** Database connection status */
  connected: boolean;
  /** Connection pool status */
  pool_status: {
    active: number;
    idle: number;
    total: number;
  };
  /** Response time in milliseconds */
  response_time_ms: number;
}

export interface ServicesHealth {
  /** External services status */
  services: Record<string, {
    status: 'healthy' | 'unhealthy';
    response_time_ms?: number;
    error?: string;
  }>;
}

// =============================================================================
// Error Types
// =============================================================================

/**
 * API Error class for handling HTTP errors
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public url: string,
    public response?: any
  ) {
    super(`HTTP ${status} ${statusText}: ${response?.message || 'API Error'}`);
    this.name = 'ApiError';
  }
}

/**
 * Configuration options for the SDK
 */
export interface SdkConfig {
  /** Base URL of the API */
  baseUrl: string;
  /** Authentication token */
  token?: string;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Custom headers */
  headers?: Record<string, string>;
  /** Error handler function */
  onError?: (error: ApiError) => void;
}