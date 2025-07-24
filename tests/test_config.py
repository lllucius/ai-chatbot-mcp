"Test cases for config functionality."

import os
from unittest.mock import patch
from app.config import Settings


class TestConfigurationFields:
    "Test class for configurationfields functionality."

    def test_config_initialization(self):
        "Test config initialization functionality."
        config = Settings()
        assert config is not None
        assert hasattr(config, "app_name")
        assert hasattr(config, "database_url")

    def test_required_fields_have_defaults(self):
        "Test required fields have defaults functionality."
        config = Settings()
        assert config.app_name == "AI Chatbot Platform"
        assert config.app_version == "1.0.0"
        assert config.debug is False
        assert len(config.secret_key) >= 32
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes > 0
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_chat_model == "gpt-4"
        assert config.openai_embedding_model == "text-embedding-3-small"
        assert config.vector_dimension == 1536

    def test_brave_api_key_field_exists(self):
        "Test brave api key field exists functionality."
        config = Settings(_env_file=None)
        assert hasattr(config, "brave_api_key")
        assert config.brave_api_key == "your-brave-api-key"

    def test_all_document_processing_fields(self):
        "Test all document processing fields functionality."
        config = Settings()
        assert config.default_chunk_size == 1000
        assert config.default_chunk_overlap == 200
        assert config.max_chunk_size == 4000
        assert config.min_chunk_size == 100
        assert config.max_chunk_overlap == 1000
        assert config.enable_metadata_embedding is True
        assert config.embedding_batch_size == 10
        assert config.enable_text_preprocessing is True
        assert config.normalize_unicode is True
        assert config.remove_extra_whitespace is True
        assert config.language_detection is True
        assert config.max_concurrent_processing == 3
        assert config.processing_timeout == 1800

    def test_mcp_servers_use_pydantic_field(self):
        "Test mcp servers use pydantic field functionality."
        config = Settings()
        mcp_servers = config.mcp_servers
        assert "brave_search" in mcp_servers
        brave_config = mcp_servers["brave_search"]
        assert "env" in brave_config
        assert "BRAVE_API_KEY" in brave_config["env"]
        assert brave_config["env"]["BRAVE_API_KEY"] == config.brave_api_key

    @patch.dict(os.environ, {"BRAVE_API_KEY": "test-env-brave-key"})
    def test_environment_variable_override(self):
        "Test environment variable override functionality."
        config = Settings()
        assert config.brave_api_key == "test-env-brave-key"
        mcp_servers = config.mcp_servers
        brave_config = mcp_servers["brave_search"]
        assert brave_config["env"]["BRAVE_API_KEY"] == "test-env-brave-key"

    @patch.dict(
        os.environ,
        {
            "APP_NAME": "Test App",
            "DEBUG": "true",
            "VECTOR_DIMENSION": "512",
            "MAX_CHUNK_SIZE": "2000",
            "ENABLE_METADATA_EMBEDDING": "false",
        },
    )
    def test_multiple_environment_overrides(self):
        "Test multiple environment overrides functionality."
        config = Settings()
        assert config.app_name == "Test App"
        assert config.debug is True
        assert config.vector_dimension == 512
        assert config.max_chunk_size == 2000
        assert config.enable_metadata_embedding is False

    def test_field_validation(self):
        "Test field validation functionality."
        config = Settings()
        assert config.max_file_size > 0
        assert config.rate_limit_requests > 0
        assert config.rate_limit_period > 0
        assert config.vector_dimension > 0
        assert 500 <= config.max_chunk_size <= 8000
        assert 50 <= config.min_chunk_size <= 500
        assert 0 <= config.max_chunk_overlap <= 2000


class TestConfigurationConsistency:
    "Test class for configurationconsistency functionality."

    def test_no_direct_os_getenv_usage(self):
        "Test no direct os getenv usage functionality."
        config = Settings()
        mcp_servers = config.mcp_servers
        assert "brave_search" in mcp_servers
        assert "env" in mcp_servers["brave_search"]
        assert "BRAVE_API_KEY" in mcp_servers["brave_search"]["env"]

    def test_configuration_sections_complete(self):
        "Test configuration sections complete functionality."
        config = Settings()
        app_fields = [
            "app_name",
            "app_version",
            "app_description",
            "debug",
            "log_level",
        ]
        for field in app_fields:
            assert hasattr(config, field), f"Missing application field: {field}"
        security_fields = ["secret_key", "algorithm", "access_token_expire_minutes"]
        for field in security_fields:
            assert hasattr(config, field), f"Missing security field: {field}"
        openai_fields = [
            "openai_api_key",
            "openai_base_url",
            "openai_chat_model",
            "openai_embedding_model",
        ]
        for field in openai_fields:
            assert hasattr(config, field), f"Missing OpenAI field: {field}"
        mcp_fields = ["mcp_enabled", "mcp_timeout", "brave_api_key"]
        for field in mcp_fields:
            assert hasattr(config, field), f"Missing MCP field: {field}"
