"""
Unit tests for authentication API endpoints.

These tests cover user registration, login, token management, and related
authentication functionality using mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    @pytest.mark.unit
    def test_register_user_success(self, client: TestClient, sample_user_data: dict):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert data["user"]["username"] == sample_user_data["username"]
        assert data["user"]["email"] == sample_user_data["email"]
        assert "password" not in data["user"]  # Password should not be returned
    
    @pytest.mark.unit
    def test_register_user_duplicate_username(self, client: TestClient, sample_user_data: dict):
        """Test registration with duplicate username."""
        # Register user first time
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to register same username again
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["message"].lower()
    
    @pytest.mark.unit
    def test_register_user_invalid_email(self, client: TestClient, sample_user_data: dict):
        """Test registration with invalid email format."""
        sample_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    def test_register_user_weak_password(self, client: TestClient, sample_user_data: dict):
        """Test registration with weak password."""
        sample_user_data["password"] = "weak"
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "password" in data["message"].lower()
    
    @pytest.mark.unit
    def test_login_success(self, client: TestClient, sample_user_data: dict):
        """Test successful user login."""
        # Register user first
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.unit
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    @pytest.mark.unit
    def test_login_with_email(self, client: TestClient, sample_user_data: dict):
        """Test login using email instead of username."""
        # Register user first
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Login with email
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data


class TestAuthenticationFlow:
    """Test complete authentication flows."""
    
    @pytest.mark.integration
    def test_complete_auth_flow(self, client: TestClient, test_factory):
        """Test complete registration -> login -> access protected endpoint flow."""
        # 1. Register new user
        user_data = test_factory.create_user_data("flowtest", "flow@test.com")
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # 2. Login to get token
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        token = response.json()["access_token"]
        
        # 3. Access protected endpoint with token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        user_info = response.json()
        assert user_info["username"] == user_data["username"]
        assert user_info["email"] == user_data["email"]
    
    @pytest.mark.integration
    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.integration
    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED