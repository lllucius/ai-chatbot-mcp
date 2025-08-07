/**
 * Documents client for file upload, processing, and management
 */

import { HttpClient } from '../http-client';
import { 
  Document,
  DocumentUpdate,
  ProcessingStatus,
  PaginatedResponse,
  BaseResponse
} from '../types';

export class DocumentsClient {
  constructor(private http: HttpClient) {}

  /**
   * Upload a document for processing
   */
  async upload(
    file: File | Blob,
    options: {
      title?: string;
      process_immediately?: boolean;
      metadata?: Record<string, any>;
    } = {}
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.title) {
      formData.append('title', options.title);
    }
    
    if (options.process_immediately !== undefined) {
      formData.append('process_immediately', options.process_immediately.toString());
    }
    
    if (options.metadata) {
      formData.append('metadata', JSON.stringify(options.metadata));
    }

    return this.http.upload<Document>('/api/v1/documents/upload', formData);
  }

  /**
   * List documents with filtering and pagination
   */
  async list(options: {
    page?: number;
    size?: number;
    file_type?: string;
    status?: string;
  } = {}): Promise<PaginatedResponse<Document>> {
    const params = new URLSearchParams();
    
    if (options.page) params.append('page', options.page.toString());
    if (options.size) params.append('size', options.size.toString());
    if (options.file_type) params.append('file_type', options.file_type);
    if (options.status) params.append('status', options.status);

    const query = params.toString();
    return this.http.get<PaginatedResponse<Document>>(
      `/api/v1/documents/${query ? '?' + query : ''}`
    );
  }

  /**
   * Get document by ID
   */
  async get(documentId: string): Promise<Document> {
    return this.http.get<Document>(`/api/v1/documents/byid/${documentId}`);
  }

  /**
   * Update document metadata
   */
  async update(documentId: string, data: DocumentUpdate): Promise<Document> {
    return this.http.put<Document>(`/api/v1/documents/byid/${documentId}`, data);
  }

  /**
   * Delete document
   */
  async delete(documentId: string): Promise<BaseResponse> {
    return this.http.delete<BaseResponse>(`/api/v1/documents/byid/${documentId}`);
  }

  /**
   * Get document processing status
   */
  async getStatus(documentId: string): Promise<ProcessingStatus> {
    return this.http.get<ProcessingStatus>(`/api/v1/documents/byid/${documentId}/status`);
  }

  /**
   * Reprocess document for chunk generation and embeddings
   */
  async reprocess(documentId: string): Promise<BaseResponse> {
    return this.http.post<BaseResponse>(`/api/v1/documents/byid/${documentId}/reprocess`);
  }

  /**
   * Download original document file
   */
  async download(documentId: string): Promise<Blob> {
    // Use raw client for binary downloads
    const response = await this.http.getRawClient().get(
      `/api/v1/documents/byid/${documentId}/download`,
      { responseType: 'blob' }
    );
    
    return response.data;
  }

  /**
   * Get document statistics
   */
  async getStats(): Promise<any> {
    return this.http.get('/api/v1/documents/stats');
  }

  /**
   * Cleanup old documents
   */
  async cleanup(options: {
    older_than_days?: number;
    status_filter?: string;
  } = {}): Promise<BaseResponse> {
    const params = new URLSearchParams();
    
    if (options.older_than_days) {
      params.append('older_than_days', options.older_than_days.toString());
    }
    if (options.status_filter) {
      params.append('status_filter', options.status_filter);
    }

    const query = params.toString();
    return this.http.post<BaseResponse>(
      `/api/v1/documents/cleanup${query ? '?' + query : ''}`
    );
  }

  /**
   * Bulk reprocess multiple documents
   */
  async bulkReprocess(documentIds: string[]): Promise<BaseResponse> {
    return this.http.post<BaseResponse>('/api/v1/documents/bulk-reprocess', {
      document_ids: documentIds
    });
  }

  /**
   * Get document processing queue status
   */
  async getProcessingQueue(): Promise<any> {
    return this.http.get('/api/v1/documents/processing-queue');
  }

  /**
   * Pause document processing
   */
  async pauseProcessing(): Promise<BaseResponse> {
    return this.http.post<BaseResponse>('/api/v1/documents/pause-processing');
  }

  /**
   * Resume document processing
   */
  async resumeProcessing(): Promise<BaseResponse> {
    return this.http.post<BaseResponse>('/api/v1/documents/resume-processing');
  }
}