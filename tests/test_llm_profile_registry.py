"""
Unit tests for LLM profile registry functionality.

These tests cover LLM parameter profile management including creation,
parameter validation, and usage tracking.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm_profile_service import LLMProfileService


class TestLLMProfileService:
    """Test LLM profile service functionality."""

    @pytest.mark.asyncio
    async def test_create_profile(self):
        """Test creating an LLM profile."""
        with patch(
            "app.services.llm_profile_service.AsyncSessionLocal"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            profile = await LLMProfileService.create_profile(
                name="test_profile",
                title="Test Profile",
                description="Test profile description",
                temperature=0.7,
                top_p=0.9,
                max_tokens=2000,
            )

            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_default_profile(self):
        """Test creating a default profile unsets other defaults."""
        with patch(
            "app.services.llm_profile_service.AsyncSessionLocal"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            await LLMProfileService.create_profile(
                name="default_profile",
                title="Default Profile",
                is_default=True,
                temperature=0.5,
            )

            # Should unset existing defaults first
            assert mock_db.execute.call_count >= 1
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_parameters(self):
        """Test parameter validation."""
        # Test valid parameters
        errors = await LLMProfileService.validate_parameters(
            temperature=0.7, top_p=0.9, max_tokens=2000
        )
        assert len(errors) == 0

        # Test invalid parameters
        errors = await LLMProfileService.validate_parameters(
            temperature=3.0,  # Too high
            top_p=-0.1,  # Too low
            max_tokens=-100,  # Negative
        )
        assert len(errors) == 3
        assert "temperature" in errors
        assert "top_p" in errors
        assert "max_tokens" in errors

    @pytest.mark.asyncio
    async def test_clone_profile(self):
        """Test cloning an existing profile."""
        with patch(
            "app.services.llm_profile_service.AsyncSessionLocal"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock source profile
            source_profile = AsyncMock()
            source_profile.title = "Original Profile"
            source_profile.description = "Original description"
            source_profile.temperature = 0.7
            source_profile.top_p = 0.9
            source_profile.max_tokens = 2000
            source_profile.presence_penalty = 0.1
            source_profile.frequency_penalty = 0.2
            source_profile.stop = ["STOP"]
            source_profile.other_params = {"custom": "value"}

            with patch.object(LLMProfileService, "get_profile") as mock_get:
                with patch.object(LLMProfileService, "create_profile") as mock_create:
                    mock_get.return_value = source_profile
                    mock_create.return_value = AsyncMock()

                    cloned = await LLMProfileService.clone_profile(
                        source_name="original",
                        new_name="cloned",
                        new_title="Cloned Profile",
                    )

                    # Verify create was called with correct parameters
                    mock_create.assert_called_once()
                    call_args = mock_create.call_args
                    assert call_args[1]["name"] == "cloned"
                    assert call_args[1]["title"] == "Cloned Profile"
                    assert call_args[1]["is_default"] is False
                    assert call_args[1]["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_get_profile_for_openai(self):
        """Test getting profile parameters for OpenAI API."""
        with patch.object(LLMProfileService, "get_profile") as mock_get:
            with patch.object(LLMProfileService, "record_profile_usage") as mock_record:
                # Mock profile
                mock_profile = AsyncMock()
                mock_profile.name = "test_profile"
                mock_profile.to_openai_params.return_value = {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000,
                }
                mock_get.return_value = mock_profile

                params = await LLMProfileService.get_profile_for_openai("test_profile")

                assert params["temperature"] == 0.7
                assert params["top_p"] == 0.9
                assert params["max_tokens"] == 2000
                mock_record.assert_called_once_with("test_profile")


class TestLLMProfileModel:
    """Test LLM profile model functionality."""

    def test_profile_to_openai_params(self):
        """Test converting profile to OpenAI parameters."""
        from app.models.llm_profile import LLMProfile

        profile = LLMProfile(
            name="test",
            title="Test Profile",
            temperature=0.7,
            top_p=0.9,
            max_tokens=2000,
            presence_penalty=0.1,
            frequency_penalty=0.2,
            stop=["STOP", "END"],
        )

        params = profile.to_openai_params()

        assert params["temperature"] == 0.7
        assert params["top_p"] == 0.9
        assert params["max_tokens"] == 2000
        assert params["presence_penalty"] == 0.1
        assert params["frequency_penalty"] == 0.2
        assert params["stop"] == ["STOP", "END"]

    def test_profile_to_openai_params_with_other_params(self):
        """Test converting profile with other_params to OpenAI parameters."""
        from app.models.llm_profile import LLMProfile

        profile = LLMProfile(
            name="test",
            title="Test Profile",
            temperature=0.7,
            other_params={
                "custom_param": "value",
                "temperature": 0.8,
            },  # Should not override
        )

        params = profile.to_openai_params()

        assert params["temperature"] == 0.7  # Original value, not overridden
        assert params["custom_param"] == "value"

    def test_profile_to_dict(self):
        """Test converting profile to dictionary."""
        from datetime import datetime

        from app.models.llm_profile import LLMProfile

        now = datetime.utcnow()
        profile = LLMProfile(
            name="test",
            title="Test Profile",
            description="Test description",
            is_default=True,
            is_active=True,
            temperature=0.7,
            usage_count=5,
            last_used_at=now,
        )

        data = profile.to_dict()

        assert data["name"] == "test"
        assert data["title"] == "Test Profile"
        assert data["description"] == "Test description"
        assert data["is_default"] is True
        assert data["is_active"] is True
        assert data["temperature"] == 0.7
        assert data["usage_count"] == 5
        assert data["last_used_at"] == now

    def test_profile_record_usage(self):
        """Test profile usage recording."""
        from datetime import datetime

        from app.models.llm_profile import LLMProfile

        profile = LLMProfile(name="test", title="Test Profile", usage_count=10)

        profile.record_usage()

        assert profile.usage_count == 11
        assert isinstance(profile.last_used_at, datetime)


class TestLLMProfileParameterValidation:
    """Test LLM profile parameter validation."""

    @pytest.mark.asyncio
    async def test_temperature_validation(self):
        """Test temperature parameter validation."""
        # Valid values
        errors = await LLMProfileService.validate_parameters(temperature=0.0)
        assert "temperature" not in errors

        errors = await LLMProfileService.validate_parameters(temperature=2.0)
        assert "temperature" not in errors

        # Invalid values
        errors = await LLMProfileService.validate_parameters(temperature=-0.1)
        assert "temperature" in errors

        errors = await LLMProfileService.validate_parameters(temperature=2.1)
        assert "temperature" in errors

    @pytest.mark.asyncio
    async def test_penalty_validation(self):
        """Test penalty parameter validation."""
        # Valid values
        errors = await LLMProfileService.validate_parameters(
            presence_penalty=-2.0, frequency_penalty=2.0
        )
        assert "presence_penalty" not in errors
        assert "frequency_penalty" not in errors

        # Invalid values
        errors = await LLMProfileService.validate_parameters(
            presence_penalty=-2.1, frequency_penalty=2.1
        )
        assert "presence_penalty" in errors
        assert "frequency_penalty" in errors

    @pytest.mark.asyncio
    async def test_positive_integer_validation(self):
        """Test positive integer parameter validation."""
        # Valid values
        errors = await LLMProfileService.validate_parameters(
            top_k=50, max_tokens=1000, context_length=4000
        )
        assert len(errors) == 0

        # Invalid values
        errors = await LLMProfileService.validate_parameters(
            top_k=0, max_tokens=-100, context_length=0
        )
        assert "top_k" in errors
        assert "max_tokens" in errors
        assert "context_length" in errors
