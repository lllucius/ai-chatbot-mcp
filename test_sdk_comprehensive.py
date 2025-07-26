#!/usr/bin/env python3
"""
Comprehensive tests for the AI Chatbot SDK.

This test suite validates all SDK functions and ensures proper pydantic
validation and API integration.
"""

import json
import tempfile
from io import BytesIO
from typing import Dict, Any
from unittest.mock import Mock, patch
import uuid

import pytest
import requests
from client.ai_chatbot_sdk import (
    AIChatbotSDK,
    ApiError,
    ChatRequest,
    ConversationCreate,
    DocumentSearchRequest,
    LLMProfileCreate,
    LoginRequest,
    PromptCreate,
    RegisterRequest,
    UserUpdate,
)


class TestSDKInitialization:
    """Test SDK initialization and configuration."""

    def test_sdk_init_basic(self):
        """Test basic SDK initialization."""
        sdk = AIChatbotSDK("http://localhost:8000")
        
        assert sdk.base_url == "http://localhost:8000"
        assert sdk.token is None
        assert sdk._session is not None
        
        # Check all clients are initialized
        assert sdk.health is not None
        assert sdk.auth is not None
        assert sdk.users is not None
        assert sdk.documents is not None
        assert sdk.conversations is not None
        assert sdk.search is not None
        assert sdk.tools is not None
        assert sdk.prompts is not None
        assert sdk.profiles is not None
        assert sdk.analytics is not None
        assert sdk.database is not None
        assert sdk.tasks is not None
        assert sdk.admin is not None

    def test_sdk_init_with_token(self):
        """Test SDK initialization with authentication token."""
        token = "test-token-123"
        sdk = AIChatbotSDK("http://localhost:8000", token=token)
        
        assert sdk.token == token

    def test_sdk_token_management(self):
        """Test token management methods."""
        sdk = AIChatbotSDK("http://localhost:8000")
        
        # Initially no token
        assert sdk.get_token() is None
        
        # Set token
        token = "test-token-456"
        sdk.set_token(token)
        assert sdk.get_token() == token
        
        # Clear token
        sdk.clear_token()
        assert sdk.get_token() is None


class TestHealthClient:
    """Test health check operations."""

    @pytest.fixture
    def sdk(self):
        return AIChatbotSDK("http://localhost:8000")

    @patch('requests.Session.request')
    def test_basic_health_check(self, mock_request, sdk):
        """Test basic health check."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        result = sdk.health.basic()
        
        assert result.success is True
        assert result.message == "Healthy"

    @patch('requests.Session.request')
    def test_detailed_health_check(self, mock_request, sdk):
        """Test detailed health check."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "database": {"connected": True},
            "services": {"openai": True},
            "performance": {"response_time": 50}
        }
        mock_request.return_value = mock_response

        result = sdk.health.detailed()
        
        assert "database" in result
        assert result["database"]["connected"] is True


class TestAuthClient:
    """Test authentication operations."""

    @pytest.fixture
    def sdk(self):
        return AIChatbotSDK("http://localhost:8000")

    @patch('requests.Session.request')
    def test_register_user(self, mock_request, sdk):
        """Test user registration."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        register_data = RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User"
        )
        
        result = sdk.auth.register(register_data)
        
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    @patch('requests.Session.request')
    def test_login_success(self, mock_request, sdk):
        """Test successful login."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "jwt-token-here",
            "token_type": "bearer",
            "expires_in": 86400
        }
        mock_request.return_value = mock_response

        result = sdk.auth.login("testuser", "testpass123")
        
        assert result.access_token == "jwt-token-here"
        assert result.token_type == "bearer"
        # Check token was set on SDK
        assert sdk.token == "jwt-token-here"

    @patch('requests.Session.request')
    def test_get_current_user(self, mock_request, sdk):
        """Test getting current user profile."""
        sdk.set_token("test-token")
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        result = sdk.auth.me()
        
        assert result.username == "testuser"
        assert result.email == "test@example.com"


class TestUsersClient:
    """Test user management operations."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_list_users(self, mock_request, sdk):
        """Test listing users."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Users retrieved successfully",
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "username": "user1",
                    "email": "user1@example.com",
                    "is_active": True,
                    "is_superuser": False,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "pagination": {"page": 1, "per_page": 20, "total": 1}
        }
        mock_request.return_value = mock_response

        result = sdk.users.list(page=1, size=20)
        
        assert result.success is True
        assert len(result.items) == 1
        assert result.items[0].username == "user1"

    @patch('requests.Session.request')
    def test_update_user(self, mock_request, sdk):
        """Test updating user profile."""
        user_id = uuid.uuid4()
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": str(user_id),
            "username": "testuser",
            "email": "newemail@example.com",
            "is_active": True,
            "is_superuser": False,
            "created_at": "2024-01-01T00:00:00Z",
            "full_name": "Updated Name"
        }
        mock_request.return_value = mock_response

        update_data = UserUpdate(
            email="newemail@example.com",
            full_name="Updated Name"
        )
        
        result = sdk.users.update(user_id, update_data)
        
        assert result.email == "newemail@example.com"
        assert result.full_name == "Updated Name"


