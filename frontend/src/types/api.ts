/**
 * Type definitions for the AI Chatbot API
 * 
 * This file contains comprehensive TypeScript types that correspond to the FastAPI backend
 * endpoints and data models. These types ensure type safety throughout the frontend
 * application and provide excellent developer experience with auto-completion.
 * 
 * The types are organized by functional area:
 * - Authentication and User Management
 * - Conversations and Messages
 * - Documents and File Processing
 * - Search and Vector Operations
 * - Analytics and Statistics
 * - MCP Tools and Server Management
 * - LLM Profiles and Prompts
 * - System Administration
 */

// =============================================================================
// Base API Response Types
// =============================================================================

/**
 * Standard API response wrapper for all endpoints
 * The backend consistently returns responses in this format
 */
export interface ApiResponse<T = any> {
  /** Indicates if the operation was successful */
  success: boolean;
  /** The actual response data */
  data?: T;
  /** Error message if success is false */
  message?: string;
  /** Additional error details for debugging */
  error?: string;
  /** Request correlation ID for tracking */
  request_id?: string;
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
  /** Whether there are more pages after current */
  has_next: boolean;
  /** Whether there are pages before current */
  has_prev: boolean;
}

/**
 * Generic paginated response wrapper
 */
export interface PaginatedResponse<T> {
  /** Array of items for current page */
  items: T[];
  /** Pagination metadata */
  pagination: PaginationMeta;
}

// =============================================================================
// Authentication and User Management Types
// =============================================================================

/**
 * User account information
 * Represents a user in the system with all profile details
 */
export interface User {
  /** Unique user identifier (integer) */
  id: string;
  /** Unique username for login */
  username: string;
  /** User's email address */
  email: string;
  /** User's full display name */
  full_name: string;
  /** Whether the account is active */
  is_active: boolean;
  /** Whether the user has admin privileges */
  is_superuser: boolean;
  /** Account creation timestamp */
  created_at: string;
  /** Last account modification timestamp */
  updated_at: string;
}

/**
 * Authentication token response
 * Returned after successful login
 */
export interface AuthToken {
  /** JWT access token for API requests */
  access_token: string;
  /** Token type (always "bearer") */
  token_type: string;
  /** Token expiration time in seconds */
  expires_in: number;
}

/**
 * User registration request payload
 */
export interface UserRegistration {
  /** Desired username (3-50 chars, alphanumeric + underscore/hyphen) */
  username: string;
  /** Valid email address */
  email: string;
  /** Strong password (min 8 chars with uppercase, lowercase, digit) */
  password: string;
  /** User's full name */
  full_name: string;
}

/**
 * User login request payload
 */
export interface UserLogin {
  /** Username or email */
  username: string;
  /** User's password */
  password: string;
}

// =============================================================================
// Conversation and Message Types
// =============================================================================

/**
 * Chat conversation container
 * Groups related messages together in a conversation thread
 */
export interface Conversation {
  /** Unique conversation identifier */
  id: string;
  /** Human-readable conversation title */
  title: string;
  /** ID of the user who owns this conversation */
  user_id: string;
  /** Whether the conversation is currently active */
  is_active: boolean;
  /** Conversation creation timestamp */
  created_at: string;
  /** Last conversation update timestamp */
  updated_at: string;
  /** Number of messages in this conversation */
  message_count?: number;
  /** Preview of the last message */
  last_message?: string;
}

/**
 * Individual chat message
 * Represents a single message within a conversation
 */
export interface Message {
  /** Unique message identifier */
  id: string;
  /** ID of the conversation this message belongs to */
  conversation_id: string;
  /** Message content/text */
  content: string;
  /** Whether this is a user message (true) or AI response (false) */
  is_user: boolean;
  /** Message creation timestamp */
  created_at: string;
  /** Token usage information for AI messages */
  token_usage?: TokenUsage;
  /** RAG context information if applicable */
  rag_context?: RagContext;
}

/**
 * Token usage tracking for AI responses
 * Helps monitor costs and optimize performance
 */
export interface TokenUsage {
  /** Tokens used in the prompt */
  prompt_tokens: number;
  /** Tokens generated in the response */
  completion_tokens: number;
  /** Total tokens used (prompt + completion) */
  total_tokens: number;
}

/**
 * RAG (Retrieval-Augmented Generation) context information
 * Provides transparency about which documents informed the AI response
 */
export interface RagContext {
  /** Number of documents retrieved */
  documents_retrieved: number;
  /** Sources used to generate the response */
  sources: DocumentSource[];
  /** Search query used for retrieval */
  search_query: string;
  /** Similarity threshold used */
  similarity_threshold: number;
}

/**
 * Document source reference for RAG
 */
export interface DocumentSource {
  /** Source document ID */
  document_id: string;
  /** Document title */
  document_title: string;
  /** Relevant text chunk */
  chunk_content: string;
  /** Similarity score (0-1) */
  similarity_score: number;
}

/**
 * Request payload for sending a chat message
 */
