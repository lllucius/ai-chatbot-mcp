"Test cases for auth functionality."

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    "Test class for authendpoints functionality."

    @pytest.mark.unit
    def test_register_user_success(self, client: TestClient, sample_user_data: dict):
        "Test register user success functionality."
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert data["user"]["username"] == sample_user_data["username"]
        assert data["user"]["email"] == sample_user_data["email"]
        assert "password" not in data["user"]

    @pytest.mark.unit
    def test_register_user_duplicate_username(
        self, client: TestClient, sample_user_data: dict
    ):
        "Test register user duplicate username functionality."
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["message"].lower()

    @pytest.mark.unit
    def test_register_user_invalid_email(
        self, client: TestClient, sample_user_data: dict
    ):
        "Test register user invalid email functionality."
        sample_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.unit
    def test_register_user_weak_password(
        self, client: TestClient, sample_user_data: dict
    ):
        "Test register user weak password functionality."
        sample_user_data["password"] = "weak"
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "password" in data["message"].lower()

    @pytest.mark.unit
    def test_login_success(self, client: TestClient, sample_user_data: dict):
        "Test login success functionality."
        client.post("/api/v1/auth/register", json=sample_user_data)
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"],
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
        "Test login invalid credentials functionality."
        login_data = {"username": "nonexistent", "password": "wrongpassword"}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False

    @pytest.mark.unit
    def test_login_with_email(self, client: TestClient, sample_user_data: dict):
        "Test login with email functionality."
        client.post("/api/v1/auth/register", json=sample_user_data)
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data


class TestAuthenticationFlow:
    "Test class for authenticationflow functionality."

    @pytest.mark.integration
    def test_complete_auth_flow(self, client: TestClient, test_factory):
        "Test complete auth flow functionality."
        user_data = test_factory.create_user_data("flowtest", "flow@test.com")
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"],
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user_info = response.json()
        assert user_info["username"] == user_data["username"]
        assert user_info["email"] == user_data["email"]

    @pytest.mark.integration
    def test_protected_endpoint_without_token(self, client: TestClient):
        "Test protected endpoint without token functionality."
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        "Test protected endpoint with invalid token functionality."
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
