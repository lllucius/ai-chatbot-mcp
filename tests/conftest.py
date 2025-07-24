"Test configuration and fixtures for pytest."

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database import get_db
from app.main import app
from app.models.base import BaseModelDB

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:password@localhost:5432/ai_chatbot_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[(asyncio.AbstractEventLoop, None, None)]:
    "Event Loop operation."
    loop = asyncio.get_event_loop_policy().new_event_loop()
    (yield loop)
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[(AsyncSession, None)]:
    "Test db functionality."
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with engine.begin() as conn:
        (await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector")))
        (await conn.run_sync(BaseModelDB.metadata.create_all))
    async with async_session_maker() as session:
        (yield session)
    (await engine.dispose())


@pytest.fixture
def client() -> TestClient:
    "Client operation."
    return TestClient(app)


@pytest_asyncio.fixture
async def authenticated_client(test_db: AsyncSession) -> TestClient:
    "Authenticated Client operation."
    app.dependency_overrides[get_db] = lambda: test_db
    client = TestClient(app)
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    login_data = {"username": "testuser", "password": "TestPass123!"}
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    (yield client)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    "Sample User Data operation."
    return {
        "username": "sampleuser",
        "email": "sample@example.com",
        "password": "SamplePass123!",
        "full_name": "Sample User",
    }


@pytest.fixture
def sample_document_data() -> dict:
    "Sample Document Data operation."
    return {
        "title": "Sample Document",
        "content": "This is a sample document for testing purposes.",
        "file_type": "txt",
        "file_size": 100,
    }


@pytest.fixture
def sample_conversation_data() -> dict:
    "Sample Conversation Data operation."
    return {
        "title": "Test Conversation",
        "user_message": "Hello, how are you?",
        "use_rag": False,
    }


class TestDataFactory:
    "Test class for datafactory functionality."

    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "TestPass123!",
    ) -> dict:
        "Create new user data."
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
        "Create new document data."
        return {
            "title": title,
            "content": content,
            "file_type": "txt",
            "file_size": len(content),
        }


@pytest.fixture
def test_factory() -> TestDataFactory:
    "Test factory functionality."
    return TestDataFactory()
