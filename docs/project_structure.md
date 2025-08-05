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
│   ├── schemas/             # DEPRECATED - schemas moved to shared/schemas
│   │   └── __init__.py      # Deprecation notice
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
├── shared/                  # Shared schemas between API and SDK
│   └── schemas/             # Pydantic schemas for API and client
│       ├── __init__.py      # Schema exports and validation
│       ├── user.py          # User-related schemas
│       ├── document.py      # Document and search schemas
│       ├── conversation.py  # Conversation and message schemas
│       ├── auth.py          # Authentication schemas
│       ├── common.py        # Common/base schemas and responses
│       ├── mcp.py           # MCP (Model Context Protocol) schemas
│       ├── admin.py         # Administrative schemas
│       ├── analytics.py     # Analytics and reporting schemas
│       ├── task_responses.py # Task and monitoring response schemas
│       ├── search_responses.py # Search response schemas
│       └── *_responses.py   # Various response schemas
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
**Note**: Schema organization has been refactored for better code sharing between API and SDK.

- **shared/schemas/**: Centralized schema definitions shared between API server and client SDK
  - **shared/schemas/auth.py**: Authentication-related schemas (login, registration, tokens)
  - **shared/schemas/user.py**: User management schemas (create, update, response)
  - **shared/schemas/document.py**: Document processing and search schemas
  - **shared/schemas/conversation.py**: Chat and conversation schemas
  - **shared/schemas/common.py**: Base response classes and pagination schemas
  - **shared/schemas/mcp.py**: Model Context Protocol (MCP) schemas
  - **shared/schemas/admin.py**: Administrative operation schemas
  - **shared/schemas/analytics.py**: Analytics and reporting schemas
  - **shared/schemas/*_responses.py**: Specialized response schemas for different modules

- **app/schemas/**: DEPRECATED - Contains only a deprecation notice directing to shared/schemas

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