class TestDocumentsClient:
    """Test document management operations."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_upload_document(self, mock_request, sdk):
        """Test document upload."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Document uploaded successfully",
            "document": {
                "id": str(uuid.uuid4()),
                "title": "Test Document",
                "filename": "test.pdf",
                "file_type": "pdf",
                "file_size": 12345,
                "processing_status": "pending",
                "owner_id": str(uuid.uuid4()),
                "chunk_count": 0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "processing_started": True
        }
        mock_request.return_value = mock_response

        # Create a test file
        test_file = BytesIO(b"Test document content")
        test_file.name = "test.pdf"
        
        result = sdk.documents.upload(test_file, title="Test Document")
        
        assert result.success is True
        assert result.document.title == "Test Document"
        assert result.document.filename == "test.pdf"
        assert result.processing_started is True

    @patch('requests.Session.request')
    def test_list_documents(self, mock_request, sdk):
        """Test listing documents."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Documents retrieved successfully",
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Document 1",
                    "filename": "doc1.pdf",
                    "file_type": "pdf",
                    "file_size": 12345,
                    "processing_status": "completed",
                    "owner_id": str(uuid.uuid4()),
                    "chunk_count": 5,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ],
            "pagination": {"page": 1, "per_page": 20, "total": 1}
        }
        mock_request.return_value = mock_response

        result = sdk.documents.list(page=1, size=20, status="completed")
        
        assert result.success is True
        assert len(result.items) == 1
        assert result.items[0].title == "Document 1"
        assert result.items[0].processing_status == "completed"


class TestConversationsClient:
    """Test conversation management operations."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_create_conversation(self, mock_request, sdk):
        """Test creating a conversation."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": str(uuid.uuid4()),
            "title": "Test Conversation",
            "is_active": True,
            "user_id": str(uuid.uuid4()),
            "message_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        conversation_data = ConversationCreate(
            title="Test Conversation",
            is_active=True
        )
        
        result = sdk.conversations.create(conversation_data)
        
        assert result.title == "Test Conversation"
        assert result.is_active is True

    @patch('requests.Session.request')
    def test_chat_message(self, mock_request, sdk):
        """Test sending a chat message."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Chat response generated",
            "ai_message": {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": "Hello! How can I help you?",
                "conversation_id": str(uuid.uuid4()),
                "token_count": 10,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "conversation": {
                "id": str(uuid.uuid4()),
                "title": "Chat Conversation",
                "is_active": True,
                "user_id": str(uuid.uuid4()),
                "message_count": 2,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "response_time_ms": 250.5
        }
        mock_request.return_value = mock_response

        chat_request = ChatRequest(
            user_message="Hello!",
            use_rag=True,
            use_tools=True
        )
        
        result = sdk.conversations.chat(chat_request)
        
        assert result.success is True
        assert result.ai_message.content == "Hello! How can I help you?"
        assert result.ai_message.role == "assistant"
        assert result.response_time_ms == 250.5


class TestSearchClient:
    """Test search operations."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_document_search(self, mock_request, sdk):
        """Test document search."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Search completed successfully",
            "results": [
                {
                    "document_id": str(uuid.uuid4()),
                    "chunk_id": 1,
                    "content": "This is relevant content...",
                    "score": 0.95,
                    "metadata": {"page": 1}
                }
            ],
            "query": "machine learning",
            "algorithm": "hybrid",
            "total_results": 1
        }
        mock_request.return_value = mock_response

        search_request = DocumentSearchRequest(
            query="machine learning",
            algorithm="hybrid",
            limit=10,
            threshold=0.8
        )
        
        result = sdk.search.search(search_request)
        
        assert result["success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["score"] == 0.95


class TestToolsClient:
    """Test MCP tools management."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_list_tools(self, mock_request, sdk):
        """Test listing MCP tools."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "Tools retrieved successfully",
            "available_tools": [
                {
                    "name": "file_manager",
                    "description": "File management operations",
                    "schema": {"type": "object"},
                    "server_name": "mcp_server",
                    "is_enabled": True,
                    "usage_count": 10
                }
            ],
            "openai_tools": [],
            "servers": [],
            "enabled_count": 1,
            "total_count": 1
        }
        mock_request.return_value = mock_response

        result = sdk.tools.list_tools()
        
        assert result.success is True
        assert len(result.available_tools) == 1
        assert result.available_tools[0].name == "file_manager"
        assert result.enabled_count == 1


