"""
Tests to validate that the SDK uses correct API endpoints.

These tests ensure that the SDK is calling the correct API endpoints and not using
deprecated or non-existent endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from client.ai_chatbot_sdk import AIChatbotSDK
from shared.schemas.auth import PasswordResetRequest, PasswordResetConfirm
from shared.schemas.user import UserUpdate, UserPasswordUpdate


class TestSDKAPIEndpointUsage:
    """Test SDK API endpoint usage correctness."""

    @pytest.fixture
    def sdk(self):
        """Create SDK instance for testing."""
        return AIChatbotSDK(base_url="http://test.example.com")

    @pytest.mark.asyncio
    async def test_auth_me_uses_correct_endpoint(self, sdk):
        """Test that AuthClient.me() calls the correct endpoint."""
        # Mock the _request method
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "123", "username": "test"}
            
            await sdk.auth.me()
            
            # Should call /api/v1/users/me, not /api/v1/auth/me
            mock_request.assert_called_once_with("/api/v1/users/me", mock_request.call_args[0][1])

    @pytest.mark.asyncio
    async def test_password_reset_uses_correct_endpoint(self, sdk):
        """Test that password reset calls the correct endpoint."""
        request = PasswordResetRequest(email="test@example.com")
        
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Reset requested"}
            
            await sdk.auth.request_password_reset(request)
            
            # Should call /api/v1/users/password-reset, not /api/v1/auth/password-reset
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "/api/v1/users/password-reset"

    @pytest.mark.asyncio
    async def test_password_reset_confirm_uses_correct_endpoint(self, sdk):
        """Test that password reset confirmation calls the correct endpoint."""
        request = PasswordResetConfirm(token="test_token", new_password="NewPass123!")
        
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Reset confirmed"}
            
            await sdk.auth.confirm_password_reset(request)
            
            # Should call /api/v1/users/password-reset/confirm, not /api/v1/auth/password-reset/confirm
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "/api/v1/users/password-reset/confirm"

    @pytest.mark.asyncio
    async def test_conversation_search_endpoint(self, sdk):
        """Test that conversation search uses correct endpoint."""
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"results": []}
            
            await sdk.conversations.search("test query")
            
            # Should call /api/v1/conversations/search with correct parameters
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Check if it's calling the right endpoint pattern
            assert "/api/v1/conversations" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_users_me_endpoint_exists(self, sdk):
        """Test that UsersClient.me() calls correct endpoint."""
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "123", "username": "test"}
            
            await sdk.users.me()
            
            # Should call /api/v1/users/me
            mock_request.assert_called_once_with("/api/v1/users/me", mock_request.call_args[0][1])

    @pytest.mark.asyncio
    async def test_no_deprecated_endpoints_used(self, sdk):
        """Test that SDK doesn't use deprecated endpoints."""
        deprecated_endpoints = [
            "/api/v1/auth/password-reset",
            "/api/v1/auth/password-reset/confirm"
        ]
        
        # Test password reset request
        request = PasswordResetRequest(email="test@example.com")
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True}
            await sdk.auth.request_password_reset(request)
            
            call_args = mock_request.call_args
            endpoint_called = call_args[0][0]
            assert endpoint_called not in deprecated_endpoints, f"SDK is using deprecated endpoint: {endpoint_called}"

        # Test password reset confirm
        confirm_request = PasswordResetConfirm(token="test", new_password="NewPass123!")
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True}
            await sdk.auth.confirm_password_reset(confirm_request)
            
            call_args = mock_request.call_args
            endpoint_called = call_args[0][0]
            assert endpoint_called not in deprecated_endpoints, f"SDK is using deprecated endpoint: {endpoint_called}"

    @pytest.mark.asyncio
    async def test_admin_endpoints_mapping(self, sdk):
        """Test that admin endpoints map to correct actual endpoints."""
        with patch.object(sdk, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"total_users": 100}
            
            # Test admin user stats - should map to the actual endpoint
            await sdk.admin.get_user_stats()
            
            # Should call an actual endpoint, not a non-existent admin endpoint
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            endpoint_called = call_args[0][0]
            
            # Should not call /api/v1/admin/* which doesn't exist
            assert not endpoint_called.startswith("/api/v1/admin/"), f"Admin endpoint {endpoint_called} doesn't exist"