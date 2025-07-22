/**
 * Health Service
 * 
 * Handles all health and monitoring related API calls.
 */

import apiClient, { handleApiResponse, handleApiError, ApiResponse, ApiError } from './apiClient';

export class HealthService {
  /**
   * Basic health check
   */
  static async getHealth(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Detailed health check
   */
  static async getDetailedHealth(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/detailed');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Database health check
   */
  static async getDatabaseHealth(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/database');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Services health check
   */
  static async getServicesHealth(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/services');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * System metrics
   */
  static async getSystemMetrics(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/metrics');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Performance metrics
   */
  static async getPerformanceMetrics(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/performance');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Readiness check
   */
  static async getReadiness(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/readiness');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Liveness check
   */
  static async getLiveness(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/health/liveness');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }
}

export default HealthService;