export interface ChatRequest {
  /** The user's message content */
  user_message: string;
  /** Optional conversation ID to continue existing conversation */
  conversation_id?: string;
  /** Whether to use RAG for document-aware responses */
  use_rag?: boolean;
  /** Optional LLM profile name to use */
  profile_name?: string;
  /** Optional prompt template name to use */
  prompt_name?: string;
  /** Override temperature setting (0-2) */
  temperature?: number;
  /** Override max tokens setting */
  max_tokens?: number;
  /** Override top_p setting (0-1) */
  top_p?: number;
}

// =============================================================================
// Document Management Types
// =============================================================================

/**
 * Uploaded document information
 * Represents a file uploaded to the system for processing
 */
export interface Document {
  /** Unique document identifier */
  id: string;
  /** Original filename */
  filename: string;
  /** Human-readable document title */
  title: string;
  /** MIME type of the file */
  content_type: string;
  /** File size in bytes */
  file_size: number;
  /** Current processing status */
  status: DocumentStatus;
  /** ID of the user who uploaded this document */
  user_id: string;
  /** Upload timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
  /** Processing completion timestamp */
  processed_at?: string;
  /** Number of text chunks extracted */
  chunk_count?: number;
  /** Error message if processing failed */
  error_message?: string;
  /** Processing progress percentage (0-100) */
  processing_progress?: number;
}

/**
 * Document processing status enumeration
 */
export type DocumentStatus = 
  | 'pending'     // Uploaded but not yet processed
  | 'processing'  // Currently being processed
  | 'completed'   // Successfully processed
  | 'failed'      // Processing failed
  | 'archived';   // Archived and not searchable

/**
 * Text chunk from processed document
 * Documents are split into chunks for vector embedding and search
 */
export interface DocumentChunk {
  /** Unique chunk identifier */
  id: string;
  /** ID of the parent document */
  document_id: string;
  /** Extracted text content */
  content: string;
  /** Chunk position in document (0-based) */
  chunk_index: number;
  /** Vector embedding for semantic search */
  embedding?: number[];
  /** Chunk creation timestamp */
  created_at: string;
}

/**
 * Document upload request
 */
export interface DocumentUpload {
  /** File to upload */
  file: File;
  /** Optional title (defaults to filename) */
  title?: string;
  /** Whether to start processing immediately */
  process_immediately?: boolean;
}

// =============================================================================
// Search and Vector Operation Types
// =============================================================================

/**
 * Search request parameters
 * Supports multiple search algorithms and configurations
 */
export interface SearchRequest {
  /** Search query text */
  query: string;
  /** Search algorithm to use */
  algorithm: SearchAlgorithm;
  /** Maximum number of results to return */
  limit?: number;
  /** Similarity threshold for vector search (0-1) */
  threshold?: number;
  /** Optional document IDs to limit search scope */
  document_ids?: string[];
  /** Whether to include chunk content in results */
  include_content?: boolean;
}

/**
 * Available search algorithms
 */
export type SearchAlgorithm = 
  | 'vector'     // Pure semantic similarity using embeddings
  | 'text'       // Traditional keyword-based full-text search
  | 'hybrid'     // Combines vector and text search with weighted scores
  | 'mmr';       // Maximum Marginal Relevance for diverse results

/**
 * Search result item
 */
