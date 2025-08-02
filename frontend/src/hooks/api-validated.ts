/**
 * Enhanced React Query Hooks with OpenAPI Validation
 * 
 * This module provides React Query hooks that use the validated API service,
 * ensuring that all API requests and responses are validated against the OpenAPI spec.
 * This provides runtime type safety and better error handling.
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { 
  enhancedAuthApi,
  enhancedConversationApi,
  enhancedDocumentApi,
  enhancedHealthApi
} from '../services/api-validated';
import type { components, operations } from '../types/api-generated';
import { queryKeys } from './api'; // Reuse existing query keys

// =============================================================================
// Enhanced Authentication Hooks with Validation
// =============================================================================

/**
 * Hook for user login with request/response validation
 */
export function useEnhancedLogin(
  options?: UseMutationOptions<
    components['schemas']['Token'],
    Error,
    { username: string; password: string }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enhancedAuthApi.login,
    onSuccess: (data) => {
      // Invalidate and refetch current user data after successful login
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser() });
      options?.onSuccess?.(data, { username: '', password: '' }, undefined);
    },
    ...options,
  });
}

/**
 * Hook for user registration with validation
 */
export function useEnhancedRegister(
  options?: UseMutationOptions<
    components['schemas']['UserResponse'],
    Error,
    { username: string; email: string; password: string; full_name: string }
  >
) {
  return useMutation({
    mutationFn: enhancedAuthApi.register,
    ...options,
  });
}

/**
 * Hook for getting current user with response validation
 */
export function useEnhancedCurrentUser(
  options?: UseQueryOptions<components['schemas']['UserResponse'], Error>
) {
  return useQuery({
    queryKey: queryKeys.currentUser(),
    queryFn: enhancedAuthApi.getCurrentUser,
    retry: false, // Don't retry if unauthorized
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
    ...options,
  });
}

// =============================================================================
// Enhanced Conversation Hooks with Validation
// =============================================================================

/**
 * Hook for getting conversations with validation
 */
export function useEnhancedConversations(
  page = 1,
  limit = 20,
  options?: UseQueryOptions<components['schemas']['PaginatedResponse_ConversationResponse_'], Error>
) {
  return useQuery({
    queryKey: queryKeys.conversationsList(page, limit),
    queryFn: () => enhancedConversationApi.getConversations(page, limit),
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
    ...options,
  });
}

/**
 * Hook for creating conversation with validation
 */
export function useEnhancedCreateConversation(
  options?: UseMutationOptions<
    components['schemas']['ConversationResponse'],
    Error,
    string
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enhancedConversationApi.createConversation,
    onSuccess: (data) => {
      // Invalidate conversations list to show new conversation
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
      options?.onSuccess?.(data, '', undefined);
    },
    ...options,
  });
}

/**
 * Hook for sending messages with validation
 */
export function useEnhancedSendMessage(
  options?: UseMutationOptions<
    components['schemas']['ChatResponse'],
    Error,
    {
      user_message: string;
      conversation_id?: string | null;
      conversation_title?: string | null;
      use_rag?: boolean;
      use_tools?: boolean;
      tool_handling_mode?: 'return_results' | 'complete_with_results';
      rag_documents?: string[] | null;
      max_tokens?: number | null;
    }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enhancedConversationApi.sendMessage,
    onSuccess: (data) => {
      // Invalidate relevant queries after successful message
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
      if (data.conversation?.id) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.conversation(data.conversation.id) 
        });
      }
      options?.onSuccess?.(data, {
        user_message: '',
        use_rag: false,
        use_tools: false,
        tool_handling_mode: 'return_results',
      }, undefined);
    },
    ...options,
  });
}

// =============================================================================
// Enhanced Document Hooks with Validation
// =============================================================================

/**
 * Hook for getting documents with validation
 */
export function useEnhancedDocuments(
  page = 1,
  limit = 20,
  options?: UseQueryOptions<components['schemas']['PaginatedResponse_DocumentResponse_'], Error>
) {
  return useQuery({
    queryKey: queryKeys.documentsList(page, limit),
    queryFn: () => enhancedDocumentApi.getDocuments(page, limit),
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
    ...options,
  });
}

/**
 * Hook for uploading documents with validation
 */
export function useEnhancedUploadDocument(
  options?: UseMutationOptions<
    components['schemas']['DocumentResponse'],
    Error,
    { file: File; title?: string; processImmediately?: boolean }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, title, processImmediately = true }) =>
      enhancedDocumentApi.uploadDocument(file, title, processImmediately),
    onSuccess: (data) => {
      // Invalidate documents list to show new document
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
      options?.onSuccess?.(data, { file: new File([], ''), title: '', processImmediately: true }, undefined);
    },
    ...options,
  });
}

// =============================================================================
// Enhanced Health Check Hooks with Validation
// =============================================================================

/**
 * Hook for basic health check with validation
 */
export function useEnhancedBasicHealth(
  options?: UseQueryOptions<components['schemas']['BaseResponse'], Error>
) {
  return useQuery({
    queryKey: ['health', 'basic'],
    queryFn: enhancedHealthApi.getBasicHealth,
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    staleTime: 10 * 1000, // Consider data stale after 10 seconds
    ...options,
  });
}

/**
 * Hook for detailed health check with validation
 */
export function useEnhancedDetailedHealth(
  options?: UseQueryOptions<Record<string, unknown>, Error>
) {
  return useQuery({
    queryKey: ['health', 'detailed'],
    queryFn: enhancedHealthApi.getDetailedHealth,
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    staleTime: 10 * 1000, // Consider data stale after 10 seconds
    ...options,
  });
}

// =============================================================================
// Error Types and Utilities
// =============================================================================

/**
 * Enhanced error type that includes validation information
 */
export interface ValidationError extends Error {
  operationId?: string;
  validationType?: 'request' | 'response';
  validationDetails?: any[];
}

/**
 * Type guard to check if error is a validation error
 */
export function isValidationError(error: unknown): error is ValidationError {
  return error instanceof Error && 'operationId' in error;
}

/**
 * Hook to handle validation errors consistently
 */
export function useValidationErrorHandler() {
  return (error: unknown) => {
    if (isValidationError(error)) {
      console.error('API Validation Error:', {
        operation: error.operationId,
        type: error.validationType,
        details: error.validationDetails,
        message: error.message,
      });
      
      // You could show a toast notification here
      return `Validation failed for ${error.operationId}: ${error.message}`;
    }
    
    return error instanceof Error ? error.message : 'Unknown error occurred';
  };
}