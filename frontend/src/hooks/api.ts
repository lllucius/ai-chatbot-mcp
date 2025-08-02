/**
 * React Query Hooks for AI Chatbot Frontend
 * 
 * This module provides React Query hooks for all API operations, offering:
 * - Automatic caching and synchronization
 * - Background refetching and error handling
 * - Optimistic updates and mutations
 * - Loading and error states management
 * - Type-safe API operations with excellent developer experience
 * 
 * React Query benefits:
 * - Reduces boilerplate for API state management
 * - Provides automatic caching and stale-while-revalidate behavior
 * - Handles loading states, error states, and retry logic
 * - Supports optimistic updates for better user experience
 * - Automatically deduplicates requests
 * - Provides background sync when window regains focus
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import type {
  User,
  AuthToken,
  UserRegistration,
  UserLogin,
  Conversation,
  Message,
  ChatRequest,
  Document,
  DocumentUpload,
  SearchRequest,
  SearchResponse,
  SystemStats,
  UsageAnalytics,
  UserStats,
  McpServer,
  McpTool,
  ToolUsageStats,
  LlmProfile,
  PromptTemplate,
  HealthCheck,
  BackgroundTask,
  PaginatedResponse,
  UploadProgressCallback,
} from '../types/api';
import {
  authApi,
  conversationApi,
  documentApi,
  searchApi,
  analyticsApi,
  mcpApi,
  profileApi,
  promptApi,
  adminApi,
} from '../services/api';

// =============================================================================
// Query Keys for React Query
// =============================================================================

/**
 * Centralized query keys for consistent caching and invalidation
 * This prevents typos and makes cache management easier
 */
export const queryKeys = {
  // Authentication and users
  auth: ['auth'] as const,
  currentUser: () => [...queryKeys.auth, 'current'] as const,
  users: ['users'] as const,
  usersList: (page: number, limit: number) => [...queryKeys.users, 'list', page, limit] as const,
  
  // Conversations
  conversations: ['conversations'] as const,
  conversationsList: (page: number, limit: number) => [...queryKeys.conversations, 'list', page, limit] as const,
  conversation: (id: string) => [...queryKeys.conversations, id] as const,
  conversationMessages: (id: string, page: number, limit: number) => 
    [...queryKeys.conversations, id, 'messages', page, limit] as const,
  conversationSearch: (query: string, page: number, limit: number) => 
    [...queryKeys.conversations, 'search', query, page, limit] as const,
  
  // Documents
  documents: ['documents'] as const,
  documentsList: (page: number, limit: number) => [...queryKeys.documents, 'list', page, limit] as const,
  document: (id: string) => [...queryKeys.documents, id] as const,
  documentStatus: (id: string) => [...queryKeys.documents, id, 'status'] as const,
  
  // Search
  search: ['search'] as const,
  searchResults: (request: SearchRequest) => [...queryKeys.search, 'results', request] as const,
  searchSuggestions: (query: string, limit: number) => [...queryKeys.search, 'suggestions', query, limit] as const,
  
  // Analytics
  analytics: ['analytics'] as const,
  systemStats: () => [...queryKeys.analytics, 'system'] as const,
  usageAnalytics: (days: number) => [...queryKeys.analytics, 'usage', days] as const,
  userStats: (page: number, limit: number) => [...queryKeys.analytics, 'users', page, limit] as const,
  performanceMetrics: () => [...queryKeys.analytics, 'performance'] as const,
  
  // MCP Tools and Servers
  mcp: ['mcp'] as const,
  mcpServers: () => [...queryKeys.mcp, 'servers'] as const,
  mcpTools: () => [...queryKeys.mcp, 'tools'] as const,
  toolStats: () => [...queryKeys.mcp, 'tool-stats'] as const,
  
  // LLM Profiles
  profiles: ['profiles'] as const,
  profilesList: () => [...queryKeys.profiles, 'list'] as const,
  profile: (name: string) => [...queryKeys.profiles, name] as const,
  
  // Prompts
  prompts: ['prompts'] as const,
  promptsList: () => [...queryKeys.prompts, 'list'] as const,
  prompt: (name: string) => [...queryKeys.prompts, name] as const,
  
  // System Administration
  admin: ['admin'] as const,
  health: () => [...queryKeys.admin, 'health'] as const,
  backgroundTasks: (page: number, limit: number) => [...queryKeys.admin, 'tasks', page, limit] as const,
};

// =============================================================================
// Authentication Hooks
// =============================================================================

