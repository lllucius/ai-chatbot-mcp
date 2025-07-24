"Client SDK for ai_chatbot_sdk functionality."

from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID
import requests
from pydantic import BaseModel


class ApiError(Exception):
    "Custom exception for error handling."

    def __init__(self, status: int, reason: str, url: str, body: Any):
        "Initialize class instance."
        super().__init__(f"HTTP {status} {reason}: {body}")
        self.status = status
        self.reason = reason
        self.url = url
        self.body = body


T = TypeVar("T")


class BaseResponse(BaseModel):
    "BaseResponse schema for data validation and serialization."

    success: bool
    message: str
    timestamp: Optional[str] = None


class Token(BaseModel):
    "Token class for specialized functionality."

    access_token: str
    expires_in: int
    token_type: Optional[str] = None


class UserResponse(BaseModel):
    "UserResponse schema for data validation and serialization."

    username: str
    email: str
    id: str
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str
    full_name: Optional[str] = None


class RegisterRequest(BaseModel):
    "RegisterRequest schema for data validation and serialization."

    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    "LoginRequest schema for data validation and serialization."

    username: str
    password: str


class PasswordResetRequest(BaseModel):
    "PasswordResetRequest schema for data validation and serialization."

    email: str


class PasswordResetConfirm(BaseModel):
    "PasswordResetConfirm class for specialized functionality."

    token: str
    new_password: str


class UserUpdate(BaseModel):
    "UserUpdate class for specialized functionality."

    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    "UserPasswordUpdate class for specialized functionality."

    current_password: str
    new_password: str


class PaginationParams(BaseModel):
    "PaginationParams class for specialized functionality."

    page: int
    per_page: int
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"


class PaginatedResponse(BaseModel, Generic[T]):
    "PaginatedResponse schema for data validation and serialization."

    success: bool
    message: str
    items: List[Any]
    pagination: PaginationParams
    timestamp: Optional[str] = None


class DocumentResponse(BaseModel):
    "DocumentResponse schema for data validation and serialization."

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
    metainfo: Optional[Dict[(str, Any)]] = None


class DocumentUploadResponse(BaseResponse):
    "DocumentUploadResponse schema for data validation and serialization."

    document: DocumentResponse
    processing_started: bool
    estimated_completion: Optional[str] = None


class DocumentUpdate(BaseModel):
    "DocumentUpdate class for specialized functionality."

    title: Optional[str] = None
    metainfo: Optional[Dict[(str, Any)]] = None


class ConversationResponse(BaseModel):
    "ConversationResponse schema for data validation and serialization."

    title: str
    is_active: bool
    id: UUID
    user_id: UUID
    message_count: int
    created_at: str
    updated_at: str
    last_message_at: Optional[datetime] = None
    metainfo: Optional[Dict[(str, Any)]] = None


class ConversationCreate(BaseModel):
    "ConversationCreate class for specialized functionality."

    title: str
    is_active: Optional[bool] = True
    metainfo: Optional[Dict[(str, Any)]] = None


class ConversationUpdate(BaseModel):
    "ConversationUpdate class for specialized functionality."

    title: Optional[str] = None
    is_active: Optional[bool] = None
    metainfo: Optional[Dict[(str, Any)]] = None


class MessageResponse(BaseModel):
    "MessageResponse schema for data validation and serialization."

    role: str
    content: str
    id: UUID
    conversation_id: UUID
    token_count: int
    created_at: str
    tool_calls: Optional[Dict[(str, Any)]] = None
    tool_call_results: Optional[Dict[(str, Any)]] = None
    metainfo: Optional[Dict[(str, Any)]] = None


class ProcessingStatusResponse(BaseResponse):
    "ProcessingStatusResponse schema for data validation and serialization."

    document_id: UUID
    status: str
    progress: float
    chunks_processed: int
    total_chunks: int
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class DocumentSearchRequest(BaseModel):
    "DocumentSearchRequest schema for data validation and serialization."

    page: Optional[int] = 1
    per_page: Optional[int] = 10
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    q: Optional[str] = None
    filters: Optional[Dict[(str, Any)]] = None
    document_ids: Optional[List[int]] = None
    file_types: Optional[List[str]] = None


