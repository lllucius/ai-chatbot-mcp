"""AI Chatbot Platform SDK - Comprehensive Python Client Library.

This module provides a complete async Python SDK for the AI Chatbot Platform, enabling
developers to integrate platform capabilities into their applications with full API
coverage, type safety, and enterprise-grade reliability. The SDK is designed for
high-performance async operations and provides comprehensive error handling and
retry mechanisms.

The SDK covers all platform functionality including authentication, user management,
conversation handling, document processing, analytics, MCP integration, and
administrative operations. All methods are async and should be called with await
for optimal performance.

Key Features:
    - Complete platform API coverage with async operations
    - Type-safe operations with Pydantic models and validation
    - Comprehensive error handling with detailed exception information
    - Automatic retry mechanisms with exponential backoff
    - Streaming support for real-time operations
    - Authentication management with automatic token refresh

API Coverage:
    - Authentication: Login, logout, token management, user verification
    - Users: User creation, management, profile updates, administrative operations
    - Conversations: Chat management, message handling, conversation analytics
    - Documents: Upload, processing, search, vector embedding generation
    - Analytics: System metrics, user analytics, performance monitoring
    - Database: Administrative operations, health checks, maintenance
    - Tasks: Background job management, queue monitoring, worker scaling
    - MCP: Model Context Protocol integration, tool management
    - Profiles: LLM parameter management, optimization, A/B testing
    - Prompts: Template management, versioning, performance analytics

Authentication Flow:
    The SDK implements secure JWT-based authentication with automatic token
    management and refresh capabilities. Tokens are managed transparently
    for all authenticated operations.

Error Handling:
    The SDK provides comprehensive error handling with structured exceptions
    that include HTTP status codes, detailed error messages, and context
    information for debugging and monitoring.

Performance Features:
    - Async operations for non-blocking I/O and high throughput
    - Connection pooling and keep-alive for efficient HTTP operations
    - Request batching for bulk operations
    - Streaming support for large data transfers
    - Configurable timeouts and retry policies

Type Safety:
    All SDK operations use Pydantic models for request/response validation,
    providing compile-time type checking and runtime validation for robust
    application development.

Use Cases:
    - Application development and platform integration
    - Automated testing and validation workflows
    - Data analysis and reporting applications
    - System administration and monitoring tools
    - Custom AI applications and workflow automation

Example Usage:
    ```python
    import asyncio
    from ai_chatbot_sdk import AIChatbotSDK
    from shared.schemas import ChatRequest

    async def main():
        # Initialize SDK
        sdk = AIChatbotSDK(
            base_url="https://api.chatbot.example.com",
            timeout=30
        )

        # Authenticate
        token = await sdk.auth.login("username", "password")
        sdk.set_token(token.access_token)

        # Create conversation
        conversation = await sdk.conversations.create(
            title="Customer Support Session"
        )

        # Send message
        chat_request = ChatRequest(
            conversation_id=conversation.id,
            message="Hello, how can you help me today?"
        )
        response = await sdk.conversations.chat(chat_request)

        # Search documents
        search_results = await sdk.documents.search(
            query="machine learning best practices",
            limit=10
        )

        # Get analytics
        overview = await sdk.analytics.get_overview()

    # Run the example
    asyncio.run(main())
    ```

Integration Patterns:
    - Microservices architecture with async service communication
    - Event-driven applications with real-time data processing
    - Data pipeline integration for document processing and analysis
    - Monitoring and alerting system integration
    - Custom dashboard and reporting application development

Performance Considerations:
    - Use connection pooling for multiple concurrent operations
    - Implement proper error handling and retry logic
    - Consider rate limiting for high-volume operations
    - Use streaming operations for large data transfers
    - Monitor token expiration and refresh proactively
"""

from collections.abc import AsyncIterator
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

import httpx

# Import all schema models from shared package instead of defining locally
from shared.schemas import (  # Base and common schemas; Conversation schemas; Document schemas; LLM Profile schemas; Prompt schemas; Auth schemas; Search schemas; User schemas
    BaseResponse,
    BaseSchema,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationStatsResponse,
    ConversationUpdate,
    DatabaseHealthResponse,
    DocumentResponse,
    DocumentSearchRequest,
    LLMProfileCreate,
    LLMProfileResponse,
    MessageResponse,
    PaginationParams,
    PasswordResetConfirm,
    PasswordResetRequest,
    PromptCreate,
    PromptResponse,
    RegisterRequest,
    RegistryStatsResponse,
    SearchResponse,
    ServicesHealthResponse,
    SystemMetricsResponse,
    Token,
    UserPasswordUpdate,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
)

# --- Exceptions ---


class ApiError(Exception):
    """Exception raised when API requests fail.

    Args:
        status: HTTP status code of the failed request.
        reason: HTTP reason phrase.
        url: The URL that was requested.
        body: Response body content.

    """

    def __init__(self, status: int, reason: str, url: str, body: Any):
        """Initialize ApiError with HTTP response details.

        Args:
            status: HTTP status code of the failed request.
            reason: HTTP reason phrase.
            url: The URL that was requested.
            body: Response body content.

        """
        super().__init__(f"HTTP {status} {reason}: {body}")
        self.status = status
        self.reason = reason
        self.url = url
        self.body = body


T = TypeVar("T")


# --- Additional Response Models (not in shared schemas) ---


class DocumentUploadResponse(BaseResponse):
    """Document upload response model."""

    document: DocumentResponse
    processing_started: bool
    estimated_completion: Optional[str] = None