/**
 * Hook for user registration
 * Creates a new user account and automatically logs them in
 */
export function useRegister() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: () => {
      // Invalidate auth queries to refresh current user
      queryClient.invalidateQueries({ queryKey: queryKeys.auth });
    },
  });
}

/**
 * Hook for user login
 * Authenticates user and stores token for subsequent requests
 */
export function useLogin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: () => {
      // Invalidate auth queries to fetch current user data
      queryClient.invalidateQueries({ queryKey: queryKeys.auth });
    },
  });
}

/**
 * Hook for user logout
 * Clears authentication and invalidates all cached data
 */
export function useLogout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear all cached data when logging out
      queryClient.clear();
    },
  });
}

/**
 * Hook for getting current user information
 * Automatically retries and caches user data
 */
export function useCurrentUser(options?: UseQueryOptions<User>) {
  return useQuery({
    queryKey: queryKeys.currentUser(),
    queryFn: authApi.getCurrentUser,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry if it's an authentication error
      if (error?.status_code === 401) return false;
      return failureCount < 3;
    },
    ...options,
  });
}

/**
 * Hook for updating user profile
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (updatedUser) => {
      // Update the cached user data
      queryClient.setQueryData(queryKeys.currentUser(), updatedUser);
    },
  });
}

/**
 * Hook for changing password
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) =>
      authApi.changePassword(currentPassword, newPassword),
  });
}

// =============================================================================
// Conversation Hooks
// =============================================================================

/**
 * Hook for getting paginated conversations list
 */
