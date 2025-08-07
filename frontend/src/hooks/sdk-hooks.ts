/**
 * React Query hooks using the TypeScript SDK
 * 
 * This file provides React Query hooks that integrate with the AI Chatbot MCP TypeScript SDK.
 * These hooks provide efficient data fetching, caching, and state management for React components.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import sdkService, {
  type User,
  type LoginRequest,
  type Conversation,
  type ConversationCreate,
  type Message,
  type ChatRequest,
  type ChatResponse,
  type Document,
  type SearchRequest,
  type PaginatedResponse,
  type BaseResponse
} from '../services/sdk-service';

// =============================================================================
// Authentication Hooks
// =============================================================================

/**
 * Hook for user authentication/login
 */
export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => sdkService.login(credentials),
    onSuccess: () => {
      // Invalidate all queries on successful login to refresh data
      queryClient.invalidateQueries();
    },
  });
}

/**
 * Hook for user registration
 */
export function useRegister() {
  return useMutation({
    mutationFn: (userData: {
      username: string;
      email: string;
      password: string;
      full_name?: string;
    }) => sdkService.getSdk().auth.register(userData),
  });
}

/**
 * Hook for user logout
 */
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => sdkService.logout(),
    onSuccess: () => {
      // Clear all cached data on logout
      queryClient.clear();
    },
  });
}

/**
 * Hook to get current user information
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: ['user', 'current'],
    queryFn: () => sdkService.getCurrentUser(),
    enabled: sdkService.isAuthenticated(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on auth errors
      if (error?.status === 401) return false;
      return failureCount < 3;
    },
  });
}

// =============================================================================
// Conversation Hooks
// =============================================================================

/**
 * Hook to get conversations list
 */
export function useConversations(page = 1, size = 20) {
  return useQuery({
    queryKey: ['conversations', { page, size }],
    queryFn: () => sdkService.getConversations(page, size),
    enabled: sdkService.isAuthenticated(),
  });
}

/**
 * Hook to get a specific conversation
 */
export function useConversation(conversationId: string) {
  return useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => sdkService.getConversation(conversationId),
    enabled: !!conversationId && sdkService.isAuthenticated(),
  });
}

/**
 * Hook to get messages for a conversation
 */
export function useMessages(conversationId: string, page = 1, size = 50) {
  return useQuery({
    queryKey: ['messages', conversationId, { page, size }],
    queryFn: () => sdkService.getMessages(conversationId, page, size),
    enabled: !!conversationId && sdkService.isAuthenticated(),
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ConversationCreate) => sdkService.createConversation(data),
    onSuccess: () => {
      // Invalidate conversations list to show the new conversation
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

/**
 * Hook to send a chat message
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ChatRequest) => sdkService.sendMessage(request),
    onSuccess: (data, variables) => {
      // Invalidate messages for the conversation
      queryClient.invalidateQueries({ 
        queryKey: ['messages', variables.conversation_id] 
      });
      // Also invalidate the conversation to update last message time
      queryClient.invalidateQueries({ 
        queryKey: ['conversation', variables.conversation_id] 
      });
    },
  });
}

/**
 * Hook to delete a conversation
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) => sdkService.deleteConversation(conversationId),
    onSuccess: () => {
      // Invalidate conversations list
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

/**
 * Hook to get messages for a conversation (alias)
 */
export function useConversationMessages(conversationId: string, page = 1, size = 50) {
  return useMessages(conversationId, page, size);
}

/**
 * Hook to update a conversation
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, data }: { 
      conversationId: string; 
      data: { title?: string; [key: string]: any } 
    }) => sdkService.getSdk().conversations.update(conversationId, data),
    onSuccess: (data, variables) => {
      // Invalidate the specific conversation
      queryClient.invalidateQueries({ 
        queryKey: ['conversation', variables.conversationId] 
      });
      // Also invalidate conversations list
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

// =============================================================================
// Document Hooks
// =============================================================================

/**
 * Hook to get documents list
 */
export function useDocuments(page = 1, size = 20, filters: {
  file_type?: string;
  status?: string;
} = {}) {
  return useQuery({
    queryKey: ['documents', { page, size, ...filters }],
    queryFn: () => sdkService.getDocuments(page, size, filters),
    enabled: sdkService.isAuthenticated(),
  });
}

/**
 * Hook to get a specific document
 */
export function useDocument(documentId: string) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: () => sdkService.getDocument(documentId),
    enabled: !!documentId && sdkService.isAuthenticated(),
  });
}

/**
 * Hook to upload a document
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, options }: {
      file: File;
      options?: { title?: string; process_immediately?: boolean };
    }) => sdkService.uploadDocument(file, options),
    onSuccess: () => {
      // Invalidate documents list to show the new document
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

/**
 * Hook to delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => sdkService.deleteDocument(documentId),
    onSuccess: () => {
      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

/**
 * Hook to reprocess a document
 */
