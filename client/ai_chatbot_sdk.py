"""
AI Chatbot SDK - Python client library for the AI Chatbot Platform.

This module provides a comprehensive SDK for interacting with the AI Chatbot Platform,
including authentication, document management, conversation handling, and search capabilities.

"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Type, TypeVar
from uuid import UUID

import requests
from pydantic import BaseModel, EmailStr, Field

# --- Exceptions ---


class ApiError(Exception):
    """
    Exception raised when API requests fail.

    Args:
        status: HTTP status code of the failed request.
        reason: HTTP reason phrase.
        url: The URL that was requested.
        body: Response body content.
    """

    def __init__(self, status: int, reason: str, url: str, body: Any):
        super().__init__(f"HTTP {status} {reason}: {body}")
        self.status = status
        self.reason = reason
        self.url = url
        self.body = body


T = TypeVar("T")

# --- ENUMS ---


class ToolHandlingMode(str, Enum):
    """
    Enum for different tool call result handling modes.

    - RETURN_RESULTS: Return tool call results as content without further AI processing
    - COMPLETE_WITH_RESULTS: Feed tool results back to AI for final completion
    """

    RETURN_RESULTS = "return_results"
    COMPLETE_WITH_RESULTS = "complete_with_results"


# --- SCHEMA MODELS ---


class BaseResponse(BaseModel):
    """Base response model for API responses."""

    success: bool
    message: str
    timestamp: Optional[str] = None


class Token(BaseModel):
    """Authentication token response model - matches app/schemas/auth.py Token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserResponse(BaseModel):
    """User profile response model - matches app/schemas/user.py UserResponse."""

    username: str = Field(..., description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    id: UUID = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_superuser: bool = Field(..., description="Whether the user has admin privileges")
    created_at: datetime = Field(..., description="When the user account was created")
    full_name: Optional[str] = Field(None, description="User's full name")

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    """User registration request model - matches app/schemas/auth.py RegisterRequest."""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=100, description="Strong password")
    full_name: Optional[str] = Field(None, max_length=255, description="Full display name")


class LoginRequest(BaseModel):
    """User login request model - matches app/schemas/auth.py LoginRequest."""

    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=8, max_length=100, description="Password")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: str


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""

    token: str
    new_password: str


class UserUpdate(BaseModel):
    """User profile update request model."""

    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """User password update request model."""

    current_password: str
    new_password: str