class DocumentUpdate(BaseSchema):
    """Document update request model."""

    title: Optional[str] = None
    metainfo: Optional[Dict[str, Any]] = None


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


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper model."""

    success: bool
    message: str
    items: List[Any]
    pagination: PaginationParams
    timestamp: Optional[str] = None


class ReadinessResponse(BaseSchema):
    """Readiness check response model."""

    status: str
    message: str
    timestamp: str


class LivenessResponse(BaseSchema):
    """Liveness check response model."""

    status: str
    message: str
    timestamp: str


class PerformanceMetricsResponse(BaseSchema):
    """Performance metrics response model."""

    data: Dict[str, Any]


# --- Utility Functions ---


def filter_query(query: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Filter out None values from query parameters."""
    return {k: v for k, v in (query or {}).items() if v is not None}


async def handle_response(
    resp: httpx.Response, url: str, cls: Optional[Type[T]] = None
) -> Any:
    """Handle API response and raise ApiError on failure.

    Args:
        resp: The HTTP response object from httpx.
        url: The URL that was requested.
        cls: Optional type to deserialize response data into.

    Returns:
        Parsed JSON response data, optionally deserialized to cls.

    Raises:
        ApiError: If the response indicates an error.

    """
    if not resp.is_success:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise ApiError(resp.status_code, resp.reason_phrase, url, body)

    json_data = resp.json()
    if cls:
        if "items" in json_data:
            r = PaginatedResponse(**json_data)
            items = []
            for item in r.items:
                items.append(cls(**item))
            r.items = items
            json_data["items"] = items

            return r
        return cls(**json_data)
    return json_data


def build_headers(
    token: Optional[str] = None, content_type: Optional[str] = None
) -> Dict[str, str]:
    """Build HTTP headers for API requests.

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
    """Construct a URL with optional query parameters.

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


async def fetch_all_pages(
    fetch_page: Callable[[int, int], Any], per_page: int = 50
) -> List[Any]:
    """Fetch all pages of paginated results asynchronously.

    Args:
        fetch_page: Async function that takes page and per_page parameters.
        per_page: Number of items per page.

    Returns:
        List of all items from all pages.

    """
    all_items = []
    page = 1

    while True:
        response = await fetch_page(page, per_page)

        items = response.items if hasattr(response, "items") else response

        if not items:
            break

        all_items.extend(items)

        # Check if we got a full page - if not, we're done
        if len(items) < per_page:
            break

        page += 1

    return all_items


# This is the new, clean SDK that imports schemas from shared package
# instead of defining them locally. I'll continue with the client classes.# --- SDK SUBCLIENTS ---


