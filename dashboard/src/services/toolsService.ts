/**
 * Tools Service
 * 
 * Handles all MCP tools-related API calls including
 * listing tools, testing tools, and managing tool servers.
 */

import apiClient, { handleApiResponse, handleApiError, ApiResponse, ApiError } from './apiClient';

export interface Tool {
  name: string;
  schema: any;
  enabled: boolean;
  server: string;
  description: string;
  parameters: any;
  last_used?: string;
  usage_count: number;
}

export interface ToolServer {
  name: string;
  url: string;
  status: 'connected' | 'error' | 'disconnected';
  last_check: string;
  response_time?: string;
  tool_count: number;
  error?: string;
}

export interface ToolsData {
  tools: Record<string, Tool>;
  openai_tools: any[];
  servers: Record<string, ToolServer>;
  total_tools: number;
  enabled_tools: number;
}

export class ToolsService {
  /**
   * List all available MCP tools
   */
  static async listTools(): Promise<ApiResponse<ToolsData> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/tools/');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get detailed information about a specific tool
   */
  static async getToolDetails(toolName: string): Promise<ApiResponse<Tool> | ApiError> {
    try {
      const response = await apiClient.get(`/api/v1/tools/${toolName}`);
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Test a tool with optional parameters
   */
  static async testTool(toolName: string, params?: any): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.post(`/api/v1/tools/${toolName}/test`, params || {});
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Refresh tool discovery
   */
  static async refreshTools(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.post('/api/v1/tools/refresh');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }

  /**
   * Get server status
   */
  static async getServerStatus(): Promise<ApiResponse<any> | ApiError> {
    try {
      const response = await apiClient.get('/api/v1/tools/servers/status');
      return handleApiResponse(response);
    } catch (error: any) {
      return handleApiError(error);
    }
  }
}