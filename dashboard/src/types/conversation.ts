import { BaseResponse } from './common';

// Conversation and messaging types
export type ToolHandlingMode = 'none' | 'auto' | 'manual';

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
  output: string;
  error?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
  tool_calls?: ToolCall[];
  tool_call_results?: ToolCallResult[];
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  is_active: boolean;
  metainfo?: Record<string, any>;
  message_count: number;
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

export interface MessageCreate {
  content: string;
  role?: 'user';
  metadata?: Record<string, any>;
  tool_handling_mode?: ToolHandlingMode;
}

export interface ConversationResponse extends Omit<BaseResponse, 'message'> {
  data: Conversation;
}

export interface ConversationListResponse extends BaseResponse {
  conversations: Conversation[];
  total_count: number;
}

export interface MessageResponse extends Omit<BaseResponse, 'message'> {
  data: Message;
}

export interface MessageListResponse extends BaseResponse {
  messages: Message[];
  total_count: number;
}

export interface ChatResponse extends Omit<BaseResponse, 'message'> {
  conversation: Conversation;
  user_message: Message;
  assistant_message?: Message;
}