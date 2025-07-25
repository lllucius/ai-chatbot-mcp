# SDK Response Handling Fixes

This document describes the fixes implemented to resolve SDK response handling issues in the AI Chatbot MCP platform.

## Issues Fixed

### 1. Tools List Validation Error

**Problem**: The `/tools list` command was failing with:
```
Error with tools command: 1 validation error for ToolsListResponse
message
  Field required [type=missing, input_value={'success': True, 'data':...'connected_servers': 1}}, input_type=dict]
```

**Root Cause**: The API was returning a nested response structure:
```json
{
  "success": True,
  "data": {
    "tools": [...],
    "openai_tools": [...],
    // ... other fields
  }
}
```

But the SDK `ToolsListResponse` model expected a flat structure:
```json
{
  "success": True,
  "message": "...",
  "available_tools": [...],
  "openai_tools": [...],
  "servers": [...],
  "enabled_count": 0,
  "total_count": 0
}
```

**Fix**: Modified `app/api/tools.py` to return the flat structure expected by the SDK.

### 2. Profiles List Not Showing Available Profiles

**Problem**: The `/profiles list` command was showing "No profiles available" even when profiles existed.

**Root Cause**: Similar to tools, the API was returning:
```json
{
  "success": True,
  "data": {
    "profiles": [...]
  }
}
```

But the client expected:
```json
{
  "success": True,
  "message": "...",
  "profiles": [...]
}
```

**Fix**: Modified `app/api/profiles.py` to return profiles at the top level.

### 3. Chat Stream JSON Serialization Error

**Problem**: The chat streaming endpoint was failing with:
```
TypeError: Object of type MessageResponse is not JSON serializable
```

**Root Cause**: The code was trying to serialize Pydantic objects directly:
```python
# This fails:
yield f"data: {json.dumps({'type': 'complete', 'response': chunk.get('response')})}\n\n"
```

Where `chunk.get('response')` contained `MessageResponse` and `ConversationResponse` Pydantic objects.

**Fixes**: 
1. Added proper streaming response models in `app/schemas/conversation.py`
2. Used `model_dump(mode='json')` to convert Pydantic objects to JSON-serializable dictionaries
3. Added UUID JSON encoders to handle UUID serialization
4. Added proper return type annotations

## Technical Changes

### API Response Structure Updates

#### Tools API (`app/api/tools.py`)
- Changed from nested `{"success": True, "data": {...}}` to flat structure
- Returns `available_tools`, `openai_tools`, `servers`, `enabled_count`, `total_count` at top level
- Added proper `message` field required by SDK

#### Profiles API (`app/api/profiles.py`)  
- Changed from nested `{"success": True, "data": {"profiles": [...]}}` to flat `{"success": True, "profiles": [...]}`
- Added proper `message` field
- Maintained pagination and filter information

### Streaming Response Improvements

#### New Response Models (`app/schemas/conversation.py`)
```python
class StreamStartResponse(BaseSchema):
    type: str = Field("start", description="Event type")
    message: str = Field(..., description="Start message")

class StreamContentResponse(BaseSchema):
    type: str = Field("content", description="Event type") 
    content: str = Field(..., description="Content chunk")

class StreamCompleteResponse(BaseSchema):
    type: str = Field("complete", description="Event type")
    response: Dict[str, Any] = Field(..., description="Complete response data")

# ... other streaming models
```

#### JSON Serialization Fix (`app/api/conversations.py`)
```python
# Convert Pydantic objects to JSON-serializable dicts
if "ai_message" in response_data:
    response_data["ai_message"] = response_data["ai_message"].model_dump(mode='json')
if "conversation" in response_data:
    response_data["conversation"] = response_data["conversation"].model_dump(mode='json')

complete_event = StreamCompleteResponse(response=response_data)
yield f"data: {json.dumps(complete_event.model_dump())}\n\n"
```

#### UUID Handling
Added UUID encoders to Pydantic model configs:
```python
model_config = {
    "from_attributes": True,
    "json_encoders": {datetime: lambda v: v.isoformat(), UUID: lambda v: str(v)},
}
```

### Return Type Annotations

Added proper type hints:
```python
async def process_chat_stream(
    self, request: ChatRequest, user_id: UUID
) -> AsyncGenerator[Dict[str, Any], None]:

async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> StreamingResponse:
```

## Testing

Created comprehensive tests to verify fixes:

1. **`test_fixes.py`**: Tests response structure compatibility and JSON serialization
2. **`test_cli_commands.py`**: Simulates actual CLI commands that were failing

All tests pass, confirming:
- ✅ Tools list validation error resolved
- ✅ Profiles list shows available profiles  
- ✅ Streaming JSON serialization works correctly
- ✅ CLI commands function as expected

## Migration Notes

These changes are **backward compatible** for:
- Existing API clients using the response data
- Database schema (no changes required)
- Authentication and authorization

The changes only affect:
- Response structure format (flattened instead of nested)
- Streaming event serialization (now properly typed)

## Usage Examples

### Tools List Command
```bash
# In chatbot CLI:
/tools list

# Now returns:
Available Tools (2/3 enabled):
 ✓ file_search: Search through files and documents...
 ✓ web_browse: Browse web pages and extract content...
 ✗ calculator: Perform mathematical calculations...
```

### Profiles List Command  
```bash
# In chatbot CLI:
/profile list

# Now returns:
Available LLM Profiles:
 * default: Default Profile (default)
   creative: Creative Profile
   analytical: Analytical Profile
```

### Streaming Chat
Streaming responses now work correctly without JSON serialization errors, providing real-time chat updates.