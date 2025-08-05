"""Shared schemas package for API and SDK.

Contains Pydantic schema definitions that are used by both the API server
and the client SDK to ensure consistency and eliminate duplication.
"""

# Import all schemas to make them available from this package
from .admin import *
from .admin_responses import *
from .analytics import *
from .auth import *
from .base import *
from .common import *
from .conversation import *
from .conversation_responses import *
from .database_responses import *
from .document import *
from .document_responses import *
from .health_responses import *
from .llm_profile import *
from .mcp import *
from .prompt import *
from .prompt_responses import *
from .search import *
from .search_responses import *
from .task_responses import *
from .tool_calling import *
from .user import *

__all__ = [
    # Admin schemas
    "TaskStatusResponse",
    "TaskStatsResponse",
    "QueueResponse",
    "TaskMonitorResponse",
    "WorkersResponse",
    "ProfileStatsResponse",
    "PromptCategoriesResponse",
    "PromptStatsResponse",
    "AdvancedSearchResponse",
    "DocumentStatsResponse",
    # Admin response schemas
    "DatabaseStatusResponse",
    "DatabaseTablesResponse",
    "DatabaseMigrationsResponse",
    "DatabaseAnalysisResponse",
    "DatabaseQueryResponse",
    "SearchResponse",
    "RegistryStatsResponse",
    "ConversationStatsResponse",
    # Analytics schemas
    "AnalyticsOverviewResponse",
    "AnalyticsUsageResponse",
    "AnalyticsPerformanceResponse",
    "AnalyticsTrendsResponse",
    "AnalyticsUserAnalyticsResponse",
    "AnalyticsExportResponse",
    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Base schemas
    "BaseSchema",
    # Common schemas
    "BaseResponse",
    "PaginationParams",
    # Conversation schemas
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ChatRequest",
    "ChatResponse",
    "ConversationListResponse",
    "MessageListResponse",
    "ConversationStats",
    # Document schemas
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    # LLM Profile schemas
    "LLMProfileCreate",
    "LLMProfileUpdate",
    "LLMProfileResponse",
    # MCP schemas
    "MCPServerCreateSchema",
    "MCPServerUpdateSchema",
    "MCPServerSchema",
    "MCPToolCreateSchema",
    "MCPToolUpdateSchema",
    "MCPToolResponse",
    "MCPToolExecutionRequestSchema",
    "MCPToolExecutionResultSchema",
    "MCPToolUsageStatsSchema",
    "MCPServerListResponse",
    "MCPToolListResponse",
    "MCPToolsResponse",
    "MCPStatsResponse",
    "MCPDiscoveryRequestSchema",
    "MCPDiscoveryResultSchema",
    "MCPHealthStatusSchema",
    "MCPConnectionStatusSchema",
    "MCPBatchUsageSchema",
    "MCPConnectionTestSchema",
    "MCPListFiltersSchema",
    "OpenAIToolSchema",
    "MCPOpenAIToolsResponseSchema",
    # Prompt schemas
    "PromptCreate",
    "PromptUpdate",
    "PromptResponse",
    "PromptListResponse",
    # Search schemas
    "SearchParams",
    # Task response schemas
    "TaskSystemStatusData",
    "TaskSystemStatusResponse",
    "WorkerInfo",
    "WorkerStatusData",
    "WorkerStatusResponse",
    "QueueInfo",
    "QueueStatusData",
    "QueueStatusResponse",
    "ActiveTaskInfo",
    "ActiveTasksData",
    "ActiveTasksResponse",
    "TaskStatisticsData",
    "TaskStatisticsResponse",
    "TaskMonitoringData",
    "TaskMonitoringResponse",
    "ProfileParametersData",
    "ProfileParametersResponse",
    "ProfileStatisticsData",
    "ProfileStatisticsResponse",
    "ProfileValidationData",
    "ProfileValidationResponse",
    "DefaultProfileResponse",
    # Document response schemas
    "DocumentUserInfo",
    "DocumentSearchResult",
    "DocumentSearchCriteria",
    "AdvancedSearchData",
    "DocumentStorageStats",
    "DocumentFileTypeStats",
    "DocumentTopUser",
    "DocumentStatisticsData",
    # Conversation response schemas
    "ConversationMetadata",
    "ExportedMessage",
    "ExportInfo",
    "ConversationExportDataJSON",
    "ConversationExportDataText",
    "ConversationExportDataCSV",
    "ConversationExportData",
    # Health response schemas
    "CacheStats",
    "CacheHealthData",
    "DatabaseTableInfo",
    "DatabaseHealthData",
    "ServiceStatus",
    "ServicesHealthData",
    "SystemResourceMetrics",
    "SystemMetricsData",
    "DetailedHealthCheckData",
    "PerformanceMetricsData",
    "LivenessProbeData",
    "ReadinessProbeData",
    "DatabaseHealthResponse",
    "ServicesHealthResponse",
    "SystemMetricsResponse",
    "ReadinessResponse",
    "PerformanceMetricsResponse",
    "LivenessResponse",
    # Prompt response schemas
    "PromptCategoryInfo",
    "PromptStatisticsData",
    "PromptCategoriesData",
    # Search response schemas
    "SearchSuggestion",
    "SearchSuggestionData",
    "SearchHistoryData",
    # Tool calling schemas
    "ToolHandlingMode",
    "ToolCallSummary",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserListResponse",
    "UserDetailResponse",
    "UserSearchParams",
    "UserStatsResponse",
]
