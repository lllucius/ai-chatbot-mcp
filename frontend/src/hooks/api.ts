/**
 * Re-export hooks from SDK hooks for backward compatibility
 * 
 * This file maintains compatibility with existing components while
 * transitioning to the new SDK-based architecture.
 */

export * from './sdk-hooks';

// Legacy exports for backward compatibility
export {
  useLogin,
  useRegister,
  useLogout,
  useCurrentUser,
  useConversations,
  useConversation,
  useMessages,
  useCreateConversation,
  useSendMessage,
  useDeleteConversation,
  useDocuments,
  useDocument,
  useUploadDocument,
  useDeleteDocument,
  useDocumentStatus,
  useDocumentSearch,
  useConversationSearch,
  useHealth,
  useSystemStatus,
  useSystemMetrics,
  useAnalyticsOverview,
  useUsageAnalytics,
  useMcpServers,
  useMcpTools,
  useMcpStats,
  useAddMcpServer,
  useDeleteMcpServer,
  useLlmProfiles,
  useCreateProfile,
  useDeleteProfile,
  usePrompts,
  useCreatePrompt,
  useDeletePrompt,
  usePromptCategories,
  useUpdateUserProfile,
  useUpdateProfile,
  useChangePassword,
} from './sdk-hooks';