"""
AI Chatbot Platform - Enterprise-grade AI chatbot with advanced RAG capabilities.

This package provides a comprehensive, production-ready AI chatbot platform featuring
advanced document processing, semantic vector search, intelligent conversation management,
and extensive MCP (Model Context Protocol) tool integration. Built with FastAPI,
PostgreSQL with PGVector, and OpenAI integration for enterprise-scale deployment.

Platform Features:
- Advanced RAG (Retrieval-Augmented Generation) with semantic document search
- High-performance vector database with PGVector for similarity search
- Intelligent conversation management with context preservation and multi-turn chat
- Comprehensive document processing with support for multiple formats
- MCP tool integration for extensible AI agent capabilities
- Enterprise-grade security with JWT authentication and role-based access control

Architecture Overview:
- FastAPI-based REST API with comprehensive OpenAPI documentation
- Async SQLAlchemy with PostgreSQL and PGVector for scalable data management
- Service-oriented architecture with dependency injection and clean separation
- Comprehensive middleware stack for security, performance, and monitoring
- Modular design with extensible service and API architecture
- Production-ready deployment with Docker and container orchestration support

Core Components:
- API Layer: Comprehensive REST endpoints with authentication and validation
- Service Layer: Business logic with user management, conversation, and document services
- Data Layer: PostgreSQL with PGVector for structured and vector data storage
- AI Integration: OpenAI API integration with embedding and chat completion services
- Security Layer: JWT authentication, authorization, and audit logging
- Monitoring Layer: Comprehensive logging, metrics, and health check endpoints

Key Capabilities:
- Document upload, processing, and semantic search with advanced relevance ranking
- Real-time chat with AI models featuring context-aware responses
- User authentication and authorization with secure session management
- Administrative interfaces for user and system management
- Comprehensive API documentation with interactive Swagger UI
- Performance monitoring and operational observability

Technology Stack:
- FastAPI: High-performance async web framework with automatic API documentation
- PostgreSQL + PGVector: Scalable database with native vector operations
- SQLAlchemy: Async ORM with comprehensive database abstraction
- OpenAI API: State-of-the-art language models and embedding services
- Pydantic: Data validation and serialization with type safety
- JWT: Secure token-based authentication and authorization

Deployment Options:
- Docker containerization with multi-stage builds for production optimization
- Kubernetes deployment with auto-scaling and load balancing
- Cloud platform integration (AWS, GCP, Azure) with managed services
- Traditional server deployment with systemd service management
- Development environment with hot reloading and debugging support

Use Cases:
- Enterprise knowledge management with intelligent document search and Q&A
- Customer support automation with context-aware chatbot capabilities
- Internal documentation systems with semantic search and chat interfaces
- Educational platforms with AI-powered tutoring and content discovery
- Research and development tools with document analysis and summarization
- API platform for building custom AI-powered applications and integrations

Package Modules:
- api: REST API endpoints with comprehensive functionality and documentation
- services: Business logic layer with service classes and domain operations
- models: SQLAlchemy database models with relationships and constraints
- schemas: Pydantic models for request/response validation and serialization
- core: Core functionality including exceptions, logging, and utilities
- config: Configuration management with environment variable support
- middleware: Application middleware for security, performance, and monitoring
"""

from .main import app

__version__ = "1.0.0"
__description__ = "Production-grade AI chatbot platform with RAG capabilities"
__author__ = "lllucius"
__license__ = "MIT"


__all__ = ["app"]