export function useReprocessDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => sdkService.getSdk().documents.reprocess(documentId),
    onSuccess: () => {
      // Invalidate documents list and the specific document
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

/**
 * Hook to get document processing status
 */
export function useDocumentStatus(documentId: string) {
  return useQuery({
    queryKey: ['document', documentId, 'status'],
    queryFn: () => sdkService.getDocumentStatus(documentId),
    enabled: !!documentId && sdkService.isAuthenticated(),
    refetchInterval: (data) => {
      // Poll every 2 seconds if document is still processing
      const status = data?.data?.status;
      return status === 'processing' ? 2000 : false;
    },
  });
}

// =============================================================================
// Search Hooks
// =============================================================================

/**
 * Hook for document search
 */
export function useDocumentSearch() {
  return useMutation({
    mutationFn: (request: SearchRequest) => sdkService.searchDocuments(request),
  });
}

/**
 * Hook for conversation search
 */
export function useConversationSearch() {
  return useMutation({
    mutationFn: ({ query, options }: {
      query: string;
      options?: { search_messages?: boolean; limit?: number };
    }) => sdkService.searchConversations(query, options),
  });
}

// =============================================================================
// Health & System Hooks
// =============================================================================

/**
 * Hook to get system health status
 */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => sdkService.getHealth(),
    refetchInterval: 30000, // Check every 30 seconds
  });
}

/**
 * Hook to get detailed system status
 */
export function useSystemStatus() {
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: () => sdkService.getSystemStatus(),
    refetchInterval: 60000, // Check every minute
  });
}

/**
 * Hook to get system metrics
 */
export function useSystemMetrics() {
  return useQuery({
    queryKey: ['system', 'metrics'],
    queryFn: () => sdkService.getSystemMetrics(),
    refetchInterval: 10000, // Update every 10 seconds
  });
}

/**
 * Hook to get detailed system health status
 */
export function useSystemHealth() {
  return useQuery({
    queryKey: ['system', 'health'],
    queryFn: () => sdkService.getDetailedHealth(),
    refetchInterval: 30000, // Check every 30 seconds
  });
}

/**
 * Hook to get system statistics
 */
