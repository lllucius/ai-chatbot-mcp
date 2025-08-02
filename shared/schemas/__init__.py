"""
Shared schemas package for API and SDK.

Contains Pydantic schema definitions that are used by both the API server
and the client SDK to ensure consistency and eliminate duplication.
"""

# Import all schemas to make them available from this package
from .admin import *
from .analytics import *
from .auth import *
from .base import *
from .common import *
from .conversation import *
from .document import *
from .llm_profile import *
from .mcp import *
from .prompt import *
from .search import *
from .tool_calling import *
from .user import *

__all__ = [
    # Admin schemas
    "TaskStatusResponse",
    "TaskStatsResponse",
    "ActiveTasksResponse",
    "QueueResponse",
    "TaskMonitorResponse",
    "WorkersResponse",
    "ProfileParametersResponse",
    "ProfileStatsResponse",
    "ProfileValidationResponse",
    "PromptCategoriesResponse",
    "PromptStatsResponse",
    "AdvancedSearchResponse",
    "DocumentStatsResponse",
    
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
    "ConversationStatsResponse",
    "RegistryStatsResponse",
    "DatabaseHealthResponse",
    "ServicesHealthResponse",
    "SystemMetricsResponse",
    
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
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    
    # LLM Profile schemas
    "LLMProfileBase",
    "LLMProfileCreate",
    "LLMProfileUpdate",
    "LLMProfileResponse",
    "LLMProfileListResponse",
    
    # MCP schemas
    "MCPServerCreateSchema",
    "MCPServerUpdateSchema", 
    "MCPServerSchema",
    "MCPToolCreateSchema",
    "MCPToolUpdateSchema",
    "MCPToolSchema",
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
    "PromptBase",
    "PromptCreate",
    "PromptUpdate",
    "PromptResponse",
    "PromptListResponse",
    
    # Search schemas
    "SearchParams",
    "SearchResponse",
    
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