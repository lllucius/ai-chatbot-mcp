/**
 * Document Service
 * 
 * Handles all document-related API calls including upload, processing,
 * search, and management.
 */

import apiClient, { handleApiResponse, handleApiError, ApiResponse, ApiError } from './apiClient';
import { 
  Document, 
  DocumentUpdate, 
  DocumentUploadResponse, 
  ProcessingStatusResponse,
  DocumentSearchRequest,
  DocumentSearchResponse,
  PaginatedResponse 
} from '../types';

export class DocumentService {
  /**
   * Upload a document
   */
  static async uploadDocument(
    file: File,
    title?: string,
    autoProcess?: boolean,
    priority?: number
  ): Promise<ApiResponse<DocumentUploadResponse> | ApiError> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (title) formData.append('title', title);
      if (autoProcess !== undefined) formData.append('auto_process', String(autoProcess));
      if (priority !== undefined) formData.append('priority', String(priority));

      const response = await apiClient.post('/api/v1/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * List user's documents
   */
  static async listDocuments(params?: {
    page?: number;
    size?: number;
    file_type?: string;
    status?: string;
  }): Promise<ApiResponse<PaginatedResponse<Document>> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/documents/', { params });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get document by ID
   */
  static async getDocument(documentId: string): Promise<ApiResponse<Document> | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/documents/${documentId}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Update document metadata
   */
  static async updateDocument(
    documentId: string, 
    updateData: DocumentUpdate
  ): Promise<ApiResponse<Document> | ApiError> {
    try {
      const response = await apiClient.put(`/api/v1/documents/${documentId}`, updateData);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Delete document
   */
  static async deleteDocument(documentId: string): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.delete(`/api/v1/documents/${documentId}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get document processing status
   */
  static async getProcessingStatus(documentId: string): Promise<ApiResponse<ProcessingStatusResponse> | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/documents/${documentId}/status`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Start document processing
   */
  static async startProcessing(documentId: string, priority?: number): Promise<ApiResponse | ApiError> {
    try {
      const params = priority ? { priority } : {};
      const response = await apiClient.post(`/api/v1/documents/${documentId}/process`, null, { params });
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Reprocess document
   */
  static async reprocessDocument(documentId: string): Promise<ApiResponse | ApiError> {
    try {
      const response = await apiClient.post(`/api/v1/documents/${documentId}/reprocess`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Download document
   */
  static async downloadDocument(documentId: string): Promise<Blob | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/documents/${documentId}/download`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Search documents
   */
  static async searchDocuments(searchRequest: DocumentSearchRequest): Promise<ApiResponse<DocumentSearchResponse> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/documents/search', searchRequest);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get processing configuration
   */
  static async getProcessingConfig(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/documents/processing-config');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get queue status
   */
  static async getQueueStatus(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/documents/queue-status');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }
}

export default DocumentService;