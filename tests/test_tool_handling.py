"Test cases for tool_handling functionality."

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.schemas.conversation import ChatRequest
from app.schemas.tool_calling import ToolHandlingMode
from app.services.openai_client import OpenAIClient


class TestToolHandlingModes:
    "Test class for toolhandlingmodes functionality."

    def setup_method(self):
        "Setup Method operation."
        self.openai_client = OpenAIClient()

    @pytest.mark.asyncio
    async def test_return_results_mode(self):
        "Test return results mode functionality."
        with patch("app.services.openai_client.OPENAI_AVAILABLE", True):
            with patch.object(self.openai_client, "client") as mock_client:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message = MagicMock()
                mock_response.choices[0].message.content = None
                mock_response.choices[0].message.role = "assistant"
                mock_tool_call = MagicMock()
                mock_tool_call.id = "test_call_1"
                mock_tool_call.function = MagicMock()
                mock_tool_call.function.name = "test_tool"
                mock_tool_call.function.arguments = '{"query": "test"}'
                mock_tool_call.model_dump.return_value = {
                    "id": "test_call_1",
                    "function": {"name": "test_tool", "arguments": '{"query": "test"}'},
                }
                mock_response.choices[0].message.tool_calls = [mock_tool_call]
                mock_response.choices[0].finish_reason = "tool_calls"
                mock_response.usage = MagicMock(
                    prompt_tokens=10, completion_tokens=5, total_tokens=15
                )
                mock_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )
                with patch.object(
                    self.openai_client, "_execute_unified_tool_calls"
                ) as mock_execute:
                    mock_execute.return_value = [
                        {
                            "tool_call_id": "test_call_1",
                            "tool_name": "test_tool",
                            "success": True,
                            "content": [{"type": "text", "text": "Test result"}],
                            "error": None,
                            "provider": "fastmcp",
                            "execution_time_ms": 150.0,
                        }
                    ]
                    result = await self.openai_client.chat_completion(
                        messages=[{"role": "user", "content": "Test message"}],
                        tool_handling_mode=ToolHandlingMode.RETURN_RESULTS,
                    )
                    assert (
                        result["tool_handling_mode"]
                        == ToolHandlingMode.RETURN_RESULTS.value
                    )
                    assert "Tool Execution Results" in result["content"]
                    assert "✅ **Status**: Success" in result["content"]
                    assert "Test result" in result["content"]
                    assert result["tool_calls_executed"]
                    assert len(result["tool_calls_executed"]) == 1

    @pytest.mark.asyncio
    async def test_complete_with_results_mode(self):
        "Test complete with results mode functionality."
        with patch("app.services.openai_client.OPENAI_AVAILABLE", True):
            with patch.object(self.openai_client, "client") as mock_client:
                mock_response_1 = MagicMock()
                mock_response_1.choices = [MagicMock()]
                mock_response_1.choices[0].message = MagicMock()
                mock_response_1.choices[0].message.content = None
                mock_response_1.choices[0].message.role = "assistant"
                mock_tool_call_1 = MagicMock()
                mock_tool_call_1.id = "test_call_1"
                mock_tool_call_1.function = MagicMock()
                mock_tool_call_1.function.name = "test_tool"
                mock_tool_call_1.function.arguments = '{"query": "test"}'
                mock_tool_call_1.model_dump.return_value = {
                    "id": "test_call_1",
                    "function": {"name": "test_tool", "arguments": '{"query": "test"}'},
                }
                mock_response_1.choices[0].message.tool_calls = [mock_tool_call_1]
                mock_response_1.choices[0].finish_reason = "tool_calls"
                mock_response_1.usage = MagicMock(
                    prompt_tokens=10, completion_tokens=5, total_tokens=15
                )
                mock_response_2 = MagicMock()
                mock_response_2.choices = [MagicMock()]
                mock_response_2.choices[0].message = MagicMock()
                mock_response_2.choices[0].message.content = (
                    "Based on the tool results, here is my final answer."
                )
                mock_response_2.choices[0].message.role = "assistant"
                mock_response_2.choices[0].finish_reason = "stop"
                mock_response_2.usage = MagicMock(
                    prompt_tokens=20, completion_tokens=10, total_tokens=30
                )
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=[mock_response_1, mock_response_2]
                )
                with patch.object(
                    self.openai_client, "_execute_unified_tool_calls"
                ) as mock_execute:
                    mock_execute.return_value = [
                        {
                            "tool_call_id": "test_call_1",
                            "tool_name": "test_tool",
                            "success": True,
                            "content": [
                                {"type": "text", "text": "Tool execution successful"}
                            ],
                            "error": None,
                            "provider": "fastmcp",
                            "execution_time_ms": 200.0,
                        }
                    ]
                    result = await self.openai_client.chat_completion(
                        messages=[{"role": "user", "content": "Test message"}],
                        tool_handling_mode=ToolHandlingMode.COMPLETE_WITH_RESULTS,
                    )
                    assert (
                        result["tool_handling_mode"]
                        == ToolHandlingMode.COMPLETE_WITH_RESULTS.value
                    )
                    assert (
                        result["content"]
                        == "Based on the tool results, here is my final answer."
                    )
                    assert result["usage"]["total_tokens"] == 45
                    assert result["tool_calls_executed"]
                    assert len(result["tool_calls_executed"]) == 1
                    assert mock_client.chat.completions.create.call_count == 2

    def test_format_tool_results_as_content(self):
        "Test format tool results as content functionality."
        tool_results = [
            {
                "tool_call_id": "test_1",
                "success": True,
                "content": [{"type": "text", "text": "First result"}],
                "execution_time_ms": 100.0,
            },
            {
                "tool_call_id": "test_2",
                "success": False,
                "error": "Tool failed",
                "execution_time_ms": 50.0,
            },
        ]
        content = self.openai_client._format_tool_results_as_content(tool_results)
        assert "# Tool Execution Results" in content
        assert "✅ **Status**: Success" in content
        assert "First result" in content
        assert "❌ **Status**: Failed" in content
        assert "Tool failed" in content
        assert "100.00ms" in content
        assert "50.00ms" in content

    def test_format_tool_result_for_ai(self):
        "Test format tool result for ai functionality."
        success_result = {
            "success": True,
            "content": [{"type": "text", "text": "Successful execution"}],
        }
        formatted = self.openai_client._format_tool_result_for_ai(success_result)
        assert formatted == "Successful execution"
        failed_result = {"success": False, "error": "Something went wrong"}
        formatted = self.openai_client._format_tool_result_for_ai(failed_result)
        assert formatted == "Tool execution failed: Something went wrong"
        empty_result = {"success": True, "content": []}
        formatted = self.openai_client._format_tool_result_for_ai(empty_result)
        assert formatted == "Tool executed successfully but returned no content."

    @pytest.mark.asyncio
    async def test_chat_request_with_tool_handling_mode(self):
        "Test chat request with tool handling mode functionality."
        request = ChatRequest(user_message="Test message")
        assert request.tool_handling_mode == ToolHandlingMode.COMPLETE_WITH_RESULTS
        request = ChatRequest(
            user_message="Test message",
            tool_handling_mode=ToolHandlingMode.RETURN_RESULTS,
        )
        assert request.tool_handling_mode == ToolHandlingMode.RETURN_RESULTS

    def test_tool_handling_mode_enum_values(self):
        "Test tool handling mode enum values functionality."
        assert ToolHandlingMode.RETURN_RESULTS.value == "return_results"
        assert ToolHandlingMode.COMPLETE_WITH_RESULTS.value == "complete_with_results"
        assert ToolHandlingMode("return_results") == ToolHandlingMode.RETURN_RESULTS
        assert (
            ToolHandlingMode("complete_with_results")
            == ToolHandlingMode.COMPLETE_WITH_RESULTS
        )
