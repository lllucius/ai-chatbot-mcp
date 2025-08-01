"""
Configuration management for the AI Chatbot Terminal Client.

This module provides unified configuration management that extends the main app
configuration with client-specific settings. It uses the same .env file as the
main application for consistent configuration across all components.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientConfig(BaseSettings):
    """
    Client configuration that includes all necessary settings for both app and client.

    This class contains all settings needed for the client while sharing the same
    .env file structure as the main application.

    All settings can be provided via:
    - Environment variables (both APP_ and CLIENT_ prefixes supported)
    - The shared .env file used by the main application
    - Command line arguments (when using CLI)

    Example:
        # Via environment variables
        export API_BASE_URL="http://localhost:8000"
        export CLIENT_USERNAME="admin"

        # Via .env file (shared with main app)
        API_BASE_URL=http://localhost:8000
        CLIENT_USERNAME=admin
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Configuration (from main app)
    app_name: str = Field(default="AI Chatbot Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security Configuration (from main app)
    secret_key: str = Field(
        default="change-this-super-secret-key-in-production-must-be-32-chars-minimum",
        description="Secret key for JWT tokens",
        min_length=32,
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=1440, description="Access token expiration in minutes", gt=0
    )

    # Database Configuration (from main app)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ai_chatbot",
        description="Database connection URL",
    )

    # OpenAI Configuration (from main app)
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

    # API Configuration (shared and client-specific)
    api_base_url: str = Field(
        default="http://localhost:8000", description="Base URL of the AI Chatbot API"
    )
    api_timeout: int = Field(
        default=120, description="Timeout for API requests in seconds"
    )

    # Authentication (client-specific)
    client_username: Optional[str] = Field(
        default=None,
        description="Username for authentication (will prompt if not provided)",
    )
    client_password: Optional[str] = Field(
        default=None,
        description="Password for authentication (will prompt if not provided)",
    )
    client_token_file: Optional[str] = Field(
        default=None, description="File to store authentication token for reuse"
    )

    # Default Chat Settings (client-specific)
    client_default_use_rag: bool = Field(
        default=True, description="Enable RAG by default for new conversations"
    )
    client_default_use_tools: bool = Field(
        default=True, description="Enable tools by default for new conversations"
    )
    client_default_prompt_name: Optional[str] = Field(
        default=None, description="Default prompt to use from registry"
    )
    client_default_profile_name: Optional[str] = Field(
        default=None, description="Default LLM profile to use from registry"
    )

    # UI Preferences (client-specific)
    client_spinner_enabled: bool = Field(
        default=True, description="Show loading spinner during AI responses"
    )
    client_auto_title: bool = Field(
        default=True,
        description="Automatically generate conversation titles if not provided",
    )
    client_max_history_display: int = Field(
        default=50, description="Maximum number of messages to display in history"
    )

    # Advanced Features (client-specific)
    client_enable_streaming: bool = Field(
        default=False, description="Enable streaming responses (if supported by API)"
    )
    client_save_conversations: bool = Field(
        default=True, description="Automatically save conversations locally"
    )
    client_conversation_backup_dir: Optional[str] = Field(
        default=None, description="Directory to save conversation backups"
    )

    # Debug and Development (client-specific)
    client_debug_mode: bool = Field(
        default=False, description="Enable debug output and verbose logging for client"
    )

    @property
    def effective_debug(self) -> bool:
        """
        Get effective debug mode considering both app and client settings.

        Returns:
            bool: True if either app debug or client debug mode is enabled
        """
        return self.debug or self.client_debug_mode

    @property
    def is_development(self) -> bool:
        """
        Check if running in development mode.

        Returns:
            bool: True if in development mode
        """
        return self.debug

    @property
    def is_production(self) -> bool:
        """
        Check if running in production mode.

        Returns:
            bool: True if in production mode
        """
        return not self.debug


# Legacy alias for backwards compatibility
ChatbotConfig = ClientConfig


def load_config(config_file: Optional[str] = None) -> ClientConfig:
    """
    Load configuration from environment variables and optional config file.

    Args:
        config_file: Optional path to configuration file (.env format)
                    If not provided, uses the shared .env file from the app

    Returns:
        ClientConfig: Loaded configuration object with all app and client settings

    Example:
        >>> config = load_config()
        >>> print(config.api_base_url)
        'http://localhost:8000'
        >>> print(config.client_username)
        None
    """
    if config_file and Path(config_file).exists():
        return ClientConfig(_env_file=config_file)
    return ClientConfig()


def get_config_dir() -> Path:
    """
    Get the configuration directory for storing user settings.

    Creates the directory if it doesn't exist.

    Returns:
        Path: User configuration directory path

    Example:
        >>> config_dir = get_config_dir()
        >>> print(config_dir)
        /home/user/.config/ai-chatbot
    """
    config_dir = Path.home() / ".config" / "ai-chatbot"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_default_token_file() -> str:
    """
    Get the default token file path for storing authentication tokens.

    Returns:
        str: Full path to the default token file

    Example:
        >>> token_file = get_default_token_file()
        >>> print(token_file)
        /home/user/.config/ai-chatbot/token
    """
    return str(get_config_dir() / "token")


def get_default_backup_dir() -> str:
    """
    Get the default conversation backup directory.

    Creates the directory if it doesn't exist.

    Returns:
        str: Full path to the default backup directory

    Example:
        >>> backup_dir = get_default_backup_dir()
        >>> print(backup_dir)
        /home/user/.config/ai-chatbot/conversations
    """
    backup_dir = get_config_dir() / "conversations"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return str(backup_dir)


# Global configuration instance
config = ClientConfig()
