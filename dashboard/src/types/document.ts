import { BaseResponse, PaginatedResponse } from './common';

// Document related types
export interface Document {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  file_size: number;
  mime_type?: string;
  processing_status: string;
  owner_id: string;
  metainfo?: Record<string, any>;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentUpdate {
  title?: string;
  metainfo?: Record<string, any>;
}

export interface DocumentUploadResponse extends BaseResponse {
  document: Document;
  task_id?: string;
  auto_processing: boolean;
}

export interface DocumentChunk {
  id: string;
  content: string;
  chunk_index: number;
  start_char: number;
  end_char: number;
  token_count: number;
  document_id: string;
  document_title?: string;
  similarity_score?: number;
  metainfo?: Record<string, any>;
  created_at: string;
}

export interface ProcessingStatusResponse extends BaseResponse {
  document_id: string;
  status: string;
  chunk_count: number;
  processing_time?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  task_id?: string;
  task_status?: string;
  progress?: number;
  task_created_at?: string;
  task_started_at?: string;
  task_error?: string;
}

export interface DocumentSearchRequest {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  query?: string;
  algorithm?: 'vector' | 'text' | 'hybrid' | 'mmr';
  limit?: number;
  threshold?: number;
  filters?: Record<string, any>;
  document_ids?: string[];
  file_types?: string[];
}

export interface DocumentSearchResponse extends BaseResponse {
  results: DocumentChunk[];
  query: string;
  algorithm: string;
  total_results: number;
  search_time_ms: number;
}