export interface SearchResult {
  /** Source document information */
  document: Document;
  /** Matching text chunk */
  chunk: DocumentChunk;
  /** Relevance score (algorithm-dependent) */
  score: number;
  /** Search algorithm used */
  algorithm_used: SearchAlgorithm;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Complete search response
 */
export interface SearchResponse {
  /** Array of search results */
  results: SearchResult[];
  /** Total number of potential matches */
  total_matches: number;
  /** Search execution time in milliseconds */
  search_time_ms: number;
  /** Search parameters used */
  query_params: SearchRequest;
}

// =============================================================================
// Analytics and Statistics Types
// =============================================================================

/**
 * System overview statistics
 * High-level metrics for dashboard display
 */
export interface SystemStats {
  /** Total number of registered users */
  total_users: number;
  /** Number of active users (last 30 days) */
  active_users: number;
  /** Total number of conversations */
  total_conversations: number;
  /** Total number of messages sent */
  total_messages: number;
  /** Total number of uploaded documents */
  total_documents: number;
  /** Total number of processed document chunks */
  total_chunks: number;
  /** Total token usage across all conversations */
  total_tokens_used: number;
  /** Average response time in milliseconds */
  avg_response_time: number;
}

/**
 * Usage analytics over time
 * For creating charts and trend analysis
 */
export interface UsageAnalytics {
  /** Date for this data point (YYYY-MM-DD format) */
  date: string;
  /** Number of messages sent on this date */
  message_count: number;
  /** Number of unique users active on this date */
  active_users: number;
  /** Total tokens consumed on this date */
  tokens_used: number;
  /** Number of documents uploaded on this date */
  documents_uploaded: number;
  /** Average response time for this date */
  avg_response_time: number;
}

/**
 * User activity statistics
 */
export interface UserStats {
  /** User information */
  user: User;
  /** Number of conversations created */
  conversation_count: number;
  /** Total messages sent */
  message_count: number;
  /** Total tokens used */
  total_tokens: number;
  /** Number of documents uploaded */
  document_count: number;
  /** Last activity timestamp */
  last_active: string;
  /** Account age in days */
  account_age_days: number;
}

// =============================================================================
// MCP Tools and Server Management Types
// =============================================================================

/**
 * MCP (Model Context Protocol) server registration
 */
export interface McpServer {
  /** Unique server identifier */
  id: string;
  /** Human-readable server name */
  name: string;
  /** Server endpoint URL */
  url: string;
  /** Server description */
  description?: string;
  /** Whether the server is currently enabled */
  is_enabled: boolean;
  /** Server registration timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
  /** Connection status */
  status: 'connected' | 'disconnected' | 'error';
  /** Last successful connection timestamp */
  last_connected?: string;
}

/**
 * MCP tool definition
 */
export interface McpTool {
  /** Unique tool identifier */
  id: string;
  /** Tool name as defined by the MCP server */
  name: string;
  /** ID of the MCP server providing this tool */
  server_id: string;
  /** Tool description */
  description: string;
  /** Whether the tool is currently enabled */
  is_enabled: boolean;
  /** Tool usage count */
  usage_count: number;
  /** Last usage timestamp */
  last_used?: string;
  /** Tool parameters schema */
  parameters_schema?: Record<string, any>;
}

/**
 * Tool usage statistics
 */
export interface ToolUsageStats {
  /** Tool information */
  tool: McpTool;
  /** Number of times tool was used */
  usage_count: number;
  /** Average execution time in milliseconds */
  avg_execution_time: number;
  /** Success rate (0-1) */
  success_rate: number;
  /** Last usage timestamp */
  last_used?: string;
}

// =============================================================================
// LLM Profile and Prompt Management Types
// =============================================================================

/**
 * LLM parameter profile for consistent conversation behavior
 */
export interface LlmProfile {
  /** Unique profile identifier */
  id: string;
  /** Profile name (unique) */
  name: string;
  /** Human-readable title */
  title: string;
  /** Profile description */
  description?: string;
  /** LLM parameters */
  parameters: LlmParameters;
  /** Whether this is the default profile */
  is_default: boolean;
  /** Whether the profile is active */
  is_active: boolean;
  /** Usage count */
  usage_count: number;
  /** Profile creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * LLM generation parameters
 */
export interface LlmParameters {
  /** Model temperature (0-2, higher = more creative) */
  temperature: number;
  /** Maximum tokens to generate */
  max_tokens: number;
  /** Top-p nucleus sampling (0-1) */
  top_p: number;
  /** Frequency penalty (-2 to 2) */
  frequency_penalty?: number;
  /** Presence penalty (-2 to 2) */
  presence_penalty?: number;
  /** Stop sequences */
  stop?: string[];
}

/**
 * Prompt template for consistent AI behavior
 */
export interface PromptTemplate {
  /** Unique prompt identifier */
  id: string;
  /** Prompt name (unique) */
  name: string;
  /** Human-readable title */
  title: string;
  /** Prompt content with placeholder support */
  content: string;
  /** Prompt description */
  description?: string;
  /** Prompt category for organization */
  category: string;
  /** Tags for filtering and search */
  tags: string[];
  /** Whether this is the default prompt */
  is_default: boolean;
  /** Whether the prompt is active */
  is_active: boolean;
  /** Usage count */
  usage_count: number;
  /** Prompt creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

// =============================================================================
// System Administration Types
// =============================================================================

/**
 * System health check result
 */
export interface HealthCheck {
  /** Overall system status */
  status: 'healthy' | 'degraded' | 'unhealthy';
  /** Individual service checks */
  checks: Record<string, ServiceHealth>;
  /** System uptime in seconds */
  uptime: number;
  /** Health check timestamp */
  timestamp: string;
}

/**
 * Individual service health status
 */
export interface ServiceHealth {
  /** Service status */
  status: 'healthy' | 'degraded' | 'unhealthy';
  /** Response time in milliseconds */
  response_time?: number;
  /** Error message if unhealthy */
  error?: string;
  /** Additional service details */
  details?: Record<string, any>;
}

/**
 * Background task information
 */
export interface BackgroundTask {
  /** Task identifier */
  id: string;
  /** Task name/type */
  name: string;
  /** Current task status */
  status: 'pending' | 'running' | 'completed' | 'failed';
  /** Task progress (0-100) */
  progress: number;
  /** Task result if completed */
  result?: any;
  /** Error message if failed */
  error?: string;
  /** Task creation timestamp */
  created_at: string;
  /** Task start timestamp */
  started_at?: string;
  /** Task completion timestamp */
  completed_at?: string;
}

// =============================================================================
// API Request/Response Helpers
// =============================================================================

/**
 * Generic API error response
 */
export interface ApiError {
  /** Error message */
  message: string;
  /** HTTP status code */
  status_code: number;
  /** Error details */
  details?: Record<string, any>;
  /** Request correlation ID */
  request_id?: string;
}

/**
 * File upload progress callback type
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * API configuration options
 */
export interface ApiConfig {
  /** Base API URL */
  baseUrl: string;
  /** Default timeout in milliseconds */
  timeout: number;
  /** API version */
  version: string;
}