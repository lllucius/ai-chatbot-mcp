/**
 * OpenAPI Validation Utilities
 * 
 * This module provides utilities for validating API requests and responses
 * against the OpenAPI specification. It uses the auto-generated types from
 * the backend's OpenAPI spec to ensure type safety and runtime validation.
 */

import { z } from 'zod';
import type { paths, components, operations } from '../types/api-generated';

// =============================================================================
// Type Utilities for OpenAPI Operations
// =============================================================================

/**
 * Extract the response type for a given operation and status code
 */
export type OperationResponse<
  TOperation extends keyof operations,
  TStatus extends keyof operations[TOperation]['responses'] = 200
> = operations[TOperation]['responses'][TStatus] extends { content: { 'application/json': infer TContent } }
  ? TContent
  : never;

/**
 * Extract the request body type for a given operation
 */
export type OperationRequestBody<TOperation extends keyof operations> = 
  operations[TOperation]['requestBody'] extends { content: { 'application/json': infer TContent } }
    ? TContent
    : never;

/**
 * Extract path parameters for a given operation
 */
export type OperationPathParams<TOperation extends keyof operations> = 
  operations[TOperation]['parameters']['path'];

/**
 * Extract query parameters for a given operation
 */
export type OperationQueryParams<TOperation extends keyof operations> = 
  operations[TOperation]['parameters']['query'];

// =============================================================================
// Base Schema Definitions using Zod
// =============================================================================

/**
 * Base response schema that matches the backend's BaseResponse
 */
export const BaseResponseSchema = z.object({
  success: z.boolean(),
  message: z.string().optional(),
  data: z.unknown().optional(),
  error: z.string().optional(),
  request_id: z.string().optional(),
});

/**
 * Pagination metadata schema
 */
export const PaginationMetaSchema = z.object({
  page: z.number(),
  per_page: z.number(),
  total: z.number(),
  pages: z.number(),
  has_next: z.boolean(),
  has_prev: z.boolean(),
});

/**
 * Paginated response schema
 */
export const PaginatedResponseSchema = <T extends z.ZodType>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    pagination: PaginationMetaSchema,
  });

// =============================================================================
// Specific Entity Schemas
// =============================================================================

/**
 * User schema for validation
 */
export const UserSchema = z.object({
  id: z.string().uuid(),
  username: z.string(),
  email: z.string().email(),
  full_name: z.string(),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

/**
 * Conversation schema for validation
 */
export const ConversationSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  user_id: z.string().uuid(),
  is_active: z.boolean().default(true),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  message_count: z.number().optional(),
  last_message_at: z.string().datetime().optional(),
  metainfo: z.record(z.string(), z.unknown()).optional(),
});

/**
 * Message schema for validation
 */
export const MessageSchema = z.object({
  id: z.string().uuid(),
  conversation_id: z.string().uuid(),
  content: z.string(),
  is_user: z.boolean(),
  created_at: z.string().datetime(),
  token_usage: z.object({
    prompt_tokens: z.number(),
    completion_tokens: z.number(),
    total_tokens: z.number(),
  }).optional(),
  rag_context: z.object({
    documents_retrieved: z.number(),
    sources: z.array(z.object({
      document_id: z.string().uuid(),
      document_title: z.string(),
      chunk_content: z.string(),
      similarity_score: z.number(),
    })),
    search_query: z.string(),
    similarity_threshold: z.number(),
  }).optional(),
});

/**
 * Document schema for validation
 */
export const DocumentSchema = z.object({
  id: z.string().uuid(),
  filename: z.string(),
  title: z.string(),
  content_type: z.string(),
  file_size: z.number(),
  status: z.enum(['pending', 'processing', 'completed', 'failed', 'archived']),
  user_id: z.string().uuid(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  processed_at: z.string().datetime().optional(),
  chunk_count: z.number().optional(),
  error_message: z.string().optional(),
  processing_progress: z.number().min(0).max(100).optional(),
});

/**
 * Chat request schema for validation
 */
export const ChatRequestSchema = z.object({
  user_message: z.string().min(1),
  conversation_id: z.string().uuid().optional(),
  use_rag: z.boolean().default(false),
  profile_name: z.string().optional(),
  prompt_name: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  max_tokens: z.number().positive().optional(),
  top_p: z.number().min(0).max(1).optional(),
});

// =============================================================================
// Validation Functions
// =============================================================================

/**
 * Generic function to validate data against a Zod schema
 */
export function validateData<T>(schema: z.ZodType<T>, data: unknown): T {
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const issues = error.issues.map(issue => `${issue.path.join('.')}: ${issue.message}`).join(', ');
      throw new Error(`Validation failed: ${issues}`);
    }
    throw error;
  }
}

/**
 * Validate API response with proper error handling
 */
export function validateApiResponse<T>(
  schema: z.ZodType<T>,
  response: unknown,
  operationId: string
): T {
  try {
    // First validate the base response structure
    const baseResponse = BaseResponseSchema.parse(response);
    
    if (!baseResponse.success) {
      throw new Error(baseResponse.message || 'API request failed');
    }
    
    // Then validate the data payload against the specific schema
    return schema.parse(baseResponse.data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error(`Response validation failed for ${operationId}:`, error.issues);
      throw new Error(`Invalid response format for ${operationId}: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Validate request data before sending to API
 */
export function validateRequest<T>(
  schema: z.ZodType<T>,
  data: unknown,
  operationId: string
): T {
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error(`Request validation failed for ${operationId}:`, error.issues);
      throw new Error(`Invalid request data for ${operationId}: ${error.message}`);
    }
    throw error;
  }
}

// =============================================================================
// Type Guards using OpenAPI Generated Types
// =============================================================================

/**
 * Type guard to check if response matches BaseResponse structure
 */
export function isValidBaseResponse(response: unknown): response is components['schemas']['BaseResponse'] {
  return BaseResponseSchema.safeParse(response).success;
}

/**
 * Extract typed data from a validated API response
 */
export function extractResponseData<T>(response: components['schemas']['BaseResponse']): T {
  if (!response.success) {
    throw new Error(response.message || 'API request failed');
  }
  // Handle the case where BaseResponse might not have a 'data' field
  return (response as any).data as T;
}

// =============================================================================
// Error Handling Utilities
// =============================================================================

/**
 * Enhanced error type for API validation failures
 */
export class ApiValidationError extends Error {
  constructor(
    public operationId: string,
    public validationType: 'request' | 'response',
    public details: z.ZodIssue[],
    message?: string
  ) {
    super(message || `Validation failed for ${operationId} (${validationType})`);
    this.name = 'ApiValidationError';
  }
}

/**
 * Wrapper function to handle validation errors consistently
 */
export function withValidation<T>(
  validationFn: () => T,
  operationId: string,
  validationType: 'request' | 'response'
): T {
  try {
    return validationFn();
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ApiValidationError(operationId, validationType, error.issues);
    }
    throw error;
  }
}