class PaginationParams(BaseModel):
    """Pagination parameters for list requests."""

    page: int
    per_page: int
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper model."""

    success: bool
    message: str
    items: List[Any]
    pagination: PaginationParams
    timestamp: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document metadata response model - matches app/schemas/document.py DocumentResponse."""

    id: UUID = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    processing_status: str = Field(..., description="Processing status")
    owner_id: UUID = Field(..., description="Owner user ID")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    chunk_count: int = Field(0, description="Number of chunks")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseResponse):
    """Document upload response model."""

    document: DocumentResponse
    processing_started: bool
    estimated_completion: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Document update request model."""

    title: Optional[str] = None
    metainfo: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Conversation metadata response model - matches app/schemas/conversation.py ConversationResponse."""

    id: UUID = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    is_active: bool = Field(True, description="Whether conversation is active")
    user_id: UUID = Field(..., description="Owner user ID")
    message_count: int = Field(0, description="Number of messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    """Conversation creation request model."""

    title: str
    is_active: Optional[bool] = True
    metainfo: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """Conversation update request model."""

    title: Optional[str] = None
    is_active: Optional[bool] = None
    metainfo: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Chat message response model - matches app/schemas/conversation.py MessageResponse."""

    id: UUID = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    conversation_id: UUID = Field(..., description="Parent conversation ID")
    token_count: int = Field(0, description="Number of tokens")
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="Tool calls made")
    tool_call_results: Optional[Dict[str, Any]] = Field(None, description="Tool call results")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class ProcessingStatusResponse(BaseResponse):
    """Document processing status response model."""

    document_id: UUID
    status: str
    progress: float
    chunks_processed: int
    total_chunks: int
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class DocumentSearchRequest(BaseModel):
    """Document search request model - matches app/schemas/document.py DocumentSearchRequest."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")
    algorithm: str = Field("hybrid", description="Search algorithm: vector, text, hybrid, mmr")
    document_ids: Optional[List[UUID]] = Field(None, description="Specific document IDs to search")
    file_types: Optional[List[str]] = Field(None, description="File types to include")


class ChatRequest(BaseModel):
    """Chat message request model - matches app/schemas/conversation.py ChatRequest."""

    user_message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID")
    conversation_title: Optional[str] = Field(
        None, max_length=500, description="New conversation title"
    )
    use_rag: bool = Field(True, description="Whether to use RAG for context")
    use_tools: bool = Field(True, description="Whether to enable tool calling")
    tool_handling_mode: ToolHandlingMode = Field(
        default=ToolHandlingMode.COMPLETE_WITH_RESULTS,
        description="How to handle tool call results: return_results or complete_with_results",
    )
    rag_documents: Optional[List[UUID]] = Field(None, description="Specific document IDs for RAG")

    # Registry integration fields
    prompt_name: Optional[str] = Field(
        None, description="Name of prompt to use from prompt registry"
    )
    profile_name: Optional[str] = Field(
        None, description="Name of LLM profile to use from profile registry"
    )
    llm_profile: Optional[Dict[str, Any]] = Field(
        None, description="LLM profile object with parameter configuration"
    )

    # Legacy fields for backward compatibility (deprecated)
    max_tokens: Optional[int] = Field(None, description="Max tokens (deprecated - use profile)")
    temperature: Optional[float] = Field(None, description="Temperature (deprecated - use profile)")


class ChatResponse(BaseResponse):
    """Chat response model with AI message - matches app/schemas/conversation.py ChatResponse."""

    ai_message: MessageResponse
    conversation: ConversationResponse
    response_time_ms: float
    usage: Optional[Dict[str, Any]] = None
    rag_context: Optional[List[Dict[str, Any]]] = None
    tool_calls_made: Optional[List[Dict[str, Any]]] = None
    tool_call_summary: Optional[Dict[str, Any]] = None


# --- NEW REGISTRY MODELS ---


class PromptResponse(BaseModel):
    """Prompt registry response model."""

    name: str = Field(..., description="Unique prompt name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Prompt description")
    category: Optional[str] = Field(None, description="Prompt category")
    content: str = Field(..., description="Prompt template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    is_active: bool = Field(True, description="Whether prompt is active")
    usage_count: int = Field(0, description="How many times used")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class PromptCreate(BaseModel):
    """Create prompt request model."""

    name: str = Field(..., description="Unique prompt name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Prompt description")
    category: Optional[str] = Field(None, description="Prompt category")
    content: str = Field(..., description="Prompt template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class LLMProfileResponse(BaseModel):
    """LLM profile registry response model."""

    name: str = Field(..., description="Unique profile name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Profile description")
    model_name: str = Field(..., description="OpenAI model name")
    parameters: Dict[str, Any] = Field(..., description="Model parameters")
    is_default: bool = Field(False, description="Whether this is the default profile")
    is_active: bool = Field(True, description="Whether profile is active")
    usage_count: int = Field(0, description="How many times used")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class LLMProfileCreate(BaseModel):
    """Create LLM profile request model."""

    name: str = Field(..., description="Unique profile name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Profile description")
    model_name: str = Field(..., description="OpenAI model name")
    parameters: Dict[str, Any] = Field(..., description="Model parameters")
    is_default: bool = Field(False, description="Whether this is the default profile")


class ToolResponse(BaseModel):
    """MCP tool response model."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    tool_schema: Dict[str, Any] = Field(..., description="Tool schema", alias="schema")
    server_name: str = Field(..., description="MCP server name")
    is_enabled: bool = Field(True, description="Whether tool is enabled")
    usage_count: int = Field(0, description="How many times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ToolsListResponse(BaseResponse):
    """Tools list response model."""

    available_tools: List[ToolResponse] = Field([], description="Available MCP tools")
    openai_tools: List[Dict[str, Any]] = Field([], description="OpenAI-formatted tools")
    servers: List[Dict[str, Any]] = Field([], description="MCP servers status")
    enabled_count: int = Field(0, description="Number of enabled tools")
    total_count: int = Field(0, description="Total number of tools")


# --- Helper Functions ---


def filter_query(query: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Filter out None values from query parameters."""
    return {k: v for k, v in (query or {}).items() if v is not None}


def handle_response(resp: requests.Response, url: str, cls: Optional[Type[T]] = None) -> Any:
    """
    Handle API response and raise ApiError on failure.

    Args:
        resp: The HTTP response object.
        url: The URL that was requested.
        cls: Optional type to deserialize response data into.

    Returns:
        Parsed JSON response data, optionally deserialized to cls.

    Raises:
        ApiError: If the response indicates an error.
    """
    if not resp.ok:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise ApiError(resp.status_code, resp.reason, url, body)

    json = resp.json()
    if cls:
        if "items" in json:
            r = PaginatedResponse(**json)
            items = []
            for item in r.items:
                items.append(cls(**item))
            r.items = items
            json["items"] = items

            return r
        return cls(**json)
    return json


def build_headers(
    token: Optional[str] = None, content_type: Optional[str] = None
) -> Dict[str, str]:
    """
    Build HTTP headers for API requests.

    Args:
        token: Optional authentication token.
        content_type: Optional content type header value.

    Returns:
        Dictionary of HTTP headers.
    """
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def make_url(base: str, path: str, query: Optional[Dict[str, Any]] = None) -> str:
    """
    Construct a URL with optional query parameters.

    Args:
        base: Base URL.
        path: URL path to append.
        query: Optional query parameters.

    Returns:
        Complete URL string.
    """
    url = base.rstrip("/") + path
    q = filter_query(query)
    if q:
        from urllib.parse import urlencode

        url += ("?" if "?" not in url else "&") + urlencode(q, doseq=True)
    return url


def fetch_all_pages(fetch_page: Callable[[int, int], Any], per_page: int = 50) -> List[Any]:
    """
    Fetch all pages of paginated results.

    Args:
        fetch_page: Function that takes page and per_page parameters.
        per_page: Number of items per page.

    Returns:
        List of all items from all pages.
    """
    items = []
    page = 1
    while True:
        resp = fetch_page(page, per_page)
        items.extend(resp.items)
        if len(resp.items) < per_page:
            break
        page += 1
    return items


# --- SDK SUBCLIENTS ---


class HealthClient:
    """Client for health check endpoints."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def basic(self) -> BaseResponse:
        """Get basic health status."""
        return self.sdk._request("/api/v1/health/", BaseResponse)

    def detailed(self) -> Dict[str, Any]:
        """Get detailed health status including system information."""
        return self.sdk._request("/api/v1/health/detailed")

    def database(self) -> Dict[str, Any]:
        """Check database connectivity status."""
        return self.sdk._request("/api/v1/health/database")

    def services(self) -> Dict[str, Any]:
        """Check external services status."""
        return self.sdk._request("/api/v1/health/services")

    def metrics(self) -> Dict[str, Any]:
        """Get system metrics and performance data."""
        return self.sdk._request("/api/v1/health/metrics")

    def readiness(self) -> Dict[str, Any]:
        """Check if the service is ready to accept requests."""
        return self.sdk._request("/api/v1/health/readiness")

    def liveness(self) -> Dict[str, Any]:
        """Check if the service is alive and responsive."""
        return self.sdk._request("/api/v1/health/liveness")


class AuthClient:
    """Client for authentication operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def register(self, data: RegisterRequest) -> UserResponse:
        return self.sdk._request(
            "/api/v1/auth/register",
            UserResponse,
            method="POST",
            json=data.model_dump(),
        )

    def login(self, username: str, password: str) -> Token:
        data = {"username": username, "password": password}
        token = self.sdk._request("/api/v1/auth/login", Token, method="POST", json=data)
        self.sdk.set_token(token.access_token)
        return token

    def me(self) -> UserResponse:
        return self.sdk._request("/api/v1/auth/me", UserResponse)

    def logout(self) -> BaseResponse:
        """Logout current user and invalidate token."""
        return self.sdk._request("/api/v1/auth/logout", BaseResponse, method="POST")

    def refresh(self) -> Token:
        """Refresh authentication token."""
        return self.sdk._request("/api/v1/auth/refresh", Token, method="POST")

    def request_password_reset(self, data: PasswordResetRequest) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/auth/password-reset",
            BaseResponse,
            method="POST",
            json=data.model_dump(),
        )

    def confirm_password_reset(self, data: PasswordResetConfirm) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/auth/password-reset/confirm",
            BaseResponse,
            method="POST",
            json=data.model_dump(),
        )


class UsersClient:
    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def me(self) -> UserResponse:
        return self.sdk._request("/api/v1/users/me", UserResponse)

    def update_me(self, data: UserUpdate) -> UserResponse:
        return self.sdk._request(
            "/api/v1/users/me", UserResponse, method="PUT", json=data.model_dump()
        )

    def change_password(self, data: UserPasswordUpdate) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/users/me/change-password",
            BaseResponse,
            method="POST",
            json=data.model_dump(),
        )

    def list(
        self,
        page: int = 1,
        size: int = 20,
        active_only: Optional[bool] = None,
        superuser_only: Optional[bool] = None,
    ) -> PaginatedResponse:
        params = filter_query(
            {
                "page": page,
                "size": size,
                "active_only": active_only,
                "superuser_only": superuser_only,
            }
        )
        return self.sdk._request("/api/v1/users/", UserResponse, params=params)

    def get(self, user_id: UUID) -> UserResponse:
        return self.sdk._request(f"/api/v1/users/{user_id}", UserResponse)

    def update(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        return self.sdk._request(
            f"/api/v1/users/{user_id}",
            UserResponse,
            method="PUT",
            json=data.model_dump(),
        )

    def delete(self, user_id: UUID) -> BaseResponse:
        return self.sdk._request(f"/api/v1/users/{user_id}", BaseResponse, method="DELETE")


class DocumentsClient:
    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def upload(self, file, title: Optional[str] = None) -> DocumentUploadResponse:
        """Upload a new document for processing."""
        files = {"file": file}
        data = {}
        if title:
            data["title"] = title
        return self.sdk._request(
            "/api/v1/documents/upload",
            DocumentUploadResponse,
            method="POST",
            files=files,
            data=data,
        )

    def list(
        self,
        page: int = 1,
        size: int = 20,
        file_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResponse:
        params = filter_query(
            {"page": page, "size": size, "file_type": file_type, "status": status}
        )
        return self.sdk._request("/api/v1/documents/", DocumentResponse, params=params)

    def get(self, document_id: UUID) -> DocumentResponse:
        return self.sdk._request(f"/api/v1/documents/{document_id}", DocumentResponse)

    def update(self, document_id: UUID, data: DocumentUpdate) -> DocumentResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}",
            DocumentResponse,
            method="PUT",
            json=data.model_dump(),
        )

    def delete(self, document_id: UUID) -> BaseResponse:
        return self.sdk._request(f"/api/v1/documents/{document_id}", BaseResponse, method="DELETE")

    def status(self, document_id: UUID) -> ProcessingStatusResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}/status",
            ProcessingStatusResponse,
        )

    def reprocess(self, document_id: UUID) -> BaseResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}/reprocess",
            BaseResponse,
            method="POST",
        )

    def download(self, document_id: UUID) -> bytes:
        url = make_url(self.sdk.base_url, f"/api/v1/documents/{document_id}/download")
        resp = self.sdk._session.get(url, headers=build_headers(self.sdk.token), stream=True)
        if not resp.ok:
            raise ApiError(resp.status_code, resp.reason, url, resp.text)
        return resp.content


class ConversationsClient:
    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def create(self, data: ConversationCreate) -> ConversationResponse:
        return self.sdk._request(
            "/api/v1/conversations/",
            ConversationResponse,
            method="POST",
            json=data.model_dump(mode="json"),
        )

    def list(
        self, page: int = 1, size: int = 20, active_only: Optional[bool] = None
    ) -> PaginatedResponse:
        params = filter_query({"page": page, "size": size, "active_only": active_only})
        return self.sdk._request("/api/v1/conversations/", ConversationResponse, params=params)

    def get(self, conversation_id: UUID) -> ConversationResponse:
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            ConversationResponse,
        )

    def update(self, conversation_id: UUID, data: ConversationUpdate) -> ConversationResponse:
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            ConversationResponse,
            method="PUT",
            json=data.model_dump(),
        )

    def delete(self, conversation_id: UUID) -> BaseResponse:
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            BaseResponse,
            method="DELETE",
        )

    def messages(self, conversation_id: UUID, page: int = 1, size: int = 50) -> PaginatedResponse:
        params = filter_query({"page": page, "size": size})
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}/messages",
            MessageResponse,
            params=params,
        )

    def chat(self, data: ChatRequest) -> ChatResponse:
        """Send a message and get AI response."""
        return self.sdk._request(
            "/api/v1/conversations/chat",
            ChatResponse,
            method="POST",
            json=data.model_dump(mode="json"),
        )

    def chat_stream(self, data: ChatRequest) -> Iterator[str]:
        """Send a message and get streaming AI response."""
        url = make_url(self.sdk.base_url, "/api/v1/conversations/chat/stream")
        headers = build_headers(self.sdk.token)
        headers["Accept"] = "text/event-stream"

        resp = self.sdk._session.post(
            url, headers=headers, json=data.model_dump(mode="json"), stream=True
        )

        if not resp.ok:
            raise ApiError(resp.status_code, resp.reason or "", url, resp.text)

        # Parse Server-Sent Events
        for line in resp.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data_content = line[6:]  # Remove "data: " prefix
                if data_content.strip() == "[DONE]":
                    break
                if data_content.strip():
                    yield data_content

    def stats(self) -> Dict[str, Any]:
        return self.sdk._request("/api/v1/conversations/stats")


class SearchClient:
    """Client for search operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def search(self, data: DocumentSearchRequest) -> Dict[str, Any]:
        """Search across documents using various algorithms."""
        return self.sdk._request("/api/v1/search/", dict, method="POST", json=data.model_dump())

    def similar_chunks(self, chunk_id: int, limit: int = 5) -> Dict[str, Any]:
        params = {"limit": limit}
        return self.sdk._request(f"/api/v1/search/similar/{chunk_id}", dict, params=params)

    def suggestions(self, query: str, limit: int = 5) -> List[Any]:
        params = {"query": query, "limit": limit}
        return self.sdk._request("/api/v1/search/suggestions", list, params=params)

    def history(self, limit: int = 10) -> List[Any]:
        params = {"limit": limit}
        return self.sdk._request("/api/v1/search/history", list, params=params)

    def clear_history(self) -> BaseResponse:
        return self.sdk._request("/api/v1/search/history", BaseResponse, method="DELETE")


class ToolsClient:
    """Client for MCP tools management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def list_tools(self) -> ToolsListResponse:
        """List all available MCP tools with registry integration."""
        return self.sdk._request("/api/v1/tools/", ToolsListResponse)

    def get_tool(self, tool_name: str) -> ToolResponse:
        """Get details for a specific tool."""
        return self.sdk._request(f"/api/v1/tools/{tool_name}", ToolResponse)

    def enable_tool(self, tool_name: str) -> BaseResponse:
        """Enable a specific tool."""
        return self.sdk._request(f"/api/v1/tools/{tool_name}/enable", BaseResponse, method="POST")

    def disable_tool(self, tool_name: str) -> BaseResponse:
        """Disable a specific tool."""
        return self.sdk._request(f"/api/v1/tools/{tool_name}/disable", BaseResponse, method="POST")

    def get_tool_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        return self.sdk._request("/api/v1/tools/stats", dict)


class MCPClient:
    """Client for MCP server and tools management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    # Server management methods
    def list_servers(
        self,
        enabled_only: bool = False,
        connected_only: bool = False,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """List all registered MCP servers."""
        params = filter_query({
            "enabled_only": enabled_only,
            "connected_only": connected_only,
            "detailed": detailed,
        })
        return self.sdk._request("/api/v1/mcp/servers", dict, params=params)

    def add_server(
        self,
        name: str,
        url: str,
        description: str = "",
        enabled: bool = True,
        transport: str = "http",
    ) -> Dict[str, Any]:
        """Add a new MCP server."""
        data = {
            "name": name,
            "url": url,
            "description": description,
            "enabled": enabled,
            "transport": transport,
        }
        return self.sdk._request("/api/v1/mcp/servers", dict, method="POST", json=data)

    def get_server(self, server_name: str) -> Dict[str, Any]:
        """Get details for a specific server."""
        return self.sdk._request(f"/api/v1/mcp/servers/{server_name}", dict)

    def update_server(self, server_name: str, **kwargs) -> Dict[str, Any]:
        """Update an MCP server."""
        return self.sdk._request(f"/api/v1/mcp/servers/{server_name}", dict, method="PATCH", json=kwargs)

    def remove_server(self, server_name: str) -> BaseResponse:
        """Remove an MCP server."""
        return self.sdk._request(f"/api/v1/mcp/servers/{server_name}", BaseResponse, method="DELETE")

    def enable_server(self, server_name: str) -> Dict[str, Any]:
        """Enable an MCP server."""
        return self.update_server(server_name, enabled=True)

    def disable_server(self, server_name: str) -> Dict[str, Any]:
        """Disable an MCP server."""
        return self.update_server(server_name, enabled=False)

    def test_server(self, server_name: str) -> Dict[str, Any]:
        """Test connection to an MCP server."""
        return self.sdk._request(f"/api/v1/mcp/servers/{server_name}/test", dict, method="POST")

    # Tools management methods
    def list_tools(
        self,
        server: Optional[str] = None,
        enabled_only: bool = False,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """List all available MCP tools."""
        params = filter_query({
            "server": server,
            "enabled_only": enabled_only,
            "detailed": detailed,
        })
        return self.sdk._request("/api/v1/mcp/tools", dict, params=params)

    def enable_tool(self, tool_name: str, server: Optional[str] = None) -> Dict[str, Any]:
        """Enable an MCP tool."""
        params = filter_query({"server": server})
        return self.sdk._request(f"/api/v1/mcp/tools/{tool_name}/enable", dict, method="PATCH", params=params)

    def disable_tool(self, tool_name: str, server: Optional[str] = None) -> Dict[str, Any]:
        """Disable an MCP tool."""
        params = filter_query({"server": server})
        return self.sdk._request(f"/api/v1/mcp/tools/{tool_name}/disable", dict, method="PATCH", params=params)

    # Statistics and refresh methods
    def get_stats(self) -> Dict[str, Any]:
        """Get MCP usage statistics."""
        return self.sdk._request("/api/v1/mcp/stats", dict)

    def refresh(self, server: Optional[str] = None) -> Dict[str, Any]:
        """Refresh MCP server connections and tool discovery."""
        params = filter_query({"server": server})
        return self.sdk._request("/api/v1/mcp/refresh", dict, method="POST", params=params)


class PromptsClient:
    """Client for prompt registry management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def list_prompts(
        self,
        active_only: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all prompts with optional filtering."""
        params = filter_query({"active_only": active_only, "category": category, "search": search})
        return self.sdk._request("/api/v1/prompts/", dict, params=params)

    def get_prompt(self, prompt_name: str) -> PromptResponse:
        """Get a specific prompt by name."""
        return self.sdk._request(f"/api/v1/prompts/{prompt_name}", PromptResponse)

    def create_prompt(self, data: PromptCreate) -> PromptResponse:
        """Create a new prompt."""
        return self.sdk._request(
            "/api/v1/prompts/", PromptResponse, method="POST", json=data.model_dump()
        )

    def update_prompt(self, prompt_name: str, data: Dict[str, Any]) -> PromptResponse:
        """Update an existing prompt."""
        return self.sdk._request(
            f"/api/v1/prompts/{prompt_name}", PromptResponse, method="PUT", json=data
        )

    def delete_prompt(self, prompt_name: str) -> BaseResponse:
        """Delete a prompt."""
        return self.sdk._request(f"/api/v1/prompts/{prompt_name}", BaseResponse, method="DELETE")

    def get_prompt_stats(self) -> Dict[str, Any]:
        """Get prompt usage statistics."""
        return self.sdk._request("/api/v1/prompts/stats", dict)

    def get_categories(self) -> Dict[str, Any]:
        """Get prompt categories."""
        return self.sdk._request("/api/v1/prompts/categories/", dict)

    def set_default_prompt(self, prompt_name: str) -> BaseResponse:
        """Set a prompt as the default."""
        return self.sdk._request(f"/api/v1/prompts/{prompt_name}/set-default", BaseResponse, method="POST")


class ProfilesClient:
    """Client for LLM profile registry management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def list_profiles(
        self, active_only: bool = True, search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all LLM profiles with optional filtering."""
        params = filter_query({"active_only": active_only, "search": search})
        return self.sdk._request("/api/v1/profiles/", dict, params=params)

    def get_profile(self, profile_name: str) -> LLMProfileResponse:
        """Get a specific LLM profile by name."""
        return self.sdk._request(f"/api/v1/profiles/{profile_name}", LLMProfileResponse)

    def create_profile(self, data: LLMProfileCreate) -> LLMProfileResponse:
        """Create a new LLM profile."""
        return self.sdk._request(
            "/api/v1/profiles/",
            LLMProfileResponse,
            method="POST",
            json=data.model_dump(),
        )

    def update_profile(self, profile_name: str, data: Dict[str, Any]) -> LLMProfileResponse:
        """Update an existing LLM profile."""
        return self.sdk._request(
            f"/api/v1/profiles/{profile_name}",
            LLMProfileResponse,
            method="PUT",
            json=data,
        )

    def delete_profile(self, profile_name: str) -> BaseResponse:
        """Delete an LLM profile."""
        return self.sdk._request(f"/api/v1/profiles/{profile_name}", BaseResponse, method="DELETE")

    def get_profile_stats(self) -> Dict[str, Any]:
        """Get LLM profile usage statistics."""
        return self.sdk._request("/api/v1/profiles/stats", dict)

    def set_default_profile(self, profile_name: str) -> BaseResponse:
        """Set a profile as the default."""
        return self.sdk._request(f"/api/v1/profiles/{profile_name}/set-default", BaseResponse, method="POST")


class AnalyticsClient:
    """Client for analytics and reporting."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def get_overview(self) -> Dict[str, Any]:
        """Get system overview analytics."""
        return self.sdk._request("/api/v1/analytics/overview", dict)

    def get_usage(self, period: Optional[str] = None, detailed: bool = False) -> Dict[str, Any]:
        """Get usage analytics."""
        params = filter_query({"period": period, "detailed": detailed})
        return self.sdk._request("/api/v1/analytics/usage", dict, params=params)

    def get_performance(self) -> Dict[str, Any]:
        """Get performance analytics."""
        return self.sdk._request("/api/v1/analytics/performance", dict)

    def get_users_analytics(self, top: Optional[int] = None, metric: Optional[str] = None) -> Dict[str, Any]:
        """Get user analytics."""
        params = filter_query({"top": top, "metric": metric})
        return self.sdk._request("/api/v1/analytics/users", dict, params=params)

    def get_trends(self) -> Dict[str, Any]:
        """Get trend analytics."""
        return self.sdk._request("/api/v1/analytics/trends", dict)

    def export_report(self, output: Optional[str] = None, details: bool = False) -> Dict[str, Any]:
        """Export analytics report."""
        data = filter_query({"output": output, "details": details})
        return self.sdk._request("/api/v1/analytics/export-report", dict, method="POST", json=data)


class DatabaseClient:
    """Client for database management operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def init_database(self) -> BaseResponse:
        """Initialize the database."""
        return self.sdk._request("/api/v1/database/init", BaseResponse, method="POST")

    def get_status(self) -> Dict[str, Any]:
        """Get database status."""
        return self.sdk._request("/api/v1/database/status", dict)

    def upgrade(self) -> BaseResponse:
        """Run database migrations/upgrade."""
        return self.sdk._request("/api/v1/database/upgrade", BaseResponse, method="POST")

    def downgrade(self) -> BaseResponse:
        """Downgrade database."""
        return self.sdk._request("/api/v1/database/downgrade", BaseResponse, method="POST")

    def backup(self, output: Optional[str] = None) -> BaseResponse:
        """Create database backup."""
        data = filter_query({"output": output})
        return self.sdk._request("/api/v1/database/backup", BaseResponse, method="POST", json=data)

    def restore(self, backup_file: str) -> BaseResponse:
        """Restore database from backup."""
        data = {"backup_file": backup_file}
        return self.sdk._request("/api/v1/database/restore", BaseResponse, method="POST", json=data)

    def get_tables(self) -> Dict[str, Any]:
        """Get database tables information."""
        return self.sdk._request("/api/v1/database/tables", dict)

    def vacuum(self) -> BaseResponse:
        """Vacuum database."""
        return self.sdk._request("/api/v1/database/vacuum", BaseResponse, method="POST")

    def get_migrations(self) -> Dict[str, Any]:
        """Get migration status."""
        return self.sdk._request("/api/v1/database/migrations", dict)

    def query(self, sql: str) -> Dict[str, Any]:
        """Execute custom query."""
        data = {"sql": sql}
        return self.sdk._request("/api/v1/database/query", dict, method="POST", json=data)

    def validate(self) -> Dict[str, Any]:
        """Validate database schema."""
        return self.sdk._request("/api/v1/database/validate", dict, method="POST")


class TasksClient:
    """Client for background task management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def get_status(self) -> Dict[str, Any]:
        """Get task system status."""
        return self.sdk._request("/api/v1/tasks/status", dict)

    def get_workers(self) -> Dict[str, Any]:
        """Get worker status."""
        return self.sdk._request("/api/v1/tasks/workers", dict)

    def get_queue(self) -> Dict[str, Any]:
        """Get queue information."""
        return self.sdk._request("/api/v1/tasks/queue", dict)

    def get_active(self) -> Dict[str, Any]:
        """Get active tasks."""
        return self.sdk._request("/api/v1/tasks/active", dict)

    def schedule_task(self, task_name: str, **kwargs) -> BaseResponse:
        """Schedule a task."""
        data = {"task_name": task_name, **kwargs}
        return self.sdk._request("/api/v1/tasks/schedule", BaseResponse, method="POST", json=data)

    def retry_failed(self) -> BaseResponse:
        """Retry failed tasks."""
        return self.sdk._request("/api/v1/tasks/retry-failed", BaseResponse, method="POST")

    def purge_queue(self) -> BaseResponse:
        """Purge task queue."""
        return self.sdk._request("/api/v1/tasks/purge", BaseResponse, method="POST")

    def monitor(self, refresh: Optional[int] = None, duration: Optional[int] = None) -> Dict[str, Any]:
        """Monitor tasks."""
        params = filter_query({"refresh": refresh, "duration": duration})
        return self.sdk._request("/api/v1/tasks/monitor", dict, params=params)


class AdminClient:
    """Client for admin operations across different resources."""

    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    # User admin operations
    def promote_user(self, user_id: UUID) -> BaseResponse:
        """Promote user to superuser."""
        return self.sdk._request(f"/api/v1/admin/users/{user_id}/promote", BaseResponse, method="POST")

    def demote_user(self, user_id: UUID) -> BaseResponse:
        """Demote user from superuser."""
        return self.sdk._request(f"/api/v1/admin/users/{user_id}/demote", BaseResponse, method="POST")

    def activate_user(self, user_id: UUID) -> BaseResponse:
        """Activate user account."""
        return self.sdk._request(f"/api/v1/admin/users/{user_id}/activate", BaseResponse, method="POST")

    def deactivate_user(self, user_id: UUID) -> BaseResponse:
        """Deactivate user account."""
        return self.sdk._request(f"/api/v1/admin/users/{user_id}/deactivate", BaseResponse, method="POST")

    def reset_user_password(self, user_id: UUID, new_password: Optional[str] = None) -> BaseResponse:
        """Reset user password."""
        data = filter_query({"new_password": new_password})
        return self.sdk._request(f"/api/v1/admin/users/{user_id}/reset-password", BaseResponse, method="POST", json=data)

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        return self.sdk._request("/api/v1/admin/users/stats", dict)

    # Document admin operations
    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        return self.sdk._request("/api/v1/admin/documents/stats", dict)

    def cleanup_documents(self, older_than: Optional[int] = None, status: Optional[str] = None) -> BaseResponse:
        """Cleanup old documents."""
        data = filter_query({"older_than": older_than, "status": status})
        return self.sdk._request("/api/v1/admin/documents/cleanup", BaseResponse, method="POST", json=data)

    def bulk_reprocess_documents(self, document_ids: Optional[List[UUID]] = None) -> BaseResponse:
        """Bulk reprocess documents."""
        data = filter_query({"document_ids": [str(id) for id in document_ids] if document_ids else None})
        return self.sdk._request("/api/v1/admin/documents/bulk-reprocess", BaseResponse, method="POST", json=data)

    def search_documents_advanced(self, **kwargs) -> Dict[str, Any]:
        """Advanced document search."""
        return self.sdk._request("/api/v1/admin/documents/search/advanced", dict, params=kwargs)

    # Conversation admin operations
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return self.sdk._request("/api/v1/admin/conversations/stats", dict)

    def search_conversations(self, **kwargs) -> Dict[str, Any]:
        """Search conversations."""
        return self.sdk._request("/api/v1/admin/conversations/search", dict, params=kwargs)

    def export_conversation(self, conversation_id: UUID) -> Dict[str, Any]:
        """Export conversation."""
        return self.sdk._request(f"/api/v1/admin/conversations/{conversation_id}/export", dict)

    def import_conversations(self, data: Dict[str, Any]) -> BaseResponse:
        """Import conversations."""
        return self.sdk._request("/api/v1/admin/conversations/import", BaseResponse, method="POST", json=data)

    def archive_conversations(self, older_than: Optional[int] = None) -> BaseResponse:
        """Archive old conversations."""
        data = filter_query({"older_than": older_than})
        return self.sdk._request("/api/v1/admin/conversations/archive", BaseResponse, method="POST", json=data)


# --- MAIN SDK CLASS ---


class AIChatbotSDK:
    """
    Main SDK class for AI Chatbot Platform API interactions.

    Provides a comprehensive client for accessing all API endpoints including
    authentication, document management, conversations, search functionality,
    and registry-based features for prompts, LLM profiles, and MCP tools.

    Features:
    - User authentication and management
    - Document upload, processing, and search
    - AI conversations with RAG and tool calling
    - Health monitoring and system status
    - Prompt registry for consistent system prompts
    - LLM profile registry for parameter management
    - MCP tools integration and management
    - Analytics and reporting
    - Database management
    - Background task management
    - Admin operations

    Args:
        base_url: Base URL of the AI Chatbot API.
        token: Optional authentication token.
        on_error: Optional error handler callback.
        session: Optional custom requests session.

    Example:
        >>> sdk = AIChatbotSDK("http://localhost:8000")
        >>> token = sdk.auth.login("username", "password")
        >>> prompts = sdk.prompts.list_prompts()
        >>> response = sdk.conversations.chat(ChatRequest(
        ...     user_message="Hello!",
        ...     prompt_name="helpful_assistant"
        ... ))
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        on_error: Optional[Callable[[ApiError], None]] = None,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.on_error = on_error
        self._session = session or requests.Session()

        # Initialize all client endpoints
        self.health = HealthClient(self)
        self.auth = AuthClient(self)
        self.users = UsersClient(self)
        self.documents = DocumentsClient(self)
        self.conversations = ConversationsClient(self)
        self.search = SearchClient(self)

        # Registry-based clients
        self.tools = ToolsClient(self)
        self.mcp = MCPClient(self)
        self.prompts = PromptsClient(self)
        self.profiles = ProfilesClient(self)

        # Management clients
        self.analytics = AnalyticsClient(self)
        self.database = DatabaseClient(self)
        self.tasks = TasksClient(self)
        self.admin = AdminClient(self)

    def set_token(self, token: Optional[str]) -> None:
        """Set authentication token for API requests."""
        self.token = token

    def get_token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.token

    def clear_token(self) -> None:
        """Clear stored authentication token."""
        self.token = None

    def _request(
        self,
        path: str,
        cls: Optional[Type[T]] = None,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = make_url(self.base_url, path, params)
        headers = build_headers(self.token)
        try:
            resp = self._session.request(
                method=method,
                url=url,
                headers=headers,
                params=None,
                json=json,
                data=data,
                files=files,
            )
            return handle_response(resp, url, cls)
        except ApiError as e:
            if self.on_error:
                self.on_error(e)
            raise
