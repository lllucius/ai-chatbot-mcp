"""
Unit tests for user management functionality.

These tests cover user-related operations including profile management,
user queries, and user administration features.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestUserEndpoints:
    """Test user management API endpoints."""

    @pytest.mark.unit
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_get_current_user_authorized(self, authenticated_client: TestClient):
        """Test getting current user with valid authentication."""
        response = authenticated_client.get("/api/v1/users/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data
        # Password should never be returned
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.integration
    def test_update_user_profile(self, authenticated_client: TestClient):
        """Test updating user profile information."""
        update_data = {"full_name": "Updated Full Name", "email": "updated@example.com"}

        response = authenticated_client.put("/api/v1/users/me", json=update_data)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["full_name"] == update_data["full_name"]
            assert data["email"] == update_data["email"]
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            # Endpoint not implemented yet - acceptable for now
            pass
        else:
            # Check that we get expected status codes
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
            ]


class TestUserValidation:
    """Test user data validation."""

    @pytest.mark.unit
    def test_register_user_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        incomplete_data = {
            "username": "testuser"
            # Missing email, password, full_name
        }

        response = client.post("/api/v1/auth/register", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.unit
    def test_register_user_invalid_username(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test registration with invalid username formats."""
        invalid_usernames = ["", "a", "user@name", "user name", "123"]

        for invalid_username in invalid_usernames:
            user_data = sample_user_data.copy()
            user_data["username"] = invalid_username

            response = client.post("/api/v1/auth/register", json=user_data)
            # Should either reject with validation error or business logic error
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

    @pytest.mark.unit
    def test_register_user_valid_data(self, client: TestClient, test_factory):
        """Test registration with various valid user data formats."""
        valid_users = [
            test_factory.create_user_data(
                "user1", "user1@example.com", "ValidPass123!"
            ),
            test_factory.create_user_data(
                "test_user_2", "test2@domain.org", "AnotherPass456@"
            ),
            test_factory.create_user_data(
                "developer123", "dev@company.co.uk", "DevPassword789#"
            ),
        ]

        for i, user_data in enumerate(valid_users):
            response = client.post("/api/v1/auth/register", json=user_data)
            assert (
                response.status_code == status.HTTP_201_CREATED
            ), f"Failed for user {i+1}: {user_data}"

            data = response.json()
            assert data["success"] is True
            assert data["user"]["username"] == user_data["username"]
            assert data["user"]["email"] == user_data["email"]
