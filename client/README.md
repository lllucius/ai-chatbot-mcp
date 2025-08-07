# AI Chatbot Platform SDK

A comprehensive Python SDK for interacting with the AI Chatbot Platform API.

## Features

- **Authentication**: User registration, login, token management with persistence
- **Document Management**: Upload, process, search, and manage documents
- **Conversations**: AI-powered chat with RAG and tool calling support
- **Registry Integration**: Prompt templates, LLM profiles, and MCP tools
- **Health Monitoring**: System status and performance metrics
- **Enhanced Terminal Client**: Feature-rich command-line interface

## Installation

The SDK is included in the main project. Import it directly:

```python
from client.ai_chatbot_sdk import AIChatbotSDK
```

## Enhanced Terminal Client

The terminal client (`client/chatbot.py`) has been significantly enhanced with advanced features:

### Configuration Management

Create a `.env` file or use environment variables:

```bash
# .env file
CHATBOT_API_URL=http://localhost:8000
CHATBOT_USERNAME=your_username
CHATBOT_DEFAULT_USE_RAG=true
CHATBOT_DEFAULT_USE_TOOLS=true
CHATBOT_SPINNER_ENABLED=true
CHATBOT_DEBUG_MODE=false
```

### Running the Enhanced Client

```bash
# Basic usage
python client/chatbot.py

# With custom config file
python client/chatbot.py --config my_config.env

# With debug mode
python client/chatbot.py --debug
```

### New Commands

The enhanced client supports many new commands:

#### Basic Commands
- `/help` - Show comprehensive help
- `/settings` - Display current settings
- `/config` - Interactive configuration
- `/export` - Export current conversation
- `/search` - Search conversations
- `/logout` - Logout and clear saved token

#### Registry Commands
- `/prompt list` - List available prompts
- `/prompt use <name>` - Use a specific prompt
- `/prompt show [name]` - Show prompt details
- `/profile list` - List available LLM profiles
- `/profile use <name>` - Use a specific profile
- `/tools list` - List available tools
- `/tools enable/disable <name>` - Manage tools

#### Document Commands
- `/docs list` - List your documents
- `/docs upload <file>` - Upload a new document
- `/docs search <query>` - Search documents
- `/docs status <id>` - Check processing status

### Key Improvements

1. **Persistent Authentication**: Tokens are saved and reused automatically
2. **Configuration Management**: Flexible configuration via files and environment variables
3. **Registry Integration**: Full support for prompts, LLM profiles, and MCP tools
4. **Document Management**: Upload, search, and manage documents directly from the terminal
5. **Enhanced Conversation Management**: Search, filter, and export conversations
6. **Better Error Handling**: Graceful error recovery and debugging support
7. **Interactive Settings**: Configure preferences without editing files

## Installation

The SDK is included in the main project. Import it directly:

```python
from client.ai_chatbot_sdk import AIChatbotSDK
```

## Quick Start

```python
from client.ai_chatbot_sdk import AIChatbotSDK
from shared.schemas import (
    ChatRequest, 
    RegisterRequest, 
    PromptCreate, 
    LLMProfileCreate, 
    DocumentSearchRequest
)

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
- Integer-based identifiers
- Registry-based features (prompts, profiles, tools)
- Enhanced chat features with tool calling
- Comprehensive error handling