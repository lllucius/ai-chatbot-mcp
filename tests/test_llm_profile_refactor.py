"Test cases for llm_profile_refactor functionality."

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.conversation import ChatRequest
from app.models.llm_profile import LLMProfile
from app.services.openai_client import OpenAIClient


class TestLLMProfileRefactoring:
    "Test class for llmprofilerefactoring functionality."

    def test_chat_request_schema_changes(self):
        "Test chat request schema changes functionality."
        request = ChatRequest(user_message="Test message", profile_name="test_profile")
        assert not hasattr(request, "temperature")
        assert not hasattr(request, "max_tokens")
        assert hasattr(request, "llm_profile")
        assert request.llm_profile is None
        profile = LLMProfile(
            name="test_profile", title="Test Profile", temperature=0.8, max_tokens=1500
        )
        request_with_profile = ChatRequest(
            user_message="Test message", llm_profile=profile
        )
        assert request_with_profile.llm_profile == profile

    def test_openai_client_signature_changes(self):
        "Test openai client signature changes functionality."
        import inspect

        client = OpenAIClient()
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
        "Test llm profile to openai params functionality."
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
        "Test openai client uses profile params functionality."
        with patch("app.services.openai_client.OPENAI_AVAILABLE", True):
            client = OpenAIClient()
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
                profile = LLMProfile(
                    name="test_profile",
                    title="Test Profile",
                    temperature=0.8,
                    max_tokens=1500,
                    top_p=0.9,
                )
                result = await client.chat_completion(
                    messages=[{"role": "user", "content": "Test message"}],
                    llm_profile=profile,
                )
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["temperature"] == 0.8
                assert call_args["max_tokens"] == 1500
                assert call_args["top_p"] == 0.9
                assert result["content"] == "Test response"
                assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_openai_client_default_when_no_profile(self):
        "Test openai client default when no profile functionality."
        with patch("app.services.openai_client.OPENAI_AVAILABLE", True):
            client = OpenAIClient()
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
                result = await client.chat_completion(
                    messages=[{"role": "user", "content": "Test message"}],
                    llm_profile=None,
                )
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["temperature"] == 0.7
                assert "max_tokens" not in call_args
                assert result["content"] == "Test response"

    def test_backward_compatibility_with_profile_name(self):
        "Test backward compatibility with profile name functionality."
        request = ChatRequest(user_message="Test message", profile_name="my_profile")
        assert request.profile_name == "my_profile"
        assert request.llm_profile is None
