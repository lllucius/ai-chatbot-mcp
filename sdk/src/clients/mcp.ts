/**
 * MCP (Model Context Protocol) client for server and tools management
 */

import { HttpClient } from '../http-client';
import { McpServer, McpTool, BaseResponse } from '../types';

export class McpClient {
  constructor(private http: HttpClient) {}

  // Server management methods

  /**
   * List all registered MCP servers
   */
  async listServers(options: {
    enabled_only?: boolean;
    connected_only?: boolean;
    detailed?: boolean;
  } = {}): Promise<McpServer[]> {
    const params = new URLSearchParams();
    
    if (options.enabled_only) params.append('enabled_only', 'true');
    if (options.connected_only) params.append('connected_only', 'true');
    if (options.detailed) params.append('detailed', 'true');

    const query = params.toString();
    return this.http.get<McpServer[]>(
      `/api/v1/mcp/servers${query ? '?' + query : ''}`
    );
  }

  /**
   * Add a new MCP server
   */
  async addServer(serverData: {
    name: string;
    url: string;
    description?: string;
    enabled?: boolean;
    transport?: string;
  }): Promise<McpServer> {
    return this.http.post<McpServer>('/api/v1/mcp/servers', {
      description: '',
      enabled: true,
      transport: 'http',
      ...serverData
    });
  }

  /**
   * Get details for a specific server
   */
  async getServer(serverName: string): Promise<McpServer> {
    return this.http.get<McpServer>(`/api/v1/mcp/servers/byname/${serverName}`);
  }

  /**
   * Update an MCP server
   */
  async updateServer(serverName: string, updates: Partial<McpServer>): Promise<McpServer> {
    return this.http.patch<McpServer>(`/api/v1/mcp/servers/byname/${serverName}`, updates);
  }

  /**
   * Remove an MCP server
   */
  async removeServer(serverName: string): Promise<BaseResponse> {
    return this.http.delete<BaseResponse>(`/api/v1/mcp/servers/byname/${serverName}`);
  }

  /**
   * Enable an MCP server
   */
  async enableServer(serverName: string): Promise<McpServer> {
    return this.updateServer(serverName, { enabled: true });
  }

  /**
   * Disable an MCP server
   */
  async disableServer(serverName: string): Promise<McpServer> {
    return this.updateServer(serverName, { enabled: false });
  }

  /**
   * Test connection to an MCP server
   */
  async testServer(serverName: string): Promise<any> {
    return this.http.post(`/api/v1/mcp/servers/byname/${serverName}/test`);
  }

  // Tools management methods

  /**
   * List all available MCP tools
   */
  async listTools(options: {
    server?: string;
    enabled_only?: boolean;
    detailed?: boolean;
  } = {}): Promise<McpTool[]> {
    const params = new URLSearchParams();
    
    if (options.server) params.append('server', options.server);
    if (options.enabled_only) params.append('enabled_only', 'true');
    if (options.detailed) params.append('detailed', 'true');

    const query = params.toString();
    return this.http.get<McpTool[]>(
      `/api/v1/mcp/tools${query ? '?' + query : ''}`
    );
  }

  /**
   * Get details for a specific tool
   */
  async getTool(toolName: string, server?: string): Promise<McpTool> {
    const params = new URLSearchParams();
    if (server) params.append('server', server);

    const query = params.toString();
    return this.http.get<McpTool>(
      `/api/v1/mcp/tools/byname/${toolName}${query ? '?' + query : ''}`
    );
  }

  /**
   * Enable an MCP tool
   */
  async enableTool(toolName: string, server?: string): Promise<any> {
    const params = new URLSearchParams();
    if (server) params.append('server', server);

    const query = params.toString();
    return this.http.patch(
      `/api/v1/mcp/tools/byname/${toolName}/enable${query ? '?' + query : ''}`
    );
  }

  /**
   * Disable an MCP tool
   */
  async disableTool(toolName: string, server?: string): Promise<any> {
    const params = new URLSearchParams();
    if (server) params.append('server', server);

    const query = params.toString();
    return this.http.patch(
      `/api/v1/mcp/tools/byname/${toolName}/disable${query ? '?' + query : ''}`
    );
  }

  /**
   * Test execution of an MCP tool
   */
  async testTool(toolName: string, testParams: Record<string, any> = {}): Promise<any> {
    return this.http.post(`/api/v1/mcp/tools/byname/${toolName}/test`, testParams);
  }

  /**
   * Get comprehensive status information for all MCP servers
   */
  async getServersStatus(): Promise<any> {
    return this.listServers({ detailed: true });
  }

  /**
   * Get MCP usage statistics
   */
  async getStats(): Promise<any> {
    return this.http.get('/api/v1/mcp/stats');
  }

  /**
   * Refresh MCP server connections and tool discovery
   */
  async refresh(server?: string): Promise<any> {
    const params = new URLSearchParams();
    if (server) params.append('server', server);

    const query = params.toString();
    return this.http.post(`/api/v1/mcp/refresh${query ? '?' + query : ''}`);
  }

  /**
   * Refresh all servers (convenience method)
   */
  async refreshAll(): Promise<any> {
    return this.refresh();
  }

  /**
   * Refresh specific server (convenience method)
   */
  async refreshServer(serverName: string): Promise<any> {
    return this.refresh(serverName);
  }
}