"""
Pytest configuration and fixtures for the test suite.

This module provides common fixtures and configuration for all tests,
including database setup, authentication helpers, and test data factories.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.database import get_db
from app.main import app
from app.models.base import BaseModelDB

# Test database URL - use test PostgreSQL database
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:password@localhost:5432/ai_chatbot_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create test engine for PostgreSQL
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # Create session maker
    async_session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables and setup pgvector
    async with engine.begin() as conn:
        # Enable pgvector extension for tests
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(BaseModelDB.metadata.create_all)

    # Create session
    async with async_session_maker() as session:
        yield session

    # Clean up
    await engine.dispose()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for API testing."""
    return TestClient(app)


@pytest_asyncio.fixture
async def authenticated_client(test_db: AsyncSession) -> TestClient:
    """Create a test client with authenticated user."""
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: test_db

    client = TestClient(app)

    # Create a test user and authenticate
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    }

    # Register user
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    # Login to get token
    login_data = {"username": "testuser", "password": "TestPass123!"}
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "sampleuser",
        "email": "sample@example.com",
        "password": "SamplePass123!",
        "full_name": "Sample User",
    }


@pytest.fixture
def sample_document_data() -> dict:
    """Sample document data for testing."""
    return {
        "title": "Sample Document",
        "content": "This is a sample document for testing purposes.",
        "file_type": "txt",
        "file_size": 100,
    }


@pytest.fixture
def sample_conversation_data() -> dict:
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "user_message": "Hello, how are you?",
        "use_rag": False,
    }


class TestDataFactory:
    """Factory class for creating test data."""

    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "TestPass123!",
    ) -> dict:
        """Create user data for testing."""
        return {
            "username": username,
            "email": email,
            "password": password,
            "full_name": f"Test {username.title()}",
        }

    @staticmethod
    def create_document_data(
        title: str = "Test Document", content: str = "Test content"
    ) -> dict:
        """Create document data for testing."""
        return {
            "title": title,
            "content": content,
            "file_type": "txt",
            "file_size": len(content),
        }


@pytest.fixture
def test_factory() -> TestDataFactory:
    """Test data factory fixture."""
    return TestDataFactory()
