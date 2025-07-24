# AI Chatbot Platform SDK

A comprehensive Python SDK for interacting with the AI Chatbot Platform API.

## Features

- **Authentication**: User registration, login, token management
- **Document Management**: Upload, process, search, and manage documents
- **Conversations**: AI-powered chat with RAG and tool calling support
- **Registry Integration**: Prompt templates, LLM profiles, and MCP tools
- **Health Monitoring**: System status and performance metrics

## Installation

The SDK is included in the main project. Import it directly:

```python
from client.ai_chatbot_sdk import AIChatbotSDK
```

## Quick Start

```python
from client.ai_chatbot_sdk import AIChatbotSDK, ChatRequest, RegisterRequest

# Initialize the SDK
sdk = AIChatbotSDK("http://localhost:8000")

# Register a new user
user = sdk.auth.register(RegisterRequest(
    username="myuser",
    email="user@example.com",
    password="SecurePass123"
))

# Login and get token
token = sdk.auth.login("myuser", "SecurePass123")

# Chat with AI
response = sdk.conversations.chat(ChatRequest(
    user_message="What is machine learning?",
    conversation_title="ML Discussion",
    use_rag=True,
    use_tools=True,
    prompt_name="technical_assistant"  # Use registered prompt
))

print(response.ai_message.content)
```

## Advanced Features

### Registry-Based Management

#### Prompts
```python
# List available prompts
prompts = sdk.prompts.list_prompts(category="technical")

# Create a new prompt
prompt = sdk.prompts.create_prompt(PromptCreate(
    name="helpful_assistant",
    title="Helpful Assistant",
    content="You are a helpful AI assistant...",
    category="general"
))

# Use prompt in chat
response = sdk.conversations.chat(ChatRequest(
    user_message="Help me",
    prompt_name="helpful_assistant"
))
```

#### LLM Profiles
```python
# List available profiles
profiles = sdk.profiles.list_profiles()

# Create a custom profile
profile = sdk.profiles.create_profile(LLMProfileCreate(
    name="creative_writer",
    title="Creative Writer",
    model_name="gpt-4",
    parameters={
        "temperature": 0.9,
        "max_tokens": 2000,
        "top_p": 0.95
    }
))

# Use profile in chat
response = sdk.conversations.chat(ChatRequest(
    user_message="Write a story",
    profile_name="creative_writer"
))
```

#### MCP Tools
```python
# List available tools
tools = sdk.tools.list_tools()

# Enable/disable tools
sdk.tools.enable_tool("weather_tool")
sdk.tools.disable_tool("calculator")

# Chat with tools enabled
response = sdk.conversations.chat(ChatRequest(
    user_message="What's the weather like?",
    use_tools=True
))
```

### Document Management

```python
# Upload document
with open("document.pdf", "rb") as f:
    doc = sdk.documents.upload(f, title="Important Document")

# Check processing status
status = sdk.documents.status(doc.document.id)

# Search documents
results = sdk.search.search(DocumentSearchRequest(
    query="machine learning",
    limit=10,
    document_ids=[doc.document.id]
))
```

### Health Monitoring

```python
# Basic health check
health = sdk.health.basic()

# Detailed system information
details = sdk.health.detailed()

# Database connectivity
db_status = sdk.health.database()

# Performance metrics
metrics = sdk.health.metrics()
```

## Error Handling

```python
from client.ai_chatbot_sdk import ApiError

try:
    response = sdk.conversations.chat(ChatRequest(
        user_message="Hello"
    ))
except ApiError as e:
    print(f"API Error {e.status}: {e.body}")
```

## Configuration

The SDK automatically handles:
- Authentication token management
- Request/response serialization
- Error handling and retries
- Type validation with Pydantic models

## Models

All request and response models are based on Pydantic and provide:
- Type validation
- Automatic serialization/deserialization
- IDE autocompletion
- Runtime type checking

Key models:
- `UserResponse`, `RegisterRequest`, `LoginRequest`
- `DocumentResponse`, `DocumentUpdate`
- `ConversationResponse`, `MessageResponse`, `ChatRequest`, `ChatResponse`
- `PromptResponse`, `PromptCreate`
- `LLMProfileResponse`, `LLMProfileCreate`
- `ToolResponse`, `ToolsListResponse`

## Version Compatibility

This SDK is synchronized with the current API and supports:
- Modern Pydantic V2 models
- UUID-based identifiers
- Registry-based features (prompts, profiles, tools)
- Enhanced chat features with tool calling
- Comprehensive error handling