export function useConversations(page = 1, limit = 20) {
  return useQuery({
    queryKey: queryKeys.conversationsList(page, limit),
    queryFn: () => conversationApi.getConversations(page, limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook for getting a specific conversation
 */
export function useConversation(conversationId: string, options?: UseQueryOptions<Conversation>) {
  return useQuery({
    queryKey: queryKeys.conversation(conversationId),
    queryFn: () => conversationApi.getConversation(conversationId),
    enabled: !!conversationId,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  });
}

/**
 * Hook for creating a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: conversationApi.createConversation,
    onSuccess: () => {
      // Invalidate conversations list to show the new conversation
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
    },
  });
}

/**
 * Hook for updating conversation metadata
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ conversationId, updates }: { 
      conversationId: string; 
      updates: Partial<Pick<Conversation, 'title' | 'is_active'>> 
    }) => conversationApi.updateConversation(conversationId, updates),
    onSuccess: (updatedConversation) => {
      // Update the cached conversation data
      queryClient.setQueryData(queryKeys.conversation(updatedConversation.id), updatedConversation);
      // Invalidate conversations list to reflect changes
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
    },
  });
}

/**
 * Hook for deleting a conversation
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: conversationApi.deleteConversation,
    onSuccess: (_, conversationId) => {
      // Remove from cache and invalidate related queries
      queryClient.removeQueries({ queryKey: queryKeys.conversation(conversationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
    },
  });
}

/**
 * Hook for getting conversation messages
 */
export function useConversationMessages(conversationId: string, page = 1, limit = 50) {
  return useQuery({
    queryKey: queryKeys.conversationMessages(conversationId, page, limit),
    queryFn: () => conversationApi.getMessages(conversationId, page, limit),
    enabled: !!conversationId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook for sending chat messages
 * Includes optimistic updates for better UX
 */
export function useSendMessage() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: conversationApi.sendMessage,
    onSuccess: (response) => {
      // Invalidate conversation messages to show new message
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversationMessages(response.conversation.id, 1, 50)
      });
      // Update conversation data if needed
      queryClient.setQueryData(queryKeys.conversation(response.conversation.id), response.conversation);
      // Invalidate conversations list to update last message preview
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
    },
  });
}

/**
 * Hook for searching conversations
 */
export function useSearchConversations(query: string, page = 1, limit = 20, enabled = true) {
  return useQuery({
    queryKey: queryKeys.conversationSearch(query, page, limit),
    queryFn: () => conversationApi.searchConversations(query, page, limit),
    enabled: enabled && query.length > 0,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

// =============================================================================
// Document Hooks
// =============================================================================

/**
 * Hook for getting paginated documents list
 */
export function useDocuments(page = 1, limit = 20) {
  return useQuery({
    queryKey: queryKeys.documentsList(page, limit),
    queryFn: () => documentApi.getDocuments(page, limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook for getting a specific document
 */
export function useDocument(documentId: string, options?: UseQueryOptions<Document>) {
  return useQuery({
    queryKey: queryKeys.document(documentId),
    queryFn: () => documentApi.getDocument(documentId),
    enabled: !!documentId,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  });
}

/**
 * Hook for uploading documents with progress tracking
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ upload, onProgress }: { 
      upload: DocumentUpload; 
      onProgress?: UploadProgressCallback 
    }) => documentApi.uploadDocument(upload, onProgress),
    onSuccess: () => {
      // Invalidate documents list to show new document
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}

/**
 * Hook for deleting documents
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: documentApi.deleteDocument,
    onSuccess: (_, documentId) => {
      // Remove from cache and invalidate related queries
      queryClient.removeQueries({ queryKey: queryKeys.document(documentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}

/**
 * Hook for getting document processing status with polling
 */
export function useDocumentStatus(documentId: string, pollInterval?: number) {
  return useQuery({
    queryKey: queryKeys.documentStatus(documentId),
    queryFn: () => documentApi.getDocumentStatus(documentId),
    enabled: !!documentId,
    refetchInterval: pollInterval, // Enable polling if interval provided
    staleTime: 0, // Always refetch for status
  });
}

/**
 * Hook for reprocessing documents
 */
export function useReprocessDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: documentApi.reprocessDocument,
    onSuccess: (_, documentId) => {
      // Invalidate document status to show updated processing state
      queryClient.invalidateQueries({ queryKey: queryKeys.documentStatus(documentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.document(documentId) });
    },
  });
}

// =============================================================================
// Search Hooks
// =============================================================================

/**
 * Hook for document search
 */
export function useSearchDocuments(searchRequest: SearchRequest, enabled = true) {
  return useQuery({
    queryKey: queryKeys.searchResults(searchRequest),
    queryFn: () => searchApi.searchDocuments(searchRequest),
    enabled: enabled && searchRequest.query.length > 0,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Hook for search suggestions
 */
export function useSearchSuggestions(partialQuery: string, limit = 5, enabled = true) {
  return useQuery({
    queryKey: queryKeys.searchSuggestions(partialQuery, limit),
    queryFn: () => searchApi.getSearchSuggestions(partialQuery, limit),
    enabled: enabled && partialQuery.length > 2,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// =============================================================================
// Analytics Hooks
// =============================================================================

/**
 * Hook for system statistics
 */
export function useSystemStats() {
  return useQuery({
    queryKey: queryKeys.systemStats(),
    queryFn: analyticsApi.getSystemStats,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Hook for usage analytics over time
 */
export function useUsageAnalytics(days = 30) {
  return useQuery({
    queryKey: queryKeys.usageAnalytics(days),
    queryFn: () => analyticsApi.getUsageAnalytics(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook for user statistics
 */
export function useUserStats(page = 1, limit = 20) {
  return useQuery({
    queryKey: queryKeys.userStats(page, limit),
    queryFn: () => analyticsApi.getUserStats(page, limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook for performance metrics
 */
export function usePerformanceMetrics() {
  return useQuery({
    queryKey: queryKeys.performanceMetrics(),
    queryFn: analyticsApi.getPerformanceMetrics,
    staleTime: 30 * 1000, // 30 seconds
  });
}

// =============================================================================
// MCP Tools and Server Hooks
// =============================================================================

/**
 * Hook for getting MCP servers
 */
export function useMcpServers() {
  return useQuery({
    queryKey: queryKeys.mcpServers(),
    queryFn: mcpApi.getServers,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Hook for adding MCP servers
 */
export function useAddMcpServer() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: mcpApi.addServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcpServers() });
    },
  });
}

/**
 * Hook for updating MCP servers
 */
export function useUpdateMcpServer() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ serverId, updates }: { serverId: string; updates: Partial<McpServer> }) =>
      mcpApi.updateServer(serverId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcpServers() });
    },
  });
}

/**
 * Hook for deleting MCP servers
 */
export function useDeleteMcpServer() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: mcpApi.deleteServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcpServers() });
    },
  });
}

/**
 * Hook for getting MCP tools
 */
export function useMcpTools() {
  return useQuery({
    queryKey: queryKeys.mcpTools(),
    queryFn: mcpApi.getTools,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Hook for toggling tool enable/disable
 */
export function useToggleTool() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ toolId, enabled }: { toolId: string; enabled: boolean }) =>
      mcpApi.toggleTool(toolId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.mcpTools() });
      queryClient.invalidateQueries({ queryKey: queryKeys.toolStats() });
    },
  });
}

/**
 * Hook for tool usage statistics
 */
export function useToolStats() {
  return useQuery({
    queryKey: queryKeys.toolStats(),
    queryFn: mcpApi.getToolStats,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// =============================================================================
// LLM Profile Hooks
// =============================================================================

/**
 * Hook for getting LLM profiles
 */
export function useLlmProfiles() {
  return useQuery({
    queryKey: queryKeys.profilesList(),
    queryFn: profileApi.getProfiles,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook for getting a specific LLM profile
 */
export function useLlmProfile(profileName: string, options?: UseQueryOptions<LlmProfile>) {
  return useQuery({
    queryKey: queryKeys.profile(profileName),
    queryFn: () => profileApi.getProfile(profileName),
    enabled: !!profileName,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Hook for creating LLM profiles
 */
export function useCreateLlmProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: profileApi.createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profilesList() });
    },
  });
}

/**
 * Hook for updating LLM profiles
 */
export function useUpdateLlmProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ profileName, updates }: { profileName: string; updates: Partial<LlmProfile> }) =>
      profileApi.updateProfile(profileName, updates),
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(queryKeys.profile(updatedProfile.name), updatedProfile);
      queryClient.invalidateQueries({ queryKey: queryKeys.profilesList() });
    },
  });
}

/**
 * Hook for deleting LLM profiles
 */
export function useDeleteLlmProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: profileApi.deleteProfile,
    onSuccess: (_, profileName) => {
      queryClient.removeQueries({ queryKey: queryKeys.profile(profileName) });
      queryClient.invalidateQueries({ queryKey: queryKeys.profilesList() });
    },
  });
}