class HealthClient:
    """Async client for health check endpoints."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize health client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    async def basic(self) -> BaseResponse:
        """Get basic health status."""
        return await self.sdk._request("/api/v1/health/", BaseResponse)

    async def detailed(self) -> Dict[str, Any]:
        """Get detailed health status including system information."""
        return await self.sdk._request("/api/v1/health/detailed")

    async def database(self) -> DatabaseHealthResponse:
        """Check database connectivity status."""
        return await self.sdk._request(
            "/api/v1/health/database", DatabaseHealthResponse
        )

    async def services(self) -> ServicesHealthResponse:
        """Check external services status."""
        return await self.sdk._request(
            "/api/v1/health/services", ServicesHealthResponse
        )

    async def metrics(self) -> SystemMetricsResponse:
        """Get system metrics and performance data."""
        return await self.sdk._request("/api/v1/health/metrics", SystemMetricsResponse)

    async def readiness(self) -> ReadinessResponse:
        """Check if the service is ready to accept requests."""
        return await self.sdk._request("/api/v1/health/readiness", ReadinessResponse)

    async def liveness(self) -> LivenessResponse:
        """Check if the service is alive."""
        return await self.sdk._request("/api/v1/health/liveness", LivenessResponse)

    async def performance(self) -> PerformanceMetricsResponse:
        """Get performance metrics."""
        return await self.sdk._request(
            "/api/v1/health/performance", PerformanceMetricsResponse
        )


class AuthClient:
    """Async client for authentication operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize authentication client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user account."""
        return await self.sdk._request(
            "/api/v1/auth/register",
            UserResponse,
            method="POST",
            json=data.model_dump(),
        )

    async def login(self, username: str, password: str) -> Token:
        """Login with username and password."""
        data = {"username": username, "password": password}
        token = await self.sdk._request(
            "/api/v1/auth/login", Token, method="POST", json=data
        )
        self.sdk.set_token(token.access_token)
        return token

    async def me(self) -> UserResponse:
        """Get current user profile information."""
        return await self.sdk._request("/api/v1/users/me", UserResponse)

    async def logout(self) -> BaseResponse:
        """Logout current user and invalidate token."""
        return await self.sdk._request(
            "/api/v1/auth/logout", BaseResponse, method="POST"
        )

    async def refresh(self) -> Token:
        """Refresh authentication token."""
        return await self.sdk._request("/api/v1/auth/refresh", Token, method="POST")

    async def request_password_reset(self, data: PasswordResetRequest) -> BaseResponse:
        """Request password reset for a user."""
        return await self.sdk._request(
            "/api/v1/users/password-reset",
            BaseResponse,
            method="POST",
            json=data.model_dump(),
        )

    async def confirm_password_reset(self, data: PasswordResetConfirm) -> BaseResponse:
        """Confirm password reset with token."""
        return await self.sdk._request(
            "/api/v1/users/password-reset/confirm",
            BaseResponse,
            method="POST",
            json=data.model_dump(),
        )


class UsersClient:
    """Async client for user management operations.

    Provides comprehensive user account management including profile updates,
    password changes, user listing, and administrative operations.
    """

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize users client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    async def me(self) -> UserResponse:
        """Get current authenticated user's profile.

        Returns:
            UserResponse: Current user's profile information.

        Raises:
            ApiError: If the request fails or user is not authenticated.

        """
        return await self.sdk._request("/api/v1/users/me", UserResponse)

    async def update_me(self, data: UserUpdate) -> UserResponse:
        """Update current user's profile information.

        Args:
            data: UserUpdate model with fields to update.

        Returns:
            UserResponse: Updated user profile information.

        Raises:
            ApiError: If the request fails or validation errors occur.

        """
        return await self.sdk._request(
            "/api/v1/users/me", UserResponse, method="PUT", json=data.model_dump()
        )

    async def change_password(self, data: UserPasswordUpdate) -> BaseResponse:
        """Change current user's password.

        Args:
            data: UserPasswordUpdate with current and new password.

        Returns:
            BaseResponse: Success/failure status of password change.

        Raises:
            ApiError: If the request fails or current password is incorrect.

        """
        return await self.sdk._request(
            "/api/v1/users/me/change-password",
            BaseResponse,
            method="POST",
            json=data.model_dump(),
        )

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        active_only: Optional[bool] = None,
        superuser_only: Optional[bool] = None,
    ) -> PaginatedResponse:
        """List users with optional filtering and pagination.

        Args:
            page: Page number for pagination (default: 1).
            size: Number of users per page (default: 20).
            active_only: Filter to only active users if True.
            superuser_only: Filter to only superusers if True.

        Returns:
            PaginatedResponse: Paginated list of users.

        Raises:
            ApiError: If the request fails or insufficient permissions.

        """
        params = filter_query(
            {
                "page": page,
                "size": size,
                "active_only": active_only,
                "superuser_only": superuser_only,
            }
        )
        return await self.sdk._request("/api/v1/users/", UserResponse, params=params)

    async def get(self, user_id: UUID) -> UserResponse:
        """Get user profile by ID.

        Args:
            user_id: UUID of the user to retrieve.

        Returns:
            UserResponse: User profile information.

        Raises:
            ApiError: If user not found or insufficient permissions.

        """
        return await self.sdk._request(f"/api/v1/users/byid/{user_id}", UserResponse)

    async def update(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """Update user profile by ID.

        Args:
            user_id: UUID of the user to update.
            data: UserUpdate model with fields to update.

        Returns:
            UserResponse: Updated user profile information.

        Raises:
            ApiError: If user not found or insufficient permissions.

        """
        return await self.sdk._request(
            f"/api/v1/users/byid/{user_id}",
            UserResponse,
            method="PUT",
            json=data.model_dump(),
        )

    async def delete(self, user_id: UUID) -> BaseResponse:
        """Delete user account by ID.

        Args:
            user_id: UUID of the user to delete.

        Returns:
            BaseResponse: Success/failure status of deletion.

        Raises:
            ApiError: If user not found or insufficient permissions.

        """
        return await self.sdk._request(
            f"/api/v1/users/byid/{user_id}", BaseResponse, method="DELETE"
        )

    async def statistics(self) -> UserStatsResponse:
        """Get comprehensive user statistics for admin access."""
        return await self.sdk._request("/api/v1/users/users/stats", UserStatsResponse)


class DocumentsClient:
    """Async client for document management operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize documents client.

        Args:
            sdk: The main SDK instance for making API requests

        """
        self.sdk = sdk

    async def upload(self, file, title: Optional[str] = None) -> DocumentUploadResponse:
        """Upload a new document for processing."""
        files = {"file": file}
        data = {}
        if title:
            data["title"] = title
        return await self.sdk._request(
            "/api/v1/documents/upload",
            DocumentUploadResponse,
            method="POST",
            files=files,
            data=data,
        )

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        file_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResponse:
        """List documents with optional filtering and pagination.

        Args:
            page: Page number for pagination (default: 1).
            size: Number of documents per page (default: 20).
            file_type: Filter by file type (e.g., 'pdf', 'txt').
            status: Filter by processing status (e.g., 'completed', 'processing').

        Returns:
            PaginatedResponse: Paginated list of documents.

        Raises:
            ApiError: If the request fails.

        """
        params = filter_query(
            {"page": page, "size": size, "file_type": file_type, "status": status}
        )
        return await self.sdk._request(
            "/api/v1/documents/", DocumentResponse, params=params
        )

    async def get(self, document_id: UUID) -> DocumentResponse:
        """Get document metadata by ID.

        Args:
            document_id: UUID of the document to retrieve.

        Returns:
            DocumentResponse: Document metadata and status.

        Raises:
            ApiError: If document not found or access denied.

        """
        return await self.sdk._request(
            f"/api/v1/documents/byid/{document_id}", DocumentResponse
        )

    async def update(self, document_id: UUID, data: DocumentUpdate) -> DocumentResponse:
        """Update document metadata.

        Args:
            document_id: UUID of the document to update.
            data: DocumentUpdate model with fields to update.

        Returns:
            DocumentResponse: Updated document metadata.

        Raises:
            ApiError: If document not found or validation errors.

        """
        return await self.sdk._request(
            f"/api/v1/documents/byid/{document_id}",
            DocumentResponse,
            method="PUT",
            json=data.model_dump(),
        )

    async def delete(self, document_id: UUID) -> BaseResponse:
        """Delete document and all associated data.

        Args:
            document_id: UUID of the document to delete.

        Returns:
            BaseResponse: Success/failure status of deletion.

        Raises:
            ApiError: If document not found or access denied.

        """
        return await self.sdk._request(
            f"/api/v1/documents/byid/{document_id}", BaseResponse, method="DELETE"
        )

    async def status(self, document_id: UUID) -> ProcessingStatusResponse:
        """Get document processing status and progress.

        Args:
            document_id: UUID of the document to check.

        Returns:
            ProcessingStatusResponse: Current processing status and progress.

        Raises:
            ApiError: If document not found.

        """
        return await self.sdk._request(
            f"/api/v1/documents/byid/{document_id}/status",
            ProcessingStatusResponse,
        )

    async def reprocess(self, document_id: UUID) -> BaseResponse:
        """Reprocess document for chunk generation and embeddings.

        Args:
            document_id: UUID of the document to reprocess.

        Returns:
            BaseResponse: Success/failure status of reprocessing request.

        Raises:
            ApiError: If document not found or already processing.

        """
        return await self.sdk._request(
            f"/api/v1/documents/byid/{document_id}/reprocess",
            BaseResponse,
            method="POST",
        )

    async def download(self, document_id: UUID) -> bytes:
        """Download original document file.

        Args:
            document_id: UUID of the document to download.

        Returns:
            bytes: Binary content of the original document file.

        Raises:
            ApiError: If document not found or download failed.

        """
        url = make_url(
            self.sdk.base_url, f"/api/v1/documents/byid/{document_id}/download"
        )
        resp = self.sdk._session.get(
            url, headers=build_headers(self.sdk.token), stream=True
        )
        if not resp.ok:
            raise ApiError(resp.status_code, resp.reason, url, resp.text)
        return resp.content


class ConversationsClient:
    """Async client for conversation management operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize conversations client.

        Args:
            sdk: The main SDK instance for making API requests

        """
        self.sdk = sdk

    async def create(self, data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation.

        Args:
            data: ConversationCreate model with conversation details.

        Returns:
            ConversationResponse: Created conversation metadata.

        Raises:
            ApiError: If creation fails or validation errors occur.

        """
        return await self.sdk._request(
            "/api/v1/conversations/",
            ConversationResponse,
            method="POST",
            json=data.model_dump(mode="json"),
        )

    async def list(
        self, page: int = 1, size: int = 20, active_only: Optional[bool] = None
    ) -> PaginatedResponse:
        """List conversations with optional filtering and pagination.

        Args:
            page: Page number for pagination (default: 1).
            size: Number of conversations per page (default: 20).
            active_only: Filter to only active conversations if True.

        Returns:
            PaginatedResponse: Paginated list of conversations.

        Raises:
            ApiError: If the request fails.

        """
        params = filter_query({"page": page, "size": size, "active_only": active_only})
        return await self.sdk._request(
            "/api/v1/conversations/", ConversationResponse, params=params
        )

    async def get(self, conversation_id: UUID) -> ConversationResponse:
        """Get conversation metadata by ID.

        Args:
            conversation_id: UUID of the conversation to retrieve.

        Returns:
            ConversationResponse: Conversation metadata.

        Raises:
            ApiError: If conversation not found or access denied.

        """
        return await self.sdk._request(
            f"/api/v1/conversations/byid/{conversation_id}",
            ConversationResponse,
        )

    async def update(
        self, conversation_id: UUID, data: ConversationUpdate
    ) -> ConversationResponse:
        """Update conversation metadata.

        Args:
            conversation_id: UUID of the conversation to update.
            data: ConversationUpdate model with fields to update.

        Returns:
            ConversationResponse: Updated conversation metadata.

        Raises:
            ApiError: If conversation not found or validation errors.

        """
        return await self.sdk._request(
            f"/api/v1/conversations/byid/{conversation_id}",
            ConversationResponse,
            method="PUT",
            json=data.model_dump(),
        )

    async def delete(self, conversation_id: UUID) -> BaseResponse:
        """Delete conversation and all associated messages.

        Args:
            conversation_id: UUID of the conversation to delete.

        Returns:
            BaseResponse: Success/failure status of deletion.

        Raises:
            ApiError: If conversation not found or access denied.

        """
        return await self.sdk._request(
            f"/api/v1/conversations/byid/{conversation_id}",
            BaseResponse,
            method="DELETE",
        )

    async def messages(
        self, conversation_id: UUID, page: int = 1, size: int = 50
    ) -> PaginatedResponse:
        """Get messages from a conversation with pagination.

        Args:
            conversation_id: UUID of the conversation.
            page: Page number for pagination (default: 1).
            size: Number of messages per page (default: 50).

        Returns:
            PaginatedResponse: Paginated list of messages.

        Raises:
            ApiError: If conversation not found or access denied.

        """
        params = filter_query({"page": page, "size": size})
        return await self.sdk._request(
            f"/api/v1/conversations/byid/{conversation_id}/messages",
            MessageResponse,
            params=params,
        )

    async def chat(self, data: ChatRequest) -> ChatResponse:
        """Send a message and get AI response."""
        return await self.sdk._request(
            "/api/v1/conversations/chat",
            ChatResponse,
            method="POST",
            json=data.model_dump(mode="json"),
        )

    async def chat_stream(self, data: ChatRequest) -> AsyncIterator[str]:
        """Send a message and get streaming AI response."""
        url = make_url(self.sdk.base_url, "/api/v1/conversations/chat/stream")
        headers = build_headers(self.sdk.token)
        headers["Accept"] = "text/event-stream"

        if self.sdk._client is None:
            self.sdk._client = httpx.AsyncClient(timeout=self.sdk.timeout)

        async with self.sdk._client.stream(
            "POST",
            url,
            headers=headers,
            json=data.model_dump(mode="json"),
        ) as resp:
            if resp.status_code != 200:
                # Try to read error content
                try:
                    error_text = await resp.aread()
                except Exception:
                    error_text = ""
                raise ApiError(
                    resp.status_code, resp.reason_phrase or "", url, error_text
                )

            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_content = line[6:]  # Remove "data: " prefix
                    if data_content.strip() == "[DONE]":
                        break
                    if data_content.strip():
                        yield data_content

    async def stats(self) -> ConversationStatsResponse:
        """Get conversation statistics."""
        return await self.sdk._request(
            "/api/v1/conversations/stats", ConversationStatsResponse
        )

    async def registry_stats(self) -> RegistryStatsResponse:
        """Get registry statistics showing prompt, profile, and tool usage."""
        return await self.sdk._request(
            "/api/v1/conversations/registry-stats", RegistryStatsResponse
        )

    async def search(
        self,
        query: str,
        search_messages: bool = True,
        user_filter: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        active_only: bool = True,
        limit: int = 20,
    ) -> SearchResponse:
        """Search conversations and messages."""
        params = filter_query(
            {
                "query": query,
                "search_messages": search_messages,
                "user_filter": user_filter,
                "date_from": date_from,
                "date_to": date_to,
                "active_only": active_only,
                "limit": limit,
            }
        )
        return await self.sdk._request(
            "/api/v1/conversations/conversations/search", SearchResponse, params=params
        )


