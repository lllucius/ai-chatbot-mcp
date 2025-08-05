"""
Tests for SDK response handling with APIResponse envelope format.

Tests that the SDK properly handles APIResponse envelopes returned by the API,
including extracting data, handling errors, and processing pagination.
"""

import asyncio
import pytest
from unittest.mock import Mock
from client.ai_chatbot_sdk import handle_response, ApiError
from shared.schemas.user import UserResponse
from shared.schemas.common import PaginationParams


class TestSDKResponseHandling:
    """Test SDK response handling with APIResponse envelope format."""

    @pytest.mark.asyncio
    async def test_handle_successful_single_response(self):
        """Test handling a successful single object response in APIResponse envelope."""
        # Simulate API response in APIResponse envelope format
        api_response_json = {
            'success': True,
            'message': 'User retrieved successfully',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': {
                'id': '123e4567-e89b-12d3-a456-426614174000',
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

        # Mock httpx response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = api_response_json

        # Test the fixed handle_response function
        result = await handle_response(mock_response, 'http://test.com', UserResponse)

        # Verify the result is properly deserialized
        assert isinstance(result, UserResponse)
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
        assert result.is_active is True
        assert result.is_superuser is False

    @pytest.mark.asyncio
    async def test_handle_successful_paginated_response(self):
        """Test handling a successful paginated response in APIResponse envelope."""
        # Simulate API paginated response
        api_response_json = {
            'success': True,
            'message': 'Users retrieved successfully',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': [
                {
                    'id': '123e4567-e89b-12d3-a456-426614174000',
                    'username': 'user1',
                    'email': 'user1@example.com',
                    'full_name': 'User One',
                    'is_active': True,
                    'is_superuser': False,
                    'created_at': '2024-01-01T12:00:00Z',
                    'updated_at': '2024-01-01T12:00:00Z'
                },
                {
                    'id': '456e7890-e89b-12d3-a456-426614174001',
                    'username': 'user2',
                    'email': 'user2@example.com',
                    'full_name': 'User Two',
                    'is_active': True,
                    'is_superuser': True,
                    'created_at': '2024-01-01T13:00:00Z',
                    'updated_at': '2024-01-01T13:00:00Z'
                }
            ],
            'meta': {
                'pagination': {
                    'page': 1,
                    'per_page': 10,
                    'total': 2,
                    'total_pages': 1,
                    'has_next': False,
                    'has_prev': False
                }
            },
            'error': None
        }

        # Mock httpx response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = api_response_json

        # Test the fixed handle_response function
        result = await handle_response(mock_response, 'http://test.com', UserResponse)

        # Verify the result is a paginated response
        assert hasattr(result, 'items')
        assert hasattr(result, 'pagination')
        assert len(result.items) == 2
        
        # Verify individual items are properly deserialized
        assert isinstance(result.items[0], UserResponse)
        assert result.items[0].username == 'user1'
        assert result.items[1].username == 'user2'
        
        # Verify pagination info
        assert isinstance(result.pagination, PaginationParams)
        assert result.pagination.page == 1
        assert result.pagination.total == 2

    @pytest.mark.asyncio
    async def test_handle_error_response(self):
        """Test handling an error response in APIResponse envelope."""
        # Simulate API error response
        api_response_json = {
            'success': False,
            'message': 'User not found',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': None,
            'meta': None,
            'error': {
                'code': 'USER_NOT_FOUND',
                'details': {
                    'user_id': '123e4567-e89b-12d3-a456-426614174000',
                    'reason': 'No user exists with the specified ID'
                }
            }
        }

        # Mock httpx response (200 OK but with error in envelope)
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = api_response_json

        # Test that an ApiError is raised
        with pytest.raises(ApiError) as exc_info:
            await handle_response(mock_response, 'http://test.com', UserResponse)

        # Verify error details
        assert exc_info.value.status == 200
        assert 'User not found' in str(exc_info.value)
        assert isinstance(exc_info.value.body, dict)
        assert exc_info.value.body['error_code'] == 'USER_NOT_FOUND'

    @pytest.mark.asyncio
    async def test_handle_primitive_data_response(self):
        """Test handling a response with primitive data (not an object)."""
        # Simulate API response with primitive data
        api_response_json = {
            'success': True,
            'message': 'Count retrieved successfully',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': 42,
            'meta': None,
            'error': None
        }

        # Mock httpx response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = api_response_json

        # Test without specifying a class (should return primitive data)
        result = await handle_response(mock_response, 'http://test.com')

        # Verify the result is the primitive value
        assert result == 42

    @pytest.mark.asyncio
    async def test_handle_null_data_response(self):
        """Test handling a response with null data."""
        # Simulate API response with null data
        api_response_json = {
            'success': True,
            'message': 'No data available',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': None,
            'meta': None,
            'error': None
        }

        # Mock httpx response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = api_response_json

        # Test with and without specifying a class
        result = await handle_response(mock_response, 'http://test.com', UserResponse)
        assert result is None

        result_no_cls = await handle_response(mock_response, 'http://test.com')
        assert result_no_cls is None

    @pytest.mark.asyncio
    async def test_handle_legacy_response_format(self):
        """Test that legacy response format (non-envelope) still works."""
        # Simulate legacy API response (direct data, no envelope)
        legacy_response_json = {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'is_active': True,
            'is_superuser': False,
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z'
        }

        # Mock httpx response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = legacy_response_json

        # Test the handle_response function with legacy format
        result = await handle_response(mock_response, 'http://test.com', UserResponse)

        # Verify the result is properly deserialized
        assert isinstance(result, UserResponse)
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'

    @pytest.mark.asyncio
    async def test_handle_http_error_response(self):
        """Test handling HTTP error responses (non-200 status codes)."""
        # Mock httpx error response
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        mock_response.json.return_value = {"detail": "User not found"}

        # Test that an ApiError is raised for HTTP errors
        with pytest.raises(ApiError) as exc_info:
            await handle_response(mock_response, 'http://test.com', UserResponse)

        # Verify error details
        assert exc_info.value.status == 404
        assert "Not Found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_list_without_pagination(self):
        """Test handling a list response without pagination metadata."""
        # Simulate API response with list but no pagination meta
        api_response_json = {
            'success': True,
            'message': 'Tags retrieved successfully',
            'timestamp': '2024-01-01T12:00:00Z',
            'data': ['tag1', 'tag2', 'tag3'],
            'meta': None,
            'error': None
        }

        # Mock httpx response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = api_response_json

        # Test without specifying a class
        result = await handle_response(mock_response, 'http://test.com')

        # Verify the result is the list
        assert result == ['tag1', 'tag2', 'tag3']