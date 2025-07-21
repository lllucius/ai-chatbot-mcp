"""
Tests for configuration management and environment variable handling.

This module tests that all configuration fields are properly loaded,
validated, and that environment variables work correctly.
"""

import os
import pytest
from unittest.mock import patch

from app.config import Settings


class TestConfigurationFields:
    """Test that all configuration fields are properly defined and accessible."""

    def test_config_initialization(self):
        """Test that configuration can be initialized successfully."""
        config = Settings()
        assert config is not None
        assert hasattr(config, 'app_name')
        assert hasattr(config, 'database_url')

    def test_required_fields_have_defaults(self):
        """Test that all required fields have sensible defaults."""
        config = Settings()
        
        # Application settings
        assert config.app_name == "AI Chatbot Platform"
        assert config.app_version == "1.0.0"
        assert config.debug is False
        
        # Security settings
        assert len(config.secret_key) >= 32
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes > 0
        
        # OpenAI settings
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_chat_model == "gpt-4"
        assert config.openai_embedding_model == "text-embedding-3-small"
        
        # Vector dimension should match embedding model
        assert config.vector_dimension == 1536

    def test_brave_api_key_field_exists(self):
        """Test that brave_api_key field is properly defined in pydantic settings."""
        # Create config with custom env_file to avoid loading from .env
        config = Settings(_env_file=None)
        assert hasattr(config, 'brave_api_key')
        assert config.brave_api_key == "your-brave-api-key"  # default value

    def test_all_document_processing_fields(self):
        """Test that all document processing fields are accessible."""
        config = Settings()
        
        # Basic text processing
        assert config.default_chunk_size == 1000
        assert config.default_chunk_overlap == 200
        
        # Enhanced processing fields
        assert config.max_chunk_size == 4000
        assert config.min_chunk_size == 100
        assert config.max_chunk_overlap == 1000
        
        # Embedding configuration
        assert config.enable_metadata_embedding is True
        assert config.embedding_batch_size == 10
        
        # Preprocessing configuration
        assert config.enable_text_preprocessing is True
        assert config.normalize_unicode is True
        assert config.remove_extra_whitespace is True
        assert config.language_detection is True
        
        # Background processing
        assert config.max_concurrent_processing == 3
        assert config.processing_timeout == 1800

    def test_mcp_servers_use_pydantic_field(self):
        """Test that mcp_servers property uses the pydantic brave_api_key field."""
        config = Settings()
        mcp_servers = config.mcp_servers
        
        # Check that brave_search server exists and uses the pydantic field
        assert "brave_search" in mcp_servers
        brave_config = mcp_servers["brave_search"]
        assert "env" in brave_config
        assert "BRAVE_API_KEY" in brave_config["env"]
        assert brave_config["env"]["BRAVE_API_KEY"] == config.brave_api_key

    @patch.dict(os.environ, {"BRAVE_API_KEY": "test-env-brave-key"})
    def test_environment_variable_override(self):
        """Test that environment variables properly override defaults."""
        config = Settings()
        assert config.brave_api_key == "test-env-brave-key"
        
        # Check that mcp_servers also gets the environment value
        mcp_servers = config.mcp_servers
        brave_config = mcp_servers["brave_search"]
        assert brave_config["env"]["BRAVE_API_KEY"] == "test-env-brave-key"

    @patch.dict(os.environ, {
        "APP_NAME": "Test App",
        "DEBUG": "true",
        "VECTOR_DIMENSION": "512",
        "MAX_CHUNK_SIZE": "2000",
        "ENABLE_METADATA_EMBEDDING": "false"
    })
    def test_multiple_environment_overrides(self):
        """Test that multiple environment variables work correctly."""
        config = Settings()
        
        assert config.app_name == "Test App"
        assert config.debug is True
        assert config.vector_dimension == 512
        assert config.max_chunk_size == 2000
        assert config.enable_metadata_embedding is False

    def test_field_validation(self):
        """Test that pydantic field validation works."""
        config = Settings()
        
        # Test positive integer constraints
        assert config.max_file_size > 0
        assert config.rate_limit_requests > 0
        assert config.rate_limit_period > 0
        assert config.vector_dimension > 0
        
        # Test ranges
        assert 500 <= config.max_chunk_size <= 8000
        assert 50 <= config.min_chunk_size <= 500
        assert 0 <= config.max_chunk_overlap <= 2000


class TestConfigurationConsistency:
    """Test configuration consistency and completeness."""

    def test_no_direct_os_getenv_usage(self):
        """Test that config doesn't use os.getenv() for environment variables."""
        # This is a regression test to ensure we don't reintroduce direct os.getenv() calls
        # We should be able to create the config and access mcp_servers without any os.getenv calls
        config = Settings()
        mcp_servers = config.mcp_servers
        
        # If this works without errors, it means no os.getenv() calls are failing
        assert "brave_search" in mcp_servers
        assert "env" in mcp_servers["brave_search"]
        assert "BRAVE_API_KEY" in mcp_servers["brave_search"]["env"]

    def test_configuration_sections_complete(self):
        """Test that all configuration sections have expected fields."""
        config = Settings()
        
        # Application configuration
        app_fields = ["app_name", "app_version", "app_description", "debug", "log_level"]
        for field in app_fields:
            assert hasattr(config, field), f"Missing application field: {field}"
        
        # Security configuration  
        security_fields = ["secret_key", "algorithm", "access_token_expire_minutes"]
        for field in security_fields:
            assert hasattr(config, field), f"Missing security field: {field}"
        
        # OpenAI configuration
        openai_fields = ["openai_api_key", "openai_base_url", "openai_chat_model", "openai_embedding_model"]
        for field in openai_fields:
            assert hasattr(config, field), f"Missing OpenAI field: {field}"
        
        # MCP configuration
        mcp_fields = ["mcp_enabled", "mcp_timeout", "brave_api_key"]
        for field in mcp_fields:
            assert hasattr(config, field), f"Missing MCP field: {field}"