class ChatRequest(BaseModel):
    "ChatRequest schema for data validation and serialization."

    user_message: str
    conversation_id: Optional[UUID] = None
    conversation_title: Optional[str] = None
    use_rag: Optional[bool] = True
    use_tools: Optional[bool] = True
    rag_documents: Optional[List[UUID]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7


class ChatResponse(BaseResponse):
    "ChatResponse schema for data validation and serialization."

    ai_message: MessageResponse
    conversation: ConversationResponse
    response_time_ms: float
    usage: Optional[Dict[(str, Any)]] = None
    rag_context: Optional[List[Dict[(str, Any)]]] = None
    tool_calls_made: Optional[List[Dict[(str, Any)]]] = None


def filter_query(query: Optional[Dict[(str, Any)]]) -> Dict[(str, Any)]:
    "Filter Query operation."
    return {k: v for (k, v) in (query or {}).items() if (v is not None)}


def handle_response(
    resp: requests.Response, url: str, cls: Optional[Type[T]] = None
) -> Any:
    "Handle Response operation."
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
) -> Dict[(str, str)]:
    "Build Headers operation."
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def make_url(base: str, path: str, query: Optional[Dict[(str, Any)]] = None) -> str:
    "Make Url operation."
    url = base.rstrip("/") + path
    q = filter_query(query)
    if q:
        from urllib.parse import urlencode

        url += ("?" if ("?" not in url) else "&") + urlencode(q, doseq=True)
    return url


def fetch_all_pages(
    fetch_page: Callable[([int, int], Any)], per_page: int = 50
) -> List[Any]:
    "Fetch All Pages operation."
    items = []
    page = 1
    while True:
        resp = fetch_page(page, per_page)
        items.extend(resp.items)
        if len(resp.items) < per_page:
            break
        page += 1
    return items


class HealthClient:
    "Health client for external service communication."

    def __init__(self, sdk: "AIChatbotSDK"):
        "Initialize class instance."
        self.sdk = sdk

    def basic(self) -> BaseResponse:
        "Basic operation."
        return self.sdk._request("/api/v1/health/", BaseResponse)

    def detailed(self) -> Dict[(str, Any)]:
        "Detailed operation."
        return self.sdk._request("/api/v1/health/detailed")

    def database(self) -> Dict[(str, Any)]:
        "Database operation."
        return self.sdk._request("/api/v1/health/database")

    def services(self) -> Dict[(str, Any)]:
        "Services operation."
        return self.sdk._request("/api/v1/health/services")

    def metrics(self) -> Dict[(str, Any)]:
        "Metrics operation."
        return self.sdk._request("/api/v1/health/metrics")

    def readiness(self) -> Dict[(str, Any)]:
        "Readiness operation."
        return self.sdk._request("/api/v1/health/readiness")

    def liveness(self) -> Dict[(str, Any)]:
        "Liveness operation."
        return self.sdk._request("/api/v1/health/liveness")