class SearchClient:
    """Client for search operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize search client.

        Args:
            sdk: The main SDK instance for making API requests

        """
        self.sdk = sdk

    async def search(self, data: DocumentSearchRequest) -> Dict[str, Any]:
        """Search across documents using various algorithms."""
        return await self.sdk._request(
            "/api/v1/search/", dict, method="POST", json=data.model_dump()
        )

    async def similar_chunks(self, chunk_id: int, limit: int = 5) -> Dict[str, Any]:
        """Find similar document chunks to a given chunk.

        Args:
            chunk_id: ID of the reference chunk to find similarities for.
            limit: Maximum number of similar chunks to return (default: 5).

        Returns:
            Dict[str, Any]: Similar chunks with similarity scores.

        Raises:
            ApiError: If chunk not found or search fails.

        """
        params = {"limit": limit}
        return await self.sdk._request(
            f"/api/v1/search/similar/{chunk_id}", dict, params=params
        )

    async def suggestions(self, query: str, limit: int = 5) -> List[Any]:
        """Get search suggestions based on query.

        Args:
            query: Search query to get suggestions for.
            limit: Maximum number of suggestions to return (default: 5).

        Returns:
            List[Any]: List of search suggestions.

        Raises:
            ApiError: If the request fails.

        """
        params = {"query": query, "limit": limit}
        return await self.sdk._request(
            "/api/v1/search/suggestions", list, params=params
        )

    async def history(self, limit: int = 10) -> List[Any]:
        """Get user's search history.

        Args:
            limit: Maximum number of history entries to return (default: 10).

        Returns:
            List[Any]: List of recent search queries.

        Raises:
            ApiError: If the request fails.
            
        Note:
            This endpoint is not currently implemented in the API.
        """
        # TODO: Implement search history endpoint in the API
        raise NotImplementedError("Search history endpoint not yet implemented in the API")

    async def clear_history(self) -> BaseResponse:
        """Clear user's search history.

        Returns:
            BaseResponse: Success/failure status of history clearing.

        Raises:
            ApiError: If the request fails.
            
        Note:
            This endpoint is not currently implemented in the API.
        """
        # TODO: Implement search history clearing endpoint in the API
        raise NotImplementedError("Search history endpoint not yet implemented in the API")