class TestPromptsClient:
    """Test prompt registry management."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_create_prompt(self, mock_request, sdk):
        """Test creating a prompt."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "name": "test_prompt",
            "title": "Test Prompt",
            "description": "A test prompt",
            "content": "You are a helpful assistant.",
            "category": "general",
            "tags": ["test"],
            "is_active": True,
            "usage_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        prompt_data = PromptCreate(
            name="test_prompt",
            title="Test Prompt",
            description="A test prompt",
            content="You are a helpful assistant.",
            category="general",
            tags=["test"]
        )
        
        result = sdk.prompts.create_prompt(prompt_data)
        
        assert result.name == "test_prompt"
        assert result.title == "Test Prompt"
        assert result.content == "You are a helpful assistant."


class TestProfilesClient:
    """Test LLM profile management."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_create_profile(self, mock_request, sdk):
        """Test creating an LLM profile."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "name": "creative",
            "title": "Creative Writing",
            "description": "For creative writing tasks",
            "model_name": "gpt-4",
            "parameters": {
                "temperature": 1.0,
                "top_p": 0.95,
                "max_tokens": 2000
            },
            "is_default": False,
            "is_active": True,
            "usage_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        profile_data = LLMProfileCreate(
            name="creative",
            title="Creative Writing",
            description="For creative writing tasks",
            model_name="gpt-4",
            parameters={
                "temperature": 1.0,
                "top_p": 0.95,
                "max_tokens": 2000
            }
        )
        
        result = sdk.profiles.create_profile(profile_data)
        
        assert result.name == "creative"
        assert result.title == "Creative Writing"
        assert result.parameters["temperature"] == 1.0


class TestAnalyticsClient:
    """Test analytics and reporting."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_get_overview(self, mock_request, sdk):
        """Test getting analytics overview."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "users": {"total": 100, "active": 85},
            "documents": {"total": 500, "processed": 480},
            "conversations": {"total": 1000, "active": 50},
            "system_health": {"score": 95}
        }
        mock_request.return_value = mock_response

        result = sdk.analytics.get_overview()
        
        assert result["users"]["total"] == 100
        assert result["documents"]["processed"] == 480
        assert result["system_health"]["score"] == 95


class TestDatabaseClient:
    """Test database management."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_get_status(self, mock_request, sdk):
        """Test getting database status."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "connected": True,
            "version": "14.2",
            "tables": 15,
            "size": "125MB"
        }
        mock_request.return_value = mock_response

        result = sdk.database.get_status()
        
        assert result["connected"] is True
        assert result["version"] == "14.2"
        assert result["tables"] == 15


class TestTasksClient:
    """Test background task management."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_get_status(self, mock_request, sdk):
        """Test getting task system status."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "workers": 3,
            "active_tasks": 5,
            "pending_tasks": 2,
            "failed_tasks": 0
        }
        mock_request.return_value = mock_response

        result = sdk.tasks.get_status()
        
        assert result["workers"] == 3
        assert result["active_tasks"] == 5
        assert result["failed_tasks"] == 0


class TestAdminClient:
    """Test admin operations."""

    @pytest.fixture
    def sdk(self):
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test-token")
        return sdk

    @patch('requests.Session.request')
    def test_promote_user(self, mock_request, sdk):
        """Test promoting user to superuser."""
        user_id = uuid.uuid4()
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": f"User {user_id} promoted to superuser"
        }
        mock_request.return_value = mock_response

        result = sdk.admin.promote_user(user_id)
        
        assert result.success is True
        assert "promoted" in result.message

    @patch('requests.Session.request')
    def test_get_user_stats(self, mock_request, sdk):
        """Test getting user statistics."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "total_users": 100,
            "active_users": 85,
            "superusers": 5,
            "new_users_today": 3
        }
        mock_request.return_value = mock_response

        result = sdk.admin.get_user_stats()
        
        assert result["total_users"] == 100
        assert result["active_users"] == 85
        assert result["superusers"] == 5


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def sdk(self):
        return AIChatbotSDK("http://localhost:8000")

    @patch('requests.Session.request')
    def test_api_error_handling(self, mock_request, sdk):
        """Test that API errors are properly raised."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.json.return_value = {"error": "Resource not found"}
        mock_response.text = '{"error": "Resource not found"}'
        mock_request.return_value = mock_response

        with pytest.raises(ApiError) as exc_info:
            sdk.health.basic()
        
        assert exc_info.value.status == 404
        assert exc_info.value.reason == "Not Found"

    def test_custom_error_handler(self):
        """Test custom error handler callback."""
        error_captured = []
        
        def custom_error_handler(error: ApiError):
            error_captured.append(error)
        
        sdk = AIChatbotSDK("http://localhost:8000", on_error=custom_error_handler)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 500
            mock_response.reason = "Internal Server Error"
            mock_response.json.return_value = {"error": "Server error"}
            mock_response.text = '{"error": "Server error"}'
            mock_request.return_value = mock_response

            with pytest.raises(ApiError):
                sdk.health.basic()
            
            assert len(error_captured) == 1
            assert error_captured[0].status == 500


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])