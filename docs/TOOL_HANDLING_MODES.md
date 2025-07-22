# Tool Call Handling Modes

The AI Chatbot Platform now supports flexible tool call handling through two distinct modes:

## Overview

When tools are called during a chat conversation, you can now choose how the results are handled:

1. **`return_results`** - Return tool execution results directly as the chat response
2. **`complete_with_results`** - Feed tool results back to OpenAI for a natural language response

## Usage

### API Request

Add the `tool_handling_mode` parameter to your chat requests:

```json
{
  "user_message": "What's the weather in New York?",
  "tool_handling_mode": "return_results",
  "use_tools": true
}
```

### Modes

#### RETURN_RESULTS Mode

Returns tool execution results as formatted markdown content without additional AI processing.

**Request:**
```json
{
  "user_message": "Search for Python tutorials",
  "tool_handling_mode": "return_results",
  "use_tools": true
}
```

**Response:**
```json
{
  "success": true,
  "ai_message": {
    "content": "# Tool Execution Results\n\n## Tool Call 1: web_search\n✅ **Status**: Success\n**Result**:\n```\nFound 10 Python tutorials...\n```\n**Execution Time**: 245.67ms",
    "role": "assistant"
  },
  "tool_call_summary": {
    "total_calls": 1,
    "successful_calls": 1,
    "failed_calls": 0,
    "total_execution_time_ms": 245.67,
    "results": [...]
  }
}
```

#### COMPLETE_WITH_RESULTS Mode (Default)

Executes tools and feeds results back to OpenAI for a natural language response.

**Request:**
```json
{
  "user_message": "Search for Python tutorials",
  "tool_handling_mode": "complete_with_results",
  "use_tools": true
}
```

**Response:**
```json
{
  "success": true,
  "ai_message": {
    "content": "I found several excellent Python tutorials for you. Here are some of the best options: [natural language response incorporating tool results]",
    "role": "assistant"
  },
  "tool_call_summary": {
    "total_calls": 1,
    "successful_calls": 1,
    "failed_calls": 0,
    "total_execution_time_ms": 245.67,
    "results": [...]
  }
}
```

## Use Cases

### RETURN_RESULTS Mode

- **Debugging**: See exactly what tools were called and their raw results
- **API Integration**: Get structured tool output for further processing
- **Tool Testing**: Validate tool execution without AI interpretation
- **Data Pipeline**: Extract raw tool data for downstream systems

### COMPLETE_WITH_RESULTS Mode

- **Conversational AI**: Natural language responses enhanced by tool results
- **User Interfaces**: Human-friendly responses in chat applications
- **Customer Support**: AI responses informed by tool-retrieved data
- **General Chat**: Standard conversational AI behavior

## Implementation Details

### Schema Changes

**ChatRequest:**
```python
class ChatRequest(BaseSchema):
    user_message: str
    tool_handling_mode: ToolHandlingMode = ToolHandlingMode.COMPLETE_WITH_RESULTS
    use_tools: bool = True
    # ... other fields
```

**ChatResponse:**
```python
class ChatResponse(BaseResponse):
    ai_message: MessageResponse
    tool_call_summary: Optional[ToolCallSummary] = None
    # ... other fields
```

### Tool Call Summary

The new `tool_call_summary` field provides detailed information about tool execution:

```python
{
  "total_calls": 2,
  "successful_calls": 2,
  "failed_calls": 0,
  "total_execution_time_ms": 425.32,
  "results": [
    {
      "tool_call_id": "call_123",
      "tool_name": "web_search",
      "success": true,
      "content": [...],
      "execution_time_ms": 245.67,
      "provider": "fastmcp"
    }
  ]
}
```

## Backward Compatibility

- Existing requests without `tool_handling_mode` default to `complete_with_results`
- The legacy `tool_calls_made` field is maintained for compatibility
- All existing API contracts remain unchanged

## Testing

Run the tests to validate functionality:

```bash
pytest tests/test_tool_handling.py -v
```

View the demo:

```bash
python examples/tool_handling_demo.py
```

## Configuration

No additional configuration is required. The feature works with existing tool setups including:

- FastMCP tools
- Unified tool executor
- Existing authentication and permissions