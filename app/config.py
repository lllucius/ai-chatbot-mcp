"""
Configuration management using Pydantic Settings.

This module provides centralized configuration management with environment
variable support, type validation, and secure defaults.

Current Date and Time (UTC): 2025-07-14 04:41:14
Current User: lllucius
"""

import logging
import os
from typing import Any, Dict, List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden using environment variables.
    For nested settings, use double underscores (e.g., DATABASE__URL).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Configuration
    app_name: str = Field(default="AI Chatbot Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="Production-grade AI chatbot with RAG capabilities and FastMCP integration",
        description="Application description",
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security Configuration
    secret_key: str = Field(
        default="change-this-super-secret-key-in-production-must-be-32-chars-minimum",
        description="Secret key for JWT tokens",
        min_length=32,
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=1440, description="Access token expiration in minutes", gt=0
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ai_chatbot",
        description="Database connection URL",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(
        default="your-openai-api-key-here", description="OpenAI API key"
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL"
    )
    openai_chat_model: str = Field(
        default="gpt-4", description="OpenAI chat model to use"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model to use"
    )

    # FastMCP Configuration
    mcp_enabled: bool = Field(default=True, description="Enable FastMCP integration")
    mcp_timeout: int = Field(default=30, description="MCP operation timeout in seconds")

    # CORS Configuration - Use Union to accept both string and list
    allowed_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Allowed CORS origins (comma-separated string or JSON list)",
    )
    allowed_methods: Union[str, List[str]] = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        description="Allowed HTTP methods (comma-separated string or JSON list)",
    )
    allowed_headers: Union[str, List[str]] = Field(
        default="*",
        description="Allowed HTTP headers (comma-separated string or JSON list)",
    )

    # File Upload Configuration
    max_file_size: int = Field(
        default=10485760, description="Maximum file size in bytes", gt=0  # 10MB
    )
    allowed_file_types: Union[str, List[str]] = Field(
        default="pdf,docx,txt,md,rtf",
        description="Allowed file types for upload (comma-separated string or JSON list)",
    )
    upload_directory: str = Field(
        default="./uploads", description="Directory for file uploads"
    )

    # Text Processing Configuration
    default_chunk_size: int = Field(
        default=1000, description="Default chunk size for text processing", gt=0
    )
    default_chunk_overlap: int = Field(
        default=200, description="Default chunk overlap for text processing", ge=0
    )
    
    # Enhanced Document Processing Configuration
    max_chunk_size: int = Field(
        default=4000,
        description="Maximum allowed chunk size",
        ge=500,
        le=8000
    )
    min_chunk_size: int = Field(
        default=100,
        description="Minimum allowed chunk size", 
        ge=50,
        le=500
    )
    max_chunk_overlap: int = Field(
        default=1000,
        description="Maximum allowed chunk overlap",
        ge=0,
        le=2000
    )
    
    # Embedding Configuration
    enable_metadata_embedding: bool = Field(
        default=True,
        description="Include metadata in embedding generation"
    )
    embedding_batch_size: int = Field(
        default=10,
        description="Batch size for embedding generation",
        ge=1,
        le=100
    )
    
    # Document Preprocessing Configuration
    enable_text_preprocessing: bool = Field(
        default=True,
        description="Enable advanced text preprocessing"
    )
    normalize_unicode: bool = Field(
        default=True,
        description="Normalize Unicode characters"
    )
    remove_extra_whitespace: bool = Field(
        default=True,
        description="Remove extra whitespace and normalize line endings"
    )
    language_detection: bool = Field(
        default=True,
        description="Enable language detection for chunks"
    )
    
    # Background Processing Configuration
    max_concurrent_processing: int = Field(
        default=3,
        description="Maximum concurrent document processing tasks",
        ge=1,
        le=10
    )
    processing_timeout: int = Field(
        default=1800,  # 30 minutes
        description="Processing timeout in seconds",
        ge=300,
        le=7200
    )
    
    vector_dimension: int = Field(
        default=3072, description="Vector embedding dimension", gt=0
    )

    # Rate Limiting Configuration
    rate_limit_requests: int = Field(
        default=100, description="Rate limit requests per period", gt=0
    )
    rate_limit_period: int = Field(
        default=60, description="Rate limit period in seconds", gt=0
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @field_validator("allowed_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            return [method.strip().upper() for method in v.split(",") if method.strip()]
        elif isinstance(v, list):
            return [method.upper() for method in v]
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    @field_validator("allowed_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return ["*"]
            if v.strip() == "*":
                return ["*"]
            return [header.strip() for header in v.split(",") if header.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return ["pdf", "docx", "txt", "md", "rtf"]
            return [ft.strip().lower() for ft in v.split(",") if ft.strip()]
        elif isinstance(v, list):
            return [ft.lower() for ft in v if ft]
        return ["pdf", "docx", "txt", "md", "rtf"]

    @field_validator("upload_directory")
    @classmethod
    def validate_upload_directory(cls, v):
        """Ensure upload directory exists."""
        os.makedirs(v, exist_ok=True)
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug

    @property
    def mcp_servers(self) -> Dict[str, Any]:
        """
        Get MCP server configurations for MCPConfigTransport.

        Returns configurations compatible with MCPConfigTransport.
        """
        return {
            "http": {
                "command": "npx",
                "args": [
                    "@modelcontextprotocol/server-filesystem",
                    "/tmp/mcp_workspace",
                ],
                "env": {},
                "working_directory": None,
                "required": True,
                "description": "File system operations (read, write, list files)",
            },
            "brave_search": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-brave-search"],
                "env": {
                    "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "your-brave-api-key")
                },
                "working_directory": None,
                "required": False,
                "description": "Web search capabilities via Brave Search API",
            },
            "memory": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-memory"],
                "env": {},
                "working_directory": None,
                "required": True,
                "description": "Persistent memory for conversations and context",
            },
        }


# Global settings instance
settings = Settings()

# Setup logger after settings are created
logger = logging.getLogger(__name__)

# Validate critical settings on import
if (
    settings.is_production
    and settings.secret_key
    == "change-this-super-secret-key-in-production-must-be-32-chars-minimum"
):
    raise ValueError("SECRET_KEY must be changed in production environment")

if settings.openai_api_key == "your-openai-api-key-here":
    import warnings

    warnings.warn(
        "OpenAI API key not configured - AI features will not work", UserWarning
    )
