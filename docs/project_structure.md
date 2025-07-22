# AI Chatbot Platform - Project Structure

```
ai-chatbot-platform/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection and session management
│   ├── dependencies.py        # FastAPI dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # User model
│   │   ├── document.py       # Document and chunk models
│   │   ├── conversation.py   # Conversation and message models
│   │   └── base.py           # Base model class
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py           # User Pydantic schemas
│   │   ├── document.py       # Document Pydantic schemas
│   │   ├── conversation.py   # Conversation Pydantic schemas
│   │   ├── auth.py           # Authentication schemas
│   │   └── common.py         # Common schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py           # API dependencies
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── users.py          # User management endpoints
│   │   ├── documents.py      # Document management endpoints
│   │   ├── conversations.py  # Chat and conversation endpoints
│   │   ├── search.py         # RAG search endpoints
│   │   └── health.py         # Health check endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication service
│   │   ├── user.py           # User service
│   │   ├── document.py       # Document processing service
│   │   ├── embedding.py      # Embedding service
│   │   ├── search.py         # RAG search service
│   │   ├── openai_client.py  # OpenAI integration
│   │   └── mcp_client.py     # MCP tool calling service
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py       # Security utilities
│   │   ├── text_processing.py # Text chunking and processing
│   │   ├── file_processing.py # File upload and processing
│   │   └── logging.py        # Logging configuration
│   └── core/
│       ├── __init__.py
│       ├── exceptions.py     # Custom exceptions
│       └── middleware.py     # Custom middleware
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test configuration
│   ├── test_auth.py         # Authentication tests
│   ├── test_documents.py    # Document tests
│   ├── test_search.py       # Search tests
│   └── test_conversations.py # Conversation tests
├── scripts/
│   ├── startup.py           # Application startup script
│   ├── example_usage.py     # Example usage demonstrations
│   └── manage.py            # Database and user management CLI
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables example
├── README.md               # Comprehensive documentation
└── project_structure.md    # This file
```

## File Descriptions

### Core Application Files
- **app/main.py**: FastAPI application entry point with router registration
- **app/config.py**: Environment configuration using Pydantic settings
- **app/database.py**: Async database connection and session management
- **app/dependencies.py**: FastAPI dependency injection functions

### Models (SQLAlchemy)
- **app/models/base.py**: Base model with common fields and configurations
- **app/models/user.py**: User model with authentication fields
- **app/models/document.py**: Document and chunk models with vector fields
- **app/models/conversation.py**: Conversation and message models

### Schemas (Pydantic)
- **app/schemas/**: Request/response models for API validation
- **app/schemas/auth.py**: Authentication-related schemas
- **app/schemas/user.py**: User management schemas
- **app/schemas/document.py**: Document processing schemas
- **app/schemas/conversation.py**: Chat and conversation schemas
- **app/schemas/common.py**: Shared schemas and base classes

### API Endpoints
- **app/api/auth.py**: User registration, login, token management
- **app/api/users.py**: User profile and management endpoints
- **app/api/documents.py**: Document upload, processing, management
- **app/api/conversations.py**: Chat endpoints with OpenAI integration
- **app/api/search.py**: RAG search endpoints (vector, text, hybrid, MMR)
- **app/api/health.py**: Health checks and system metadata

### Services (Business Logic)
- **app/services/auth.py**: Authentication and authorization logic
- **app/services/user.py**: User management operations
- **app/services/document.py**: Document processing and chunking
- **app/services/embedding.py**: Text embedding generation
- **app/services/search.py**: RAG search implementations
- **app/services/openai_client.py**: OpenAI API integration
- **app/services/mcp_client.py**: MCP tool calling service

### Utilities
- **app/utils/security.py**: Password hashing, JWT tokens
- **app/utils/text_processing.py**: Text chunking and preprocessing
- **app/utils/file_processing.py**: File upload and format handling
- **app/utils/logging.py**: Structured logging configuration

### Core Components
- **app/core/exceptions.py**: Custom exception classes
- **app/core/middleware.py**: Request/response middleware

### Scripts
- **scripts/startup.py**: Application initialization script
- **scripts/manage.py**: CLI for database and user management
- **scripts/example_usage.py**: Usage examples and demonstrations

### Tests
- **tests/**: Comprehensive test suite with async test support
- **tests/conftest.py**: Test configuration and fixtures