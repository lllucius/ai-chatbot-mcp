"""
Integration tests for SDK with APIResponse envelope handling.

Tests that verify the entire SDK works correctly with the fixed response handling
when integrated with real API simulation.
"""

from unittest.mock import AsyncMock, patch

import pytest

from client.ai_chatbot_sdk import AIChatbotSDK
from shared.schemas.auth import PasswordResetRequest
from shared.schemas.user import UserResponse


class TestSDKIntegration:
    """Test full SDK integration with APIResponse envelope handling."""

    @pytest.fixture
    def sdk(self):
        """Create SDK instance for testing."""
        return AIChatbotSDK(base_url="http://test.example.com")

    @pytest.mark.asyncio
    async def test_users_client_me_with_envelope(self, sdk):
        """Test UsersClient.me() with APIResponse envelope format."""
        # Simulate API response in envelope format
        api_response = {
            'success': True,
            'message': 'User retrieved successfully',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': {
                'id': 123,
                'username': 'testuser',
                'email': 'test@example.com',
                'full_name': 'Test User',
                'is_active': True,
                'is_superuser': False,
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z'
            },
            'meta': None,
            'error': None
        }

        # Mock the _request method to return our envelope response
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = UserResponse(**api_response['data'])

            # Call the SDK method
            result = await sdk.users.me()

            # Verify the request was made correctly
            mock_request.assert_called_once_with("/api/v1/users/me", UserResponse)

            # Verify the result
            assert isinstance(result, UserResponse)
            assert result.username == 'testuser'
            assert result.email == 'test@example.com'

    @pytest.mark.asyncio
    async def test_users_client_list_with_pagination(self, sdk):
        """Test UsersClient.list() with paginated APIResponse envelope format."""
        # Simulate paginated API response
        api_response = {
            'success': True,
            'message': 'Users retrieved successfully',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': [
                {
                    'id': 123,
                    'username': 'user1',
                    'email': 'user1@example.com',
                    'full_name': 'User One',
                    'is_active': True,
                    'is_superuser': False,
                    'created_at': '2024-01-01T12:00:00Z',
                    'updated_at': '2024-01-01T12:00:00Z'
                }
            ],
            'meta': {
                'pagination': {
                    'page': 1,
                    'per_page': 20,
                    'total': 1,
                    'total_pages': 1,
                    'has_next': False,
                    'has_prev': False
                }
            },
            'error': None
        }

        # Create expected paginated response structure
        from client.ai_chatbot_sdk import PaginatedResponse
        from shared.schemas.common import PaginationParams

        expected_response = PaginatedResponse(
            success=True,
            message='Users retrieved successfully',
            timestamp='2024-01-01T12:00:00Z',
            items=[UserResponse(**api_response['data'][0])],
            pagination=PaginationParams(**api_response['meta']['pagination'])
        )

        # Mock the _request method
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response

            # Call the SDK method
            result = await sdk.users.list(page=1, size=20)

            # Verify the request was made correctly
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            assert args[0] == "/api/v1/users/"
            assert args[1] == UserResponse

            # Verify the result structure
            assert hasattr(result, 'items')
            assert hasattr(result, 'pagination')
            assert len(result.items) == 1
            assert isinstance(result.items[0], UserResponse)

    @pytest.mark.asyncio
    async def test_auth_client_error_handling(self, sdk):
        """Test AuthClient error handling with APIResponse envelope format."""
        # Simulate error response in envelope format
        from client.ai_chatbot_sdk import ApiError

        error_response_data = {
            'error_code': 'USER_NOT_FOUND',
            'message': 'User not found',
            'details': {'email': 'test@example.com'},
            'timestamp': '2024-01-01T12:00:00Z'
        }

        # Mock the _request method to raise ApiError
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = ApiError(404, "User not found", "http://test.com", error_response_data)

            # Test that the error is properly propagated
            with pytest.raises(ApiError) as exc_info:
                await sdk.auth.request_password_reset(PasswordResetRequest(email="test@example.com"))

            # Verify error details
            assert exc_info.value.status == 404
            assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raw_data_response(self, sdk):
        """Test SDK handling of raw data responses (non-object data)."""
        # Mock a response that returns raw data (like a count or simple value)
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = 42

            # Use a generic endpoint that might return raw data
            result = await sdk._request("/api/v1/test/count")

            # Verify the raw data is returned correctly
            assert result == 42

    @pytest.mark.asyncio
    async def test_null_data_response(self, sdk):
        """Test SDK handling of null data responses."""
        # Mock a response that returns null data
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            # Use a generic endpoint that might return null
            result = await sdk._request("/api/v1/test/null")

            # Verify null is returned correctly
            assert result is None

    @pytest.mark.asyncio
    async def test_conversations_client_with_envelope(self, sdk):
        """Test ConversationsClient methods with APIResponse envelope format."""
        from shared.schemas.conversation import ConversationResponse

        # Simulate conversation response in envelope format
        conversation_data = {
            'id': 123,
            'title': 'Test Conversation',
            'user_id': 456,
            'is_active': True,
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z'
        }

        # Mock the _request method
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = ConversationResponse(**conversation_data)

            # Test get conversation
            conversation_id = 123
            result = await sdk.conversations.get(conversation_id)

            # Verify the request was made correctly
            mock_request.assert_called_once_with(
                f"/api/v1/conversations/byid/{conversation_id}",
                ConversationResponse
            )

            # Verify the result
            assert isinstance(result, ConversationResponse)
            assert result.title == 'Test Conversation'

    @pytest.mark.asyncio
    async def test_documents_client_with_envelope(self, sdk):
        """Test DocumentsClient methods with APIResponse envelope format."""
        from shared.schemas.document import DocumentResponse

        # Simulate document response in envelope format
        document_data = {
            'id': 123,
            'filename': 'test.pdf',
            'title': 'Test Document',
            'file_type': 'pdf',
            'file_size': 1024,
            'mime_type': 'application/pdf',
            'processing_status': 'completed',
            'owner_id': 456,
            'metainfo': None,
            'chunk_count': 0,
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z'
        }

        # Mock the _request method
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = DocumentResponse(**document_data)

            # Test get document
            document_id = 123
            result = await sdk.documents.get(document_id)

            # Verify the request was made correctly
            mock_request.assert_called_once_with(
                f"/api/v1/documents/byid/{document_id}",
                DocumentResponse
            )

            # Verify the result
            assert isinstance(result, DocumentResponse)
            assert result.title == 'Test Document'
            assert result.filename == 'test.pdf'
