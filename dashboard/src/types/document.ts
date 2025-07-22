import { BaseResponse } from './common';

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

export interface DocumentResponse extends Omit<BaseResponse, 'message'> {
  data: Document;
}

export interface DocumentListResponse extends BaseResponse {
  documents: Document[];
  total_count: number;
}

export interface DocumentUpload {
  file: File;
  title?: string;
  metainfo?: Record<string, any>;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  metadata?: Record<string, any>;
  embedding?: number[];
  created_at: string;
}

export interface DocumentSearchResult {
  document: Document;
  chunks: DocumentChunk[];
  relevance_score: number;
}