class AuthClient:
    "Auth client for external service communication."

    def __init__(self, sdk: "AIChatbotSDK"):
        "Initialize class instance."
        self.sdk = sdk

    def register(self, data: RegisterRequest) -> UserResponse:
        "Register operation."
        return self.sdk._request(
            "/api/v1/auth/register", UserResponse, method="POST", json=data.dict()
        )

    def login(self, username: str, password: str) -> Token:
        "Login operation."
        data = {"username": username, "password": password}
        token = self.sdk._request("/api/v1/auth/login", Token, method="POST", json=data)
        self.sdk.set_token(token.access_token)
        return token

    def me(self) -> UserResponse:
        "Me operation."
        return self.sdk._request("/api/v1/auth/me", UserResponse)

    def logout(self) -> BaseResponse:
        "Logout operation."
        return self.sdk._request("/api/v1/auth/logout", BaseResponse, method="POST")

    def refresh(self) -> Token:
        "Refresh operation."
        return self.sdk._request("/api/v1/auth/refresh", Token, method="POST")

    def request_password_reset(self, data: PasswordResetRequest) -> BaseResponse:
        "Request Password Reset operation."
        return self.sdk._request(
            "/api/v1/auth/password-reset", BaseResponse, method="POST", json=data.dict()
        )

    def confirm_password_reset(self, data: PasswordResetConfirm) -> BaseResponse:
        "Confirm Password Reset operation."
        return self.sdk._request(
            "/api/v1/auth/password-reset/confirm",
            BaseResponse,
            method="POST",
            json=data.dict(),
        )


class UsersClient:
    "Users client for external service communication."

    def __init__(self, sdk: "AIChatbotSDK"):
        "Initialize class instance."
        self.sdk = sdk

    def me(self) -> UserResponse:
        "Me operation."
        return self.sdk._request("/api/v1/users/me", UserResponse)

    def update_me(self, data: UserUpdate) -> UserResponse:
        "Update existing me."
        return self.sdk._request(
            "/api/v1/users/me", UserResponse, method="PUT", json=data.dict()
        )

    def change_password(self, data: UserPasswordUpdate) -> BaseResponse:
        "Change Password operation."
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
        "List operation."
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
        "Get operation."
        return self.sdk._request(f"/api/v1/users/{user_id}", UserResponse)

    def update(self, user_id: int, data: UserUpdate) -> UserResponse:
        "Update operation."
        return self.sdk._request(
            f"/api/v1/users/{user_id}", UserResponse, method="PUT", json=data.dict()
        )

    def delete(self, user_id: int) -> BaseResponse:
        "Delete operation."
        return self.sdk._request(
            f"/api/v1/users/{user_id}", BaseResponse, method="DELETE"
        )


class DocumentsClient:
    "Documents client for external service communication."

    def __init__(self, sdk: "AIChatbotSDK"):
        "Initialize class instance."
        self.sdk = sdk

    def upload(self, file, title: Optional[str] = None) -> DocumentUploadResponse:
        "Upload operation."
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
        "List operation."
        params = filter_query(
            {"page": page, "size": size, "file_type": file_type, "status": status}
        )
        return self.sdk._request("/api/v1/documents/", DocumentResponse, params=params)

    def get(self, document_id: int) -> DocumentResponse:
        "Get operation."
        return self.sdk._request(f"/api/v1/documents/{document_id}", DocumentResponse)

    def update(self, document_id: int, data: DocumentUpdate) -> DocumentResponse:
        "Update operation."
        return self.sdk._request(
            f"/api/v1/documents/{document_id}",
            DocumentResponse,
            method="PUT",
            json=data.dict(),
        )

    def delete(self, document_id: int) -> BaseResponse:
        "Delete operation."
        return self.sdk._request(
            f"/api/v1/documents/{document_id}", BaseResponse, method="DELETE"
        )

    def status(self, document_id: int) -> ProcessingStatusResponse:
        "Status operation."
        return self.sdk._request(
            f"/api/v1/documents/{document_id}/status", ProcessingStatusResponse
        )

    def reprocess(self, document_id: int) -> BaseResponse:
        "Reprocess operation."
        return self.sdk._request(
            f"/api/v1/documents/{document_id}/reprocess", BaseResponse, method="POST"
        )

    def download(self, document_id: int) -> bytes:
        "Download operation."
        url = make_url(self.sdk.base_url, f"/api/v1/documents/{document_id}/download")
        resp = self.sdk._session.get(
            url, headers=build_headers(self.sdk.token), stream=True
        )
        if not resp.ok:
            raise ApiError(resp.status_code, resp.reason, url, resp.text)
        return resp.content