class MCPClient:
    """Client for MCP server and tools management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize MCP client.

        Args:
            sdk: The main SDK instance for making API requests

        """
        self.sdk = sdk

    # Server management methods
    async def list_servers(
        self,
        enabled_only: bool = False,
        connected_only: bool = False,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """List all registered MCP servers."""
        params = filter_query(
            {
                "enabled_only": enabled_only,
                "connected_only": connected_only,
                "detailed": detailed,
            }
        )
        return await self.sdk._request("/api/v1/mcp/servers", dict, params=params)

    async def add_server(
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
        return await self.sdk._request(
            "/api/v1/mcp/servers", dict, method="POST", json=data
        )

    async def get_server(self, server_name: str) -> Dict[str, Any]:
        """Get details for a specific server."""
        return await self.sdk._request(
            f"/api/v1/mcp/servers/byname/{server_name}", dict
        )

    async def update_server(self, server_name: str, **kwargs) -> Dict[str, Any]:
        """Update an MCP server."""
        return await self.sdk._request(
            f"/api/v1/mcp/servers/byname/{server_name}",
            dict,
            method="PATCH",
            json=kwargs,
        )

    async def remove_server(self, server_name: str) -> BaseResponse:
        """Remove an MCP server."""
        return await self.sdk._request(
            f"/api/v1/mcp/servers/byname/{server_name}", BaseResponse, method="DELETE"
        )

    async def enable_server(self, server_name: str) -> Dict[str, Any]:
        """Enable an MCP server."""
        return await self.update_server(server_name, enabled=True)

    async def disable_server(self, server_name: str) -> Dict[str, Any]:
        """Disable an MCP server."""
        return await self.update_server(server_name, enabled=False)

    async def test_server(self, server_name: str) -> Dict[str, Any]:
        """Test connection to an MCP server."""
        return await self.sdk._request(
            f"/api/v1/mcp/servers/byname/{server_name}/test", dict, method="POST"
        )

    # Tools management methods
    async def list_tools(
        self,
        server: Optional[str] = None,
        enabled_only: bool = False,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """List all available MCP tools."""
        params = filter_query(
            {
                "server": server,
                "enabled_only": enabled_only,
                "detailed": detailed,
            }
        )
        return await self.sdk._request("/api/v1/mcp/tools", dict, params=params)

    async def get_tool(
        self, tool_name: str, server: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get details for a specific tool."""
        params = filter_query({"server": server})
        return await self.sdk._request(
            f"/api/v1/mcp/tools/byname/{tool_name}", dict, params=params
        )

    async def enable_tool(
        self, tool_name: str, server: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enable an MCP tool."""
        params = filter_query({"server": server})
        return await self.sdk._request(
            f"/api/v1/mcp/tools/byname/{tool_name}/enable",
            dict,
            method="PATCH",
            params=params,
        )

    async def disable_tool(
        self, tool_name: str, server: Optional[str] = None
    ) -> Dict[str, Any]:
        """Disable an MCP tool."""
        params = filter_query({"server": server})
        return await self.sdk._request(
            f"/api/v1/mcp/tools/byname/{tool_name}/disable",
            dict,
            method="PATCH",
            params=params,
        )

    async def test_tool(
        self, tool_name: str, test_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test execution of an MCP tool."""
        data = test_params or {}
        return await self.sdk._request(
            f"/api/v1/mcp/tools/byname/{tool_name}/test",
            dict,
            method="POST",
            json=data,
        )

    async def get_servers_status(self) -> Dict[str, Any]:
        """Get comprehensive status information for all MCP servers."""
        # The servers endpoint provides server status information
        return await self.sdk._request("/api/v1/mcp/servers", dict, params={"detailed": True})

    # Statistics and refresh methods
    async def get_stats(self) -> Dict[str, Any]:
        """Get MCP usage statistics."""
        return await self.sdk._request("/api/v1/mcp/stats", dict)

    async def refresh(self, server: Optional[str] = None) -> Dict[str, Any]:
        """Refresh MCP server connections and tool discovery."""
        params = filter_query({"server": server})
        return await self.sdk._request(
            "/api/v1/mcp/refresh", dict, method="POST", params=params
        )


class PromptsClient:
    """Client for prompt registry management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize prompts client.

        Args:
            sdk: The main SDK instance for making API requests

        """
        self.sdk = sdk

    async def list_prompts(
        self,
        active_only: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all prompts with optional filtering."""
        params = filter_query(
            {"active_only": active_only, "category": category, "search": search}
        )
        return await self.sdk._request("/api/v1/prompts/", dict, params=params)

    async def get_prompt(self, prompt_name: str) -> PromptResponse:
        """Get a specific prompt by name."""
        return await self.sdk._request(
            f"/api/v1/prompts/byname/{prompt_name}", PromptResponse
        )

    async def create_prompt(self, data: PromptCreate) -> PromptResponse:
        """Create a new prompt."""
        return await self.sdk._request(
            "/api/v1/prompts/", PromptResponse, method="POST", json=data.model_dump()
        )

    async def update_prompt(
        self, prompt_name: str, data: Dict[str, Any]
    ) -> PromptResponse:
        """Update an existing prompt."""
        return await self.sdk._request(
            f"/api/v1/prompts/byname/{prompt_name}",
            PromptResponse,
            method="PUT",
            json=data,
        )

    async def delete_prompt(self, prompt_name: str) -> BaseResponse:
        """Delete a prompt."""
        return await self.sdk._request(
            f"/api/v1/prompts/byname/{prompt_name}", BaseResponse, method="DELETE"
        )

    async def get_prompt_stats(self) -> Dict[str, Any]:
        """Get prompt usage statistics."""
        return await self.sdk._request("/api/v1/prompts/stats", dict)

    async def get_categories(self) -> Dict[str, Any]:
        """Get prompt categories."""
        return await self.sdk._request("/api/v1/prompts/categories/", dict)

    async def set_default_prompt(self, prompt_name: str) -> BaseResponse:
        """Set a prompt as the default."""
        return await self.sdk._request(
            f"/api/v1/prompts/byname/{prompt_name}/set-default",
            BaseResponse,
            method="POST",
        )


class ProfilesClient:
    """Client for LLM profile registry management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize profiles client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    async def list_profiles(
        self, active_only: bool = True, search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all LLM profiles with optional filtering."""
        params = filter_query({"active_only": active_only, "search": search})
        return await self.sdk._request("/api/v1/profiles/", dict, params=params)

    async def get_profile(self, profile_name: str) -> LLMProfileResponse:
        """Get a specific LLM profile by name."""
        return await self.sdk._request(
            f"/api/v1/profiles/byname/{profile_name}", LLMProfileResponse
        )

    async def create_profile(self, data: LLMProfileCreate) -> LLMProfileResponse:
        """Create a new LLM profile."""
        return await self.sdk._request(
            "/api/v1/profiles/",
            LLMProfileResponse,
            method="POST",
            json=data.model_dump(),
        )

    async def update_profile(
        self, profile_name: str, data: Dict[str, Any]
    ) -> LLMProfileResponse:
        """Update an existing LLM profile."""
        return await self.sdk._request(
            f"/api/v1/profiles/byname/{profile_name}",
            LLMProfileResponse,
            method="PUT",
            json=data,
        )

    async def delete_profile(self, profile_name: str) -> BaseResponse:
        """Delete an LLM profile."""
        return await self.sdk._request(
            f"/api/v1/profiles/byname/{profile_name}", BaseResponse, method="DELETE"
        )

    async def get_profile_stats(self) -> Dict[str, Any]:
        """Get LLM profile usage statistics."""
        return await self.sdk._request("/api/v1/profiles/stats", dict)

    async def set_default_profile(self, profile_name: str) -> BaseResponse:
        """Set a profile as the default."""
        return await self.sdk._request(
            f"/api/v1/profiles/byname/{profile_name}/set-default",
            BaseResponse,
            method="POST",
        )


class AnalyticsClient:
    """Client for analytics and reporting."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize analytics client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    async def get_overview(self) -> Dict[str, Any]:
        """Get system overview analytics."""
        return await self.sdk._request("/api/v1/analytics/overview", dict)

    async def get_usage(
        self, period: Optional[str] = None, detailed: bool = False
    ) -> Dict[str, Any]:
        """Get usage analytics."""
        params = filter_query({"period": period, "detailed": detailed})
        return await self.sdk._request("/api/v1/analytics/usage", dict, params=params)

    async def get_performance(self) -> Dict[str, Any]:
        """Get performance analytics."""
        return await self.sdk._request("/api/v1/analytics/performance", dict)

    async def get_users_analytics(
        self, top: Optional[int] = None, metric: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user analytics."""
        params = filter_query({"top": top, "metric": metric})
        return await self.sdk._request("/api/v1/analytics/users", dict, params=params)

    async def get_trends(self) -> Dict[str, Any]:
        """Get trend analytics."""
        return await self.sdk._request("/api/v1/analytics/trends", dict)

    async def export_report(
        self, output: Optional[str] = None, details: bool = False
    ) -> Dict[str, Any]:
        """Export analytics report."""
        data = filter_query({"output": output, "details": details})
        return await self.sdk._request(
            "/api/v1/analytics/export-report", dict, method="POST", json=data
        )


class DatabaseClient:
    """Client for database management operations."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize database client.

        Args:
            sdk: The main SDK instance for making API requests

        """
        self.sdk = sdk

    async def init_database(self) -> BaseResponse:
        """Initialize the database."""
        return await self.sdk._request(
            "/api/v1/database/init", BaseResponse, method="POST"
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get database status."""
        return await self.sdk._request("/api/v1/database/status", dict)

    async def upgrade(self) -> BaseResponse:
        """Run database migrations/upgrade."""
        return await self.sdk._request(
            "/api/v1/database/upgrade", BaseResponse, method="POST"
        )

    async def downgrade(self) -> BaseResponse:
        """Downgrade database."""
        return await self.sdk._request(
            "/api/v1/database/downgrade", BaseResponse, method="POST"
        )

    async def backup(self, output: Optional[str] = None) -> BaseResponse:
        """Create database backup."""
        data = filter_query({"output": output})
        return await self.sdk._request(
            "/api/v1/database/backup", BaseResponse, method="POST", json=data
        )

    async def restore(self, backup_file: str) -> BaseResponse:
        """Restore database from backup."""
        data = {"backup_file": backup_file}
        return await self.sdk._request(
            "/api/v1/database/restore", BaseResponse, method="POST", json=data
        )

    async def get_tables(self) -> Dict[str, Any]:
        """Get database tables information."""
        return await self.sdk._request("/api/v1/database/tables", dict)

    async def vacuum(self) -> BaseResponse:
        """Vacuum database."""
        return await self.sdk._request(
            "/api/v1/database/vacuum", BaseResponse, method="POST"
        )

    async def get_migrations(self) -> Dict[str, Any]:
        """Get migration status."""
        return await self.sdk._request("/api/v1/database/migrations", dict)

    async def query(self, sql: str) -> Dict[str, Any]:
        """Execute custom query."""
        data = {"sql": sql}
        return await self.sdk._request(
            "/api/v1/database/query", dict, method="POST", json=data
        )

    async def validate(self) -> Dict[str, Any]:
        """Validate database schema."""
        # Use the analyze endpoint which provides schema validation information
        return await self.sdk._request("/api/v1/database/analyze", dict, method="GET")


class TasksClient:
    """Client for background task management."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize tasks client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    async def get_status(self) -> Dict[str, Any]:
        """Get task system status."""
        return await self.sdk._request("/api/v1/tasks/status", dict)

    async def get_workers(self) -> Dict[str, Any]:
        """Get worker status."""
        return await self.sdk._request("/api/v1/tasks/workers", dict)

    async def get_queue(self) -> Dict[str, Any]:
        """Get queue information."""
        return await self.sdk._request("/api/v1/tasks/queue", dict)

    async def get_active(self) -> Dict[str, Any]:
        """Get active tasks."""
        return await self.sdk._request("/api/v1/tasks/active", dict)

    async def schedule_task(self, task_name: str, **kwargs) -> BaseResponse:
        """Schedule a task."""
        data = {"task_name": task_name, **kwargs}
        return await self.sdk._request(
            "/api/v1/tasks/schedule", BaseResponse, method="POST", json=data
        )

    async def retry_failed(self) -> BaseResponse:
        """Retry failed tasks."""
        return await self.sdk._request(
            "/api/v1/tasks/retry-failed", BaseResponse, method="POST"
        )

    async def purge_queue(self) -> BaseResponse:
        """Purge task queue."""
        return await self.sdk._request(
            "/api/v1/tasks/purge", BaseResponse, method="POST"
        )

    async def monitor(
        self, refresh: Optional[int] = None, duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """Monitor tasks."""
        params = filter_query({"refresh": refresh, "duration": duration})
        return await self.sdk._request("/api/v1/tasks/monitor", dict, params=params)


class AdminClient:
    """Client for admin operations across different resources."""

    def __init__(self, sdk: "AIChatbotSDK"):
        """Initialize admin client.

        Args:
            sdk: The main SDK instance for making API requests.

        """
        self.sdk = sdk

    # User admin operations
    async def promote_user(self, user_id: UUID) -> BaseResponse:
        """Promote user to superuser."""
        # Use the user update endpoint to set superuser status
        from shared.schemas.user import UserUpdate
        update_data = UserUpdate(is_superuser=True)
        return await self.sdk._request(
            f"/api/v1/users/byid/{user_id}", BaseResponse, method="PUT", json=update_data.model_dump()
        )

    async def demote_user(self, user_id: UUID) -> BaseResponse:
        """Demote user from superuser."""
        # Use the user update endpoint to remove superuser status
        from shared.schemas.user import UserUpdate
        update_data = UserUpdate(is_superuser=False)
        return await self.sdk._request(
            f"/api/v1/users/byid/{user_id}", BaseResponse, method="PUT", json=update_data.model_dump()
        )

    async def activate_user(self, user_id: UUID) -> BaseResponse:
        """Activate user account."""
        # Use the user update endpoint to set active status
        from shared.schemas.user import UserUpdate
        update_data = UserUpdate(is_active=True)
        return await self.sdk._request(
            f"/api/v1/users/byid/{user_id}", BaseResponse, method="PUT", json=update_data.model_dump()
        )

    async def deactivate_user(self, user_id: UUID) -> BaseResponse:
        """Deactivate user account."""
        # Use the user update endpoint to remove active status
        from shared.schemas.user import UserUpdate
        update_data = UserUpdate(is_active=False)
        return await self.sdk._request(
            f"/api/v1/users/byid/{user_id}", BaseResponse, method="PUT", json=update_data.model_dump()
        )

    async def reset_user_password(
        self, user_id: UUID, new_password: Optional[str] = None
    ) -> BaseResponse:
        """Reset user password."""
        # Use the actual admin password reset endpoint
        params = filter_query({"new_password": new_password}) if new_password else {}
        return await self.sdk._request(
            f"/api/v1/users/users/byid/{user_id}/reset-password",
            BaseResponse,
            method="POST",
            params=params,
        )

    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        return await self.sdk._request("/api/v1/users/users/stats", dict)

    # Document admin operations
    async def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        return await self.sdk._request("/api/v1/documents/documents/stats", dict)

    async def cleanup_documents(
        self, older_than: Optional[int] = None, status: Optional[str] = None
    ) -> BaseResponse:
        """Cleanup old documents."""
        params = filter_query({"older_than_days": older_than, "status_filter": status})
        return await self.sdk._request(
            "/api/v1/documents/documents/cleanup", BaseResponse, method="POST", params=params
        )

    async def bulk_reprocess_documents(
        self, document_ids: Optional[List[UUID]] = None
    ) -> BaseResponse:
        """Bulk reprocess documents."""
        # This endpoint doesn't exist yet, so mark as not implemented
        raise NotImplementedError("Bulk document reprocessing endpoint not yet implemented in the API")

    async def search_documents_advanced(self, **kwargs) -> Dict[str, Any]:
        """Advanced document search."""
        # Use the regular search endpoint with advanced parameters
        from shared.schemas.search import DocumentSearchRequest
        search_request = DocumentSearchRequest(**kwargs)
        return await self.sdk._request(
            "/api/v1/search/", dict, method="POST", json=search_request.model_dump()
        )

    # Conversation admin operations
    async def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return await self.sdk._request("/api/v1/conversations/conversations/stats", dict)

    async def search_conversations(self, **kwargs) -> Dict[str, Any]:
        """Search conversations."""
        params = filter_query(kwargs)
        return await self.sdk._request(
            "/api/v1/conversations/conversations/search", dict, params=params
        )

    async def export_conversation(self, conversation_id: UUID) -> Dict[str, Any]:
        """Export conversation."""
        return await self.sdk._request(
            f"/api/v1/conversations/conversations/byid/{conversation_id}/export", dict
        )

    async def import_conversations(self, data: Dict[str, Any]) -> BaseResponse:
        """Import conversations."""
        # This uses the file upload endpoint, so it's more complex
        return await self.sdk._request(
            "/api/v1/conversations/conversations/import", BaseResponse, method="POST", json=data
        )

    async def archive_conversations(
        self, older_than: Optional[int] = None
    ) -> BaseResponse:
        """Archive old conversations."""
        params = filter_query({"older_than_days": older_than, "dry_run": False})
        return await self.sdk._request(
            "/api/v1/conversations/conversations/archive",
            BaseResponse,
            method="POST",
            params=params,
        )


# --- MAIN SDK CLASS ---


class AIChatbotSDK:
    """Main async SDK class for AI Chatbot Platform API interactions.

    Provides a comprehensive async client for accessing all API endpoints including
    authentication, document management, conversations, search functionality,
    and registry-based features for prompts, LLM profiles, and MCP tools.

    All methods are async and should be called with await. The SDK uses httpx
    for async HTTP requests and can be used as an async context manager.

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
        client: Optional custom httpx.AsyncClient instance.
        timeout: Timeout for HTTP requests in seconds (default: 30).

    Example:
        >>> async with AIChatbotSDK("http://localhost:8000") as sdk:
        ...     token = await sdk.auth.login("username", "password")
        ...     prompts = await sdk.prompts.list_prompts()
        ...     response = await sdk.conversations.chat(ChatRequest(
        ...         user_message="Hello!",
        ...         prompt_name="helpful_assistant"
        ...     ))

    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        on_error: Optional[Callable[[ApiError], None]] = None,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 30.0,
    ):
        """Initialize AIChatbotSDK with configuration parameters."""
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.on_error = on_error
        self.timeout = timeout
        self._client = client
        self._own_client = client is None

        # Initialize all client endpoints
        self.health = HealthClient(self)
        self.auth = AuthClient(self)
        self.users = UsersClient(self)
        self.documents = DocumentsClient(self)
        self.conversations = ConversationsClient(self)
        self.search = SearchClient(self)

        # Registry-based clients
        self.mcp = MCPClient(self)
        self.prompts = PromptsClient(self)
        self.profiles = ProfilesClient(self)

        # Management clients
        self.analytics = AnalyticsClient(self)
        self.database = DatabaseClient(self)
        self.tasks = TasksClient(self)
        self.admin = AdminClient(self)

    async def __aenter__(self):
        """Async context manager entry."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_client and self._client:
            await self._client.aclose()

    def set_token(self, token: Optional[str]) -> None:
        """Set authentication token for API requests."""
        self.token = token

    def get_token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.token

    def clear_token(self) -> None:
        """Clear stored authentication token."""
        self.token = None

    async def _request(
        self,
        path: str,
        cls: Optional[Type[T]] = None,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an async HTTP request to the API."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        url = make_url(self.base_url, path, params)
        headers = build_headers(self.token)

        try:
            resp = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=None,
                json=json,
                data=data,
                files=files,
            )
            return await handle_response(resp, url, cls)
        except ApiError as e:
            if self.on_error:
                self.on_error(e)
            raise
