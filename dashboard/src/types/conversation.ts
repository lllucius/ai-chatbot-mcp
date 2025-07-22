import { BaseResponse, PaginatedResponse } from './common';

// Conversation and messaging types
export type ToolHandlingMode = 'return_results' | 'complete_with_results';

export interface ToolCall {
  id: string;
  function: {
    name: string;
    arguments: string;
  };
  type: 'function';
}

export interface ToolCallResult {
  tool_call_id: string;
  tool_name: string;
  success: boolean;
  content: any[];
  error?: string;
  provider?: string;
  execution_time_ms?: number;
}

export interface ToolCallSummary {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_execution_time_ms: number;
  results?: ToolCallResult[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  token_count: number;
  tool_calls?: Record<string, any>;
  tool_call_results?: Record<string, any>;
  metainfo?: Record<string, any>;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  is_active: boolean;
  message_count: number;
  metainfo?: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}

export interface ConversationCreate {
  title: string;
  is_active?: boolean;
  metainfo?: Record<string, any>;
}

export interface ConversationUpdate {
  title?: string;
  is_active?: boolean;
  metainfo?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  system_prompt?: string;
  conversation_title?: string;
  use_rag?: boolean;
  rag_filters?: Record<string, any>;
  tool_handling_mode?: ToolHandlingMode;
  enable_tools?: boolean;
  max_tokens?: number;
  temperature?: number;
}

export interface ChatResponse {
  success: boolean;
  message: Message;
  ai_message: Message;
  conversation: Conversation;
  rag_context?: any[];
  tool_calls_made?: any[];
  tool_call_summary?: ToolCallSummary;
  response_time_ms: number;
  timestamp?: string;
}