class ConversationsClient:
    "Conversations client for external service communication."

    def __init__(self, sdk: "AIChatbotSDK"):
        "Initialize class instance."
        self.sdk = sdk

    def create(self, data: ConversationCreate) -> ConversationResponse:
        "Create operation."
        return self.sdk._request(
            "/api/v1/conversations/",
            ConversationResponse,
            method="POST",
            json=data.model_dump(mode="json"),
        )

    def list(
        self, page: int = 1, size: int = 20, active_only: Optional[bool] = None
    ) -> PaginatedResponse:
        "List operation."
        params = filter_query({"page": page, "size": size, "active_only": active_only})
        return self.sdk._request(
            "/api/v1/conversations/", ConversationResponse, params=params
        )

    def get(self, conversation_id: int) -> ConversationResponse:
        "Get operation."
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}", ConversationResponse
        )

    def update(
        self, conversation_id: int, data: ConversationUpdate
    ) -> ConversationResponse:
        "Update operation."
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}",
            ConversationResponse,
            method="PUT",
            json=data.dict(),
        )

    def delete(self, conversation_id: int) -> BaseResponse:
        "Delete operation."
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}", BaseResponse, method="DELETE"
        )

    def messages(
        self, conversation_id: int, page: int = 1, size: int = 50
    ) -> PaginatedResponse:
        "Messages operation."
        params = filter_query({"page": page, "size": size})
        return self.sdk._request(
            f"/api/v1/conversations/{conversation_id}/messages",
            MessageResponse,
            params=params,
        )

    def chat(self, data: ChatRequest) -> ChatResponse:
        "Chat operation."
        return self.sdk._request(
            "/api/v1/conversations/chat",
            ChatResponse,
            method="POST",
            json=data.model_dump(mode="json"),
        )

    def stats(self) -> Dict[(str, Any)]:
        "Stats operation."
        return self.sdk._request("/api/v1/conversations/stats")


class SearchClient:
    "Search client for external service communication."

    def __init__(self, sdk: "AIChatbotSDK"):
        "Initialize class instance."
        self.sdk = sdk

    def search(self, data: DocumentSearchRequest) -> Dict[(str, Any)]:
        "Search operation."
        return self.sdk._request(
            "/api/v1/search/", dict, method="POST", json=data.dict()
        )

    def similar_chunks(self, chunk_id: int, limit: int = 5) -> Dict[(str, Any)]:
        "Similar Chunks operation."
        params = {"limit": limit}
        return self.sdk._request(
            f"/api/v1/search/similar/{chunk_id}", dict, params=params
        )

    def suggestions(self, query: str, limit: int = 5) -> List[Any]:
        "Suggestions operation."
        params = {"query": query, "limit": limit}
        return self.sdk._request("/api/v1/search/suggestions", list, params=params)

    def history(self, limit: int = 10) -> List[Any]:
        "History operation."
        params = {"limit": limit}
        return self.sdk._request("/api/v1/search/history", list, params=params)

    def clear_history(self) -> BaseResponse:
        "Clear History operation."
        return self.sdk._request(
            "/api/v1/search/history", BaseResponse, method="DELETE"
        )


class AIChatbotSDK:
    "AIChatbotSDK class for specialized functionality."

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        on_error: Optional[Callable[([ApiError], None)]] = None,
        session: Optional[requests.Session] = None,
    ):
        "Initialize class instance."
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
        "Set Token operation."
        self.token = token

    def get_token(self) -> Optional[str]:
        "Get token data."
        return self.token

    def clear_token(self) -> None:
        "Clear Token operation."
        self.token = None

    def _request(
        self,
        path: str,
        cls: Optional[Type[T]] = None,
        method: str = "GET",
        params: Optional[Dict[(str, Any)]] = None,
        json: Optional[Dict[(str, Any)]] = None,
        data: Optional[Dict[(str, Any)]] = None,
        files: Optional[Dict[(str, Any)]] = None,
    ) -> Any:
        "Request operation."
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
