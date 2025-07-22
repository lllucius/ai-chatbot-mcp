"""
AI Chatbot SDK - Python client library for the AI Chatbot Platform.

This module provides a comprehensive SDK for interacting with the AI Chatbot Platform,
including authentication, document management, conversation handling, and search capabilities.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID
from datetime import datetime

import requests
from pydantic import BaseModel

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

# --- SCHEMA MODELS ---


class BaseResponse(BaseModel):
    """Base response model for API responses."""
    success: bool
    message: str
    timestamp: Optional[str] = None


class Token(BaseModel):
    """Authentication token response model."""
    access_token: str
    expires_in: int
    token_type: Optional[str] = None


class UserResponse(BaseModel):
    """User profile response model."""
    username: str
    email: str
    id: str
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str
    full_name: Optional[str] = None


class RegisterRequest(BaseModel):
    """User registration request model."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request model."""
    username: str
    password: str


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
    """Document metadata response model."""
    id: int
    title: str
    filename: str
    file_type: str
    file_size: int
    processing_status: str
    owner_id: int
    chunk_count: int
    created_at: str
    updated_at: str
    mime_type: Optional[str] = None
    metainfo: Optional[Dict[str, Any]] = None


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
    """Conversation metadata response model."""
    title: str
    is_active: bool
    id: UUID
    user_id: UUID
    message_count: int
    created_at: str
    updated_at: str
    last_message_at: Optional[datetime] = None
    metainfo: Optional[Dict[str, Any]] = None


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
    """Chat message response model."""
    role: str
    content: str
    id: UUID
    conversation_id: UUID
    token_count: int
    created_at: str
    tool_calls: Optional[Dict[str, Any]] = None
    tool_call_results: Optional[Dict[str, Any]] = None
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


class DocumentSearchRequest(BaseModel):
    """Document search request model."""
    page: Optional[int] = 1
    per_page: Optional[int] = 10
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    q: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[int]] = None
    file_types: Optional[List[str]] = None


