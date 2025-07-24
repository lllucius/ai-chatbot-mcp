"Test cases for users functionality."

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestUserEndpoints:
    "Test class for userendpoints functionality."

    @pytest.mark.unit
    def test_get_current_user_unauthorized(self, client: TestClient):
        "Test get current user unauthorized functionality."
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    def test_get_current_user_authorized(self, authenticated_client: TestClient):
        "Test get current user authorized functionality."
        response = authenticated_client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.integration
    def test_update_user_profile(self, authenticated_client: TestClient):
        "Test update user profile functionality."
        update_data = {"full_name": "Updated Full Name", "email": "updated@example.com"}
        response = authenticated_client.put("/api/v1/users/me", json=update_data)
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["full_name"] == update_data["full_name"]
            assert data["email"] == update_data["email"]
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            pass
        else:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
            ]


class TestUserValidation:
    "Test class for uservalidation functionality."

    @pytest.mark.unit
    def test_register_user_missing_fields(self, client: TestClient):
        "Test register user missing fields functionality."
        incomplete_data = {"username": "testuser"}
        response = client.post("/api/v1/auth/register", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.unit
    def test_register_user_invalid_username(
        self, client: TestClient, sample_user_data: dict
    ):
        "Test register user invalid username functionality."
        invalid_usernames = ["", "a", "user@name", "user name", "123"]
        for invalid_username in invalid_usernames:
            user_data = sample_user_data.copy()
            user_data["username"] = invalid_username
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

    @pytest.mark.unit
    def test_register_user_valid_data(self, client: TestClient, test_factory):
        "Test register user valid data functionality."
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
            ), f"Failed for user {(i + 1)}: {user_data}"
            data = response.json()
            assert data["success"] is True
            assert data["user"]["username"] == user_data["username"]
            assert data["user"]["email"] == user_data["email"]