export function useSystemStats() {
  return useQuery({
    queryKey: ['system', 'stats'],
    queryFn: () => sdkService.getAnalyticsOverview(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// =============================================================================
// Analytics Hooks
// =============================================================================

/**
 * Hook to get analytics overview
 */
export function useAnalyticsOverview() {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: () => sdkService.getAnalyticsOverview(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to get usage analytics
 */
export function useUsageAnalytics(period?: string) {
  return useQuery({
    queryKey: ['analytics', 'usage', period],
    queryFn: () => sdkService.getUsageAnalytics(period),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to get user statistics
 */
export function useUserStats(page = 1, size = 20) {
  return useQuery({
    queryKey: ['analytics', 'users', { page, size }],
    queryFn: () => sdkService.getAnalyticsOverview(), // Fallback to overview for now
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to get performance metrics
 */
export function usePerformanceMetrics() {
  return useQuery({
    queryKey: ['analytics', 'performance'],
    queryFn: () => sdkService.getPerformanceAnalytics(),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

//==========================================================================
// MCP Hooks
// =============================================================================

/**
 * Hook to get MCP servers
 */
export function useMcpServers() {
  return useQuery({
    queryKey: ['mcp', 'servers'],
    queryFn: () => sdkService.getMcpServers(),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook to get MCP tools
 */
export function useMcpTools() {
  return useQuery({
    queryKey: ['mcp', 'tools'],
    queryFn: () => sdkService.getMcpTools(),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook to get MCP statistics
 */
export function useMcpStats() {
  return useQuery({
    queryKey: ['mcp', 'stats'],
    queryFn: () => sdkService.getMcpStats(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to add MCP server
 */
export function useAddMcpServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serverData: {
      name: string;
      url: string;
      description?: string;
      enabled?: boolean;
      transport?: string;
    }) => sdkService.getSdk().mcp.addServer(serverData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp', 'servers'] });
    },
  });
}

/**
 * Hook to delete MCP server
 */
export function useDeleteMcpServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serverName: string) => sdkService.getSdk().mcp.removeServer(serverName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp', 'servers'] });
    },
  });
}

// =============================================================================
// Profile & Prompt Hooks
// =============================================================================

/**
 * Hook to get LLM profiles
 */
export function useLlmProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: () => sdkService.getLlmProfiles(),
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

/**
 * Hook to create LLM profile
 */
export function useCreateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      name: string;
      description: string;
      model: string;
      parameters: Record<string, any>;
      is_default?: boolean;
    }) => sdkService.getSdk().profiles.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}

/**
 * Hook to delete LLM profile
 */
export function useDeleteProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (profileName: string) => sdkService.getSdk().profiles.delete(profileName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}

/**
 * Hook to create LLM profile (alias)
 */
export function useCreateLlmProfile() {
  return useCreateProfile();
}

/**
 * Hook to update LLM profile
 */
export function useUpdateLlmProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ profileName, data }: { 
      profileName: string; 
      data: { name?: string; description?: string; model?: string; parameters?: Record<string, any> } 
    }) => sdkService.getSdk().profiles.update(profileName, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}

/**
 * Hook to delete LLM profile (alias)
 */
export function useDeleteLlmProfile() {
  return useDeleteProfile();
}

/**
 * Hook to set default LLM profile
 */
export function useSetDefaultLlmProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (profileName: string) => sdkService.getSdk().profiles.setDefault(profileName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}

/**
 * Hook to get prompts
 */
export function usePrompts() {
  return useQuery({
    queryKey: ['prompts'],
    queryFn: () => sdkService.getPrompts(),
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

/**
 * Hook to create prompt
 */
export function useCreatePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      name: string;
      description: string;
      template: string;
      category: string;
      is_default?: boolean;
    }) => sdkService.getSdk().prompts.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
}

/**
 * Hook to delete prompt
 */
export function useDeletePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (promptName: string) => sdkService.getSdk().prompts.delete(promptName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
}

/**
 * Hook to create prompt template (alias)
 */
export function useCreatePromptTemplate() {
  return useCreatePrompt();
}

/**
 * Hook to update prompt template
 */
export function useUpdatePromptTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ promptName, data }: { 
      promptName: string; 
      data: { name?: string; description?: string; template?: string; category?: string } 
    }) => sdkService.getSdk().prompts.update(promptName, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
}

/**
 * Hook to delete prompt template (alias)
 */
export function useDeletePromptTemplate() {
  return useDeletePrompt();
}

/**
 * Hook to set default prompt template
 */
export function useSetDefaultPromptTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (promptName: string) => sdkService.getSdk().prompts.setDefault(promptName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
    },
  });
}

/**
 * Hook to get prompt categories
 */
export function usePromptCategories() {
  return useQuery({
    queryKey: ['prompts', 'categories'],
    queryFn: () => sdkService.getPromptCategories(),
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

/**
 * Hook to get prompt templates (alias)
 */
export function usePromptTemplates() {
  return usePrompts();
}

// =============================================================================
// User Management Hooks
// =============================================================================

/**
 * Hook to update user profile
 */
export function useUpdateUserProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { email?: string; full_name?: string }) => 
      sdkService.updateUserProfile(data),
    onSuccess: () => {
      // Invalidate current user query
      queryClient.invalidateQueries({ queryKey: ['user', 'current'] });
    },
  });
}

/**
 * Hook for updating profile (alias for backward compatibility)
 */
export function useUpdateProfile() {
  return useUpdateUserProfile();
}

/**
 * Hook to change user password
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      sdkService.changePassword(data),
  });
}

// =============================================================================
// Search Hooks (Additional)
// =============================================================================

/**
 * Hook for document search (alias)
 */
export function useSearchDocuments() {
  return useDocumentSearch();
}

/**
 * Hook for search suggestions
 */
export function useSearchSuggestions() {
  return useMutation({
    mutationFn: (query: string) => sdkService.getSdk().search.getSuggestions({ query }),
  });
}

// =============================================================================
// Tool Management Hooks
// =============================================================================

/**
 * Hook to get tool statistics
 */
export function useToolStats() {
  return useQuery({
    queryKey: ['tools', 'stats'],
    queryFn: () => sdkService.getMcpStats(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to update MCP server
 */
export function useUpdateMcpServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ serverName, data }: { 
      serverName: string; 
      data: { enabled?: boolean; [key: string]: any } 
    }) => sdkService.getSdk().mcp.updateServer(serverName, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp', 'servers'] });
    },
  });
}

/**
 * Hook to toggle tool
 */
export function useToggleTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ toolName, enabled }: { toolName: string; enabled: boolean }) => 
      sdkService.getSdk().mcp.toggleTool(toolName, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp', 'tools'] });
    },
  });
}

// =============================================================================
// Enhanced Validation Hooks (for Demo)
// =============================================================================

/**
 * Hook for enhanced basic health (for validation demo)
 */
export function useEnhancedBasicHealth() {
  return useHealth();
}

/**
 * Hook for enhanced detailed health (for validation demo)
 */
export function useEnhancedDetailedHealth() {
  return useSystemHealth();
}

/**
 * Hook for enhanced current user (for validation demo)
 */
export function useEnhancedCurrentUser() {
  return useCurrentUser();
}