class ChatRequest(BaseModel):
    """Chat message request model."""
    user_message: str
    conversation_id: Optional[UUID] = None
    conversation_title: Optional[str] = None
    use_rag: Optional[bool] = True
    use_tools: Optional[bool] = True
    rag_documents: Optional[List[UUID]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7


class ChatResponse(BaseResponse):
    """Chat response model with AI message."""
    ai_message: MessageResponse
    conversation: ConversationResponse
    response_time_ms: float
    usage: Optional[Dict[str, Any]] = None
    rag_context: Optional[List[Dict[str, Any]]] = None
    tool_calls_made: Optional[List[Dict[str, Any]]] = None


# --- Helper Functions ---


def filter_query(query: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Filter out None values from query parameters."""
    return {k: v for k, v in (query or {}).items() if v is not None}


def handle_response(
    resp: requests.Response, url: str, cls: Optional[Type[T]] = None
) -> Any:
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


def fetch_all_pages(
    fetch_page: Callable[[int, int], Any], per_page: int = 50
) -> List[Any]:
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
            json=data.dict(),
        )

    def login(self, username: str, password: str) -> Token:
        data = {"username": username, "password": password}
        token = self.sdk._request(
            "/api/v1/auth/login", Token, method="POST", json=data
        )
        self.sdk.set_token(token.access_token)
        return token

    def me(self) -> UserResponse:
        return self.sdk._request("/api/v1/auth/me", UserResponse)

    def logout(self) -> BaseResponse:
        """Logout current user and invalidate token."""
        return self.sdk._request(
            "/api/v1/auth/logout", BaseResponse, method="POST"
        )

    def refresh(self) -> Token:
        """Refresh authentication token."""
        return self.sdk._request("/api/v1/auth/refresh", Token, method="POST")

    def request_password_reset(self, data: PasswordResetRequest) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/auth/password-reset",
            BaseResponse,
            method="POST",
            json=data.dict(),
        )

    def confirm_password_reset(self, data: PasswordResetConfirm) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/auth/password-reset/confirm",
            BaseResponse,
            method="POST",
            json=data.dict(),
        )


class UsersClient:
    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def me(self) -> UserResponse:
        return self.sdk._request("/api/v1/users/me", UserResponse)

    def update_me(self, data: UserUpdate) -> UserResponse:
        return self.sdk._request(
            "/api/v1/users/me", UserResponse, method="PUT", json=data.dict()
        )

    def change_password(self, data: UserPasswordUpdate) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/users/me/change-password",
            BaseResponse,
            method="POST",
            json=data.dict(),
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

    def get(self, user_id: int) -> UserResponse:
        return self.sdk._request(f"/api/v1/users/{user_id}", UserResponse)

    def update(self, user_id: int, data: UserUpdate) -> UserResponse:
        return self.sdk._request(
            f"/api/v1/users/{user_id}",
            UserResponse,
            method="PUT",
            json=data.dict(),
        )

    def delete(self, user_id: int) -> BaseResponse:
        return self.sdk._request(
            f"/api/v1/users/{user_id}", BaseResponse, method="DELETE"
        )


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
        return self.sdk._request(
            "/api/v1/documents/", DocumentResponse, params=params
        )

    def get(self, document_id: int) -> DocumentResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}", DocumentResponse
        )

    def update(self, document_id: int, data: DocumentUpdate) -> DocumentResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}",
            DocumentResponse,
            method="PUT",
            json=data.dict(),
        )

    def delete(self, document_id: int) -> BaseResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}", BaseResponse, method="DELETE"
        )

    def status(self, document_id: int) -> ProcessingStatusResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}/status",
            ProcessingStatusResponse,
        )

    def reprocess(self, document_id: int) -> BaseResponse:
        return self.sdk._request(
            f"/api/v1/documents/{document_id}/reprocess",
            BaseResponse,
            method="POST",
        )

    def download(self, document_id: int) -> bytes:
        url = make_url(
            self.sdk.base_url, f"/api/v1/documents/{document_id}/download"
        )
        resp = self.sdk._session.get(
            url, headers=build_headers(self.sdk.token), stream=True
        )
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
        return self.sdk._request(
            "/api/v1/conversations/", ConversationResponse, params=params
        )

    def get(self, conversation_id: int) -> ConversationResponse:
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            ConversationResponse,
        )

    def update(
        self, conversation_id: int, data: ConversationUpdate
    ) -> ConversationResponse:
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            ConversationResponse,
            method="PUT",
            json=data.dict(),
        )

    def delete(self, conversation_id: int) -> BaseResponse:
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            BaseResponse,
            method="DELETE",
        )

    def messages(
        self, conversation_id: int, page: int = 1, size: int = 50
    ) -> PaginatedResponse:
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

    def stats(self) -> Dict[str, Any]:
        return self.sdk._request("/api/v1/conversations/stats")


class SearchClient:
    def __init__(self, sdk: "AIChatbotSDK"):
        self.sdk = sdk

    def search(self, data: DocumentSearchRequest) -> Dict[str, Any]:
        """Search across documents using various algorithms."""
        return self.sdk._request(
            "/api/v1/search/", dict, method="POST", json=data.dict()
        )

    def similar_chunks(self, chunk_id: int, limit: int = 5) -> Dict[str, Any]:
        params = {"limit": limit}
        return self.sdk._request(
            f"/api/v1/search/similar/{chunk_id}", dict, params=params
        )

    def suggestions(self, query: str, limit: int = 5) -> List[Any]:
        params = {"query": query, "limit": limit}
        return self.sdk._request(
            "/api/v1/search/suggestions", list, params=params
        )

    def history(self, limit: int = 10) -> List[Any]:
        params = {"limit": limit}
        return self.sdk._request("/api/v1/search/history", list, params=params)

    def clear_history(self) -> BaseResponse:
        return self.sdk._request(
            "/api/v1/search/history", BaseResponse, method="DELETE"
        )


# --- MAIN SDK CLASS ---


class AIChatbotSDK:
    """
    Main SDK class for AI Chatbot Platform API interactions.
    
    Provides a comprehensive client for accessing all API endpoints including
    authentication, document management, conversations, and search functionality.
    
    Args:
        base_url: Base URL of the AI Chatbot API.
        token: Optional authentication token.
        on_error: Optional error handler callback.
        session: Optional custom requests session.
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

        self.health = HealthClient(self)
        self.auth = AuthClient(self)
        self.users = UsersClient(self)
        self.documents = DocumentsClient(self)
        self.conversations = ConversationsClient(self)
        self.search = SearchClient(self)

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
