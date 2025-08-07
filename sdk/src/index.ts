/**
 * Main AI Chatbot MCP SDK class
 * 
 * This is the main entry point for the TypeScript SDK, providing access to all
 * API functionality through organized client modules.
 */

import { HttpClient } from './http-client';
import { SdkConfig } from './types';

// Import all client modules
import { AuthClient } from './clients/auth';
import { UsersClient } from './clients/users';
import { ConversationsClient } from './clients/conversations';
import { DocumentsClient } from './clients/documents';
import { SearchClient } from './clients/search';
import { McpClient } from './clients/mcp';
import { HealthClient } from './clients/health';
import { AnalyticsClient } from './clients/analytics';
import { PromptsClient } from './clients/prompts';
import { ProfilesClient } from './clients/profiles';

/**
 * Main SDK class providing access to all AI Chatbot MCP API functionality
 * 
 * @example
 * ```typescript
 * // Initialize the SDK
 * const sdk = new AiChatbotSdk({
 *   baseUrl: 'https://api.example.com',
 *   timeout: 30000
 * });
 * 
 * // Authenticate
 * const token = await sdk.auth.login({ username: 'user', password: 'pass' });
 * 
 * // Create a conversation
 * const conversation = await sdk.conversations.create({ title: 'My Chat' });
 * 
 * // Send a message
 * const response = await sdk.conversations.chat({
 *   conversation_id: conversation.id,
 *   message: 'Hello!'
 * });
 * 
 * // Upload a document
 * const document = await sdk.documents.upload(file, { title: 'My Document' });
 * 
 * // Search documents
 * const searchResults = await sdk.search.search({
 *   query: 'machine learning',
 *   limit: 10
 * });
 * ```
 */
export class AiChatbotSdk {
  private httpClient: HttpClient;

  // Client modules
  public readonly auth: AuthClient;
  public readonly users: UsersClient;
  public readonly conversations: ConversationsClient;
  public readonly documents: DocumentsClient;
  public readonly search: SearchClient;
  public readonly mcp: McpClient;
  public readonly health: HealthClient;
  public readonly analytics: AnalyticsClient;
  public readonly prompts: PromptsClient;
  public readonly profiles: ProfilesClient;

  /**
   * Initialize the AI Chatbot SDK
   * 
   * @param config SDK configuration options
   */
  constructor(config: SdkConfig) {
    // Initialize HTTP client
    this.httpClient = new HttpClient(config);

    // Initialize all client modules
    this.auth = new AuthClient(this.httpClient);
    this.users = new UsersClient(this.httpClient);
    this.conversations = new ConversationsClient(this.httpClient);
    this.documents = new DocumentsClient(this.httpClient);
    this.search = new SearchClient(this.httpClient);
    this.mcp = new McpClient(this.httpClient);
    this.health = new HealthClient(this.httpClient);
    this.analytics = new AnalyticsClient(this.httpClient);
    this.prompts = new PromptsClient(this.httpClient);
    this.profiles = new ProfilesClient(this.httpClient);
  }

  /**
   * Set authentication token for all API requests
   */
  setToken(token: string): void {
    this.httpClient.setToken(token);
  }

  /**
   * Get current authentication token
   */
  getToken(): string | undefined {
    return this.httpClient.getToken();
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.httpClient.clearToken();
  }

  /**
   * Check if the SDK is currently authenticated
   */
  isAuthenticated(): boolean {
    return !!this.httpClient.getToken();
  }

  /**
   * Get raw HTTP client for advanced usage
   */
  getHttpClient(): HttpClient {
    return this.httpClient;
  }

  /**
   * Quick authentication helper
   * 
   * @param username Username or email
   * @param password Password
   * @returns Authentication token
   */
  async quickLogin(username: string, password: string) {
    return this.auth.loginWithCredentials(username, password);
  }

  /**
   * Quick health check
   * 
   * @returns Basic health status
   */
  async ping() {
    return this.health.basic();
  }

  /**
   * Get comprehensive system status
   */
  async getSystemStatus() {
    return this.health.comprehensive();
  }
}

// Re-export types for convenience
export * from './types';

// Re-export clients for advanced usage
export {
  AuthClient,
  UsersClient,
  ConversationsClient,
  DocumentsClient,
  SearchClient,
  McpClient,
  HealthClient,
  AnalyticsClient,
  PromptsClient,
  ProfilesClient,
};

// Default export
export default AiChatbotSdk;