/**
 * Hook for setting default LLM profile
 */
export function useSetDefaultLlmProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: profileApi.setDefaultProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profilesList() });
    },
  });
}

// =============================================================================
// Prompt Template Hooks
// =============================================================================

/**
 * Hook for getting prompt templates
 */
export function usePromptTemplates() {
  return useQuery({
    queryKey: queryKeys.promptsList(),
    queryFn: promptApi.getPrompts,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook for getting a specific prompt template
 */
export function usePromptTemplate(promptName: string, options?: UseQueryOptions<PromptTemplate>) {
  return useQuery({
    queryKey: queryKeys.prompt(promptName),
    queryFn: () => promptApi.getPrompt(promptName),
    enabled: !!promptName,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Hook for creating prompt templates
 */
export function useCreatePromptTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: promptApi.createPrompt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promptsList() });
    },
  });
}

/**
 * Hook for updating prompt templates
 */
export function useUpdatePromptTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ promptName, updates }: { promptName: string; updates: Partial<PromptTemplate> }) =>
      promptApi.updatePrompt(promptName, updates),
    onSuccess: (updatedPrompt) => {
      queryClient.setQueryData(queryKeys.prompt(updatedPrompt.name), updatedPrompt);
      queryClient.invalidateQueries({ queryKey: queryKeys.promptsList() });
    },
  });
}

/**
 * Hook for deleting prompt templates
 */
export function useDeletePromptTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: promptApi.deletePrompt,
    onSuccess: (_, promptName) => {
      queryClient.removeQueries({ queryKey: queryKeys.prompt(promptName) });
      queryClient.invalidateQueries({ queryKey: queryKeys.promptsList() });
    },
  });
}

/**
 * Hook for setting default prompt template
 */
export function useSetDefaultPromptTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: promptApi.setDefaultPrompt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.promptsList() });
    },
  });
}

// =============================================================================
// Admin Hooks
// =============================================================================

/**
 * Hook for system health checks
 */
export function useSystemHealth() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: adminApi.getHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

/**
 * Hook for background tasks
 */
export function useBackgroundTasks(page = 1, limit = 20) {
  return useQuery({
    queryKey: queryKeys.backgroundTasks(page, limit),
    queryFn: () => adminApi.getBackgroundTasks(page, limit),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook for getting all users (admin only)
 */
export function useAllUsers(page = 1, limit = 20) {
  return useQuery({
    queryKey: queryKeys.usersList(page, limit),
    queryFn: () => adminApi.getAllUsers(page, limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook for updating users (admin only)
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: Partial<User> }) =>
      adminApi.updateUser(userId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users });
    },
  });
}

/**
 * Hook for deleting users (admin only)
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users });
    },
  });
}