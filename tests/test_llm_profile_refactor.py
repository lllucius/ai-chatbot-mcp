"""
Tests for LLM Profile Refactoring.

This module tests the changes where individual parameters (temperature, max_tokens)
were replaced with LLMProfile objects in the conversation API.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.llm_profile import LLMProfile
from app.schemas.conversation import ChatRequest
from app.services.openai_client import OpenAIClient


class TestLLMProfileRefactoring:
    """Test the LLM profile refactoring changes."""

    def test_chat_request_schema_changes(self):
        """Test that ChatRequest schema has been correctly refactored."""
        # Test that we can create a ChatRequest without temperature/max_tokens
        request = ChatRequest(user_message="Test message", profile_name="test_profile")

        # Verify that old fields are not present
        assert not hasattr(request, "temperature")
        assert not hasattr(request, "max_tokens")

        # Verify that new field is present
        assert hasattr(request, "llm_profile")
        assert request.llm_profile is None  # Default value

        # Test that we can create a request with an LLM profile
        profile = LLMProfile(
            name="test_profile", title="Test Profile", temperature=0.8, max_tokens=1500
        )

        request_with_profile = ChatRequest(
            user_message="Test message", llm_profile=profile
        )

        assert request_with_profile.llm_profile == profile

    def test_openai_client_signature_changes(self):
        """Test that OpenAI client methods have been correctly refactored."""
        import inspect

        client = OpenAIClient()

        # Test chat_completion method signature
        chat_completion_sig = inspect.signature(client.chat_completion)
        params = list(chat_completion_sig.parameters.keys())

        assert (
            "llm_profile" in params
        ), "chat_completion should accept llm_profile parameter"
        assert (
            "temperature" not in params
        ), "chat_completion should not accept temperature parameter"
        assert (
            "max_tokens" not in params
        ), "chat_completion should not accept max_tokens parameter"

        # Test chat_completion_stream method signature
        stream_sig = inspect.signature(client.chat_completion_stream)
        stream_params = list(stream_sig.parameters.keys())

        assert (
            "llm_profile" in stream_params
        ), "chat_completion_stream should accept llm_profile parameter"
        assert (
            "temperature" not in stream_params
        ), "chat_completion_stream should not accept temperature parameter"
        assert (
            "max_tokens" not in stream_params
        ), "chat_completion_stream should not accept max_tokens parameter"

    def test_llm_profile_to_openai_params(self):
        """Test that LLMProfile.to_openai_params() produces correct output."""
        profile = LLMProfile(
            name="test_profile",
            title="Test Profile",
            temperature=0.8,
            max_tokens=1500,
            top_p=0.9,
            presence_penalty=0.1,
            frequency_penalty=0.2,
            stop=["STOP", "END"],
        )

        params = profile.to_openai_params()

        expected_params = {
            "temperature": 0.8,
            "max_tokens": 1500,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.2,
            "stop": ["STOP", "END"],
        }

        for key, expected_value in expected_params.items():
            assert (
                params[key] == expected_value
            ), f"Expected {key}={expected_value}, got {params.get(key)}"

    @pytest.mark.asyncio
    async def test_openai_client_uses_profile_params(self):
        """Test that OpenAI client correctly uses LLM profile parameters."""
        with patch("app.services.openai_client.OPENAI_AVAILABLE", True):
            client = OpenAIClient()

            # Mock the OpenAI client
            with patch.object(client, "client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message = MagicMock()
                mock_response.choices[0].message.content = "Test response"
                mock_response.choices[0].message.role = "assistant"
                mock_response.choices[0].message.tool_calls = None
                mock_response.choices[0].finish_reason = "stop"
                mock_response.usage = MagicMock(
                    prompt_tokens=10, completion_tokens=5, total_tokens=15
                )

                mock_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )

                # Create a profile with specific parameters
                profile = LLMProfile(
                    name="test_profile",
                    title="Test Profile",
                    temperature=0.8,
                    max_tokens=1500,
                    top_p=0.9,
                )

                # Call chat_completion with the profile
                result = await client.chat_completion(
                    messages=[{"role": "user", "content": "Test message"}],
                    llm_profile=profile,
                )

                # Verify that the OpenAI client was called with profile parameters
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]

                assert call_args["temperature"] == 0.8
                assert call_args["max_tokens"] == 1500
                assert call_args["top_p"] == 0.9

                # Verify response structure
                assert result["content"] == "Test response"
                assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_openai_client_default_when_no_profile(self):
        """Test that OpenAI client uses defaults when no profile is provided."""
        with patch("app.services.openai_client.OPENAI_AVAILABLE", True):
            client = OpenAIClient()

            # Mock the OpenAI client
            with patch.object(client, "client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message = MagicMock()
                mock_response.choices[0].message.content = "Test response"
                mock_response.choices[0].message.role = "assistant"
                mock_response.choices[0].message.tool_calls = None
                mock_response.choices[0].finish_reason = "stop"
                mock_response.usage = MagicMock(
                    prompt_tokens=10, completion_tokens=5, total_tokens=15
                )

                mock_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )

                # Call chat_completion without a profile
                result = await client.chat_completion(
                    messages=[{"role": "user", "content": "Test message"}],
                    llm_profile=None,
                )

                # Verify that the OpenAI client was called with default parameters
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]

                assert call_args["temperature"] == 0.7  # Default value
                assert "max_tokens" not in call_args  # Should not be set

                # Verify response structure
                assert result["content"] == "Test response"

    def test_backward_compatibility_with_profile_name(self):
        """Test that profile_name field is still supported for backward compatibility."""
        request = ChatRequest(user_message="Test message", profile_name="my_profile")

        assert request.profile_name == "my_profile"
        assert request.llm_profile is None  # Should be None by default
