/**
 * Service Index
 * 
 * Central export point for all API services
 */

export { default as apiClient } from './apiClient';
export type { ApiResponse, ApiError } from './apiClient';

export { AuthService } from './authService';
export { UserService } from './userService';
export { DocumentService } from './documentService';
export { ConversationService } from './conversationService';
export { HealthService } from './healthService';

// Re-export the auth context
export { AuthProvider, useAuth } from './AuthContext';