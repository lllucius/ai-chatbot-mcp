/**
 * Base HTTP client with authentication and error handling
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError, AxiosRequestConfig } from 'axios';
import { ApiError, ApiResponse, SdkConfig } from './types';

/**
 * HTTP client class that handles authentication, request/response interceptors,
 * and error handling for the AI Chatbot API.
 */
export class HttpClient {
  private client: AxiosInstance;
  private token?: string;
  private onError?: (error: ApiError) => void;

  constructor(config: SdkConfig) {
    this.token = config.token;
    this.onError = config.onError;

    // Create axios instance with default configuration
    this.client = axios.create({
      baseURL: config.baseUrl.replace(/\/$/, ''), // Remove trailing slash
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
    });

    // Setup request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Setup response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError = this.createApiError(error);
        if (this.onError) {
          this.onError(apiError);
        }
        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Set authentication token
   */
  setToken(token: string | null): void {
    this.token = token || undefined;
  }

  /**
   * Get current authentication token
   */
  getToken(): string | undefined {
    return this.token;
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.token = undefined;
  }

  /**
   * Make a GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return this.extractData(response);
  }

  /**
   * Make a POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return this.extractData(response);
  }

  /**
   * Make a PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return this.extractData(response);
  }

  /**
   * Make a PATCH request
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config);
    return this.extractData(response);
  }

  /**
   * Make a DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return this.extractData(response);
  }

  /**
   * Upload a file using multipart/form-data
   */
  async upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
    });
    return this.extractData(response);
  }

  /**
   * Make a streaming request for Server-Sent Events
   */
  async stream(url: string, data?: any, config?: AxiosRequestConfig): Promise<ReadableStream> {
    const response = await this.client.post(url, data, {
      ...config,
      responseType: 'stream',
      headers: {
        ...config?.headers,
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    });

    // For browser environments, return the response stream
    if (typeof window !== 'undefined') {
      return response.data;
    }

    // For Node.js environments, wrap the stream
    const stream = new ReadableStream({
      start(controller) {
        response.data.on('data', (chunk: Buffer) => {
          controller.enqueue(new Uint8Array(chunk));
        });

        response.data.on('end', () => {
          controller.close();
        });

        response.data.on('error', (error: Error) => {
          controller.error(error);
        });
      },
    });

    return stream;
  }

  /**
   * Get raw axios instance for advanced usage
   */
  getRawClient(): AxiosInstance {
    return this.client;
  }

  /**
   * Extract data from API response, handling both envelope and direct responses
   */
  private extractData<T>(response: AxiosResponse<ApiResponse<T> | T>): T {
    const data = response.data;

    // Check if response is in APIResponse envelope format
    if (data && typeof data === 'object' && 'success' in data) {
      const apiResponse = data as ApiResponse<T>;
      
      if (!apiResponse.success) {
        // API returned an error in the envelope
        const errorMessage = apiResponse.message || 'An error occurred';
        const errorDetails = apiResponse.error || {};
        
        throw new ApiError(
          response.status,
          response.statusText,
          response.config?.url || '',
          {
            message: errorMessage,
            error: errorDetails,
            timestamp: apiResponse.timestamp,
          }
        );
      }

      // Return the data from the envelope
      return apiResponse.data as T;
    }

    // Fallback to direct response data
    return data as T;
  }

  /**
   * Create a standardized ApiError from an AxiosError
   */
  private createApiError(error: AxiosError): ApiError {
    const status = error.response?.status || 0;
    const statusText = error.response?.statusText || 'Unknown Error';
    const url = error.config?.url || '';
    
    let responseData;
    try {
      responseData = error.response?.data;
    } catch {
      responseData = error.message;
    }

    return new ApiError(status, statusText, url, responseData);
  }
}