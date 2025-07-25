"""
Configuration management for the AI Chatbot Terminal Client.

This module provides configuration management for the chatbot client, supporting
environment variables, config files, and command-line arguments.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ChatbotConfig(BaseSettings):
    """
    Configuration settings for the AI Chatbot Terminal Client.

    Settings can be provided via:
    - Environment variables (prefixed with CHATBOT_)
    - Configuration file (.env or specified file)
    - Command line arguments (when using CLI)

    Example:
        # Via environment variables
        export CHATBOT_API_URL="http://localhost:8000"
        export CHATBOT_USERNAME="admin"

        # Via .env file
        CHATBOT_API_URL=http://localhost:8000
        CHATBOT_USERNAME=admin
    """

    # API Configuration
    api_url: str = Field(
        default="http://localhost:8000", description="Base URL of the AI Chatbot API"
    )

    # Authentication
    username: Optional[str] = Field(
        default=None,
        description="Username for authentication (will prompt if not provided)",
    )
    password: Optional[str] = Field(
        default=None,
        description="Password for authentication (will prompt if not provided)",
    )
    token_file: Optional[str] = Field(
        default=None, description="File to store authentication token for reuse"
    )

    # Default Chat Settings
    default_use_rag: bool = Field(
        default=True, description="Enable RAG by default for new conversations"
    )
    default_use_tools: bool = Field(
        default=True, description="Enable tools by default for new conversations"
    )
    default_prompt_name: Optional[str] = Field(
        default=None, description="Default prompt to use from registry"
    )
    default_profile_name: Optional[str] = Field(
        default=None, description="Default LLM profile to use from registry"
    )

    # UI Preferences
    spinner_enabled: bool = Field(
        default=True, description="Show loading spinner during AI responses"
    )
    auto_title: bool = Field(
        default=True,
        description="Automatically generate conversation titles if not provided",
    )
    max_history_display: int = Field(
        default=50, description="Maximum number of messages to display in history"
    )

    # Advanced Features
    enable_streaming: bool = Field(
        default=False, description="Enable streaming responses (if supported by API)"
    )
    save_conversations: bool = Field(
        default=True, description="Automatically save conversations locally"
    )
    conversation_backup_dir: Optional[str] = Field(
        default=None, description="Directory to save conversation backups"
    )

    # Debug and Development
    debug_mode: bool = Field(default=False, description="Enable debug output and verbose logging")
    request_timeout: int = Field(default=120, description="Timeout for API requests in seconds")

    model_config = {
        "env_prefix": "CHATBOT_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def load_config(config_file: Optional[str] = None) -> ChatbotConfig:
    """
    Load configuration from environment variables and optional config file.

    Args:
        config_file: Optional path to configuration file (.env format)

    Returns:
        Loaded configuration object
    """
    if config_file and Path(config_file).exists():
        return ChatbotConfig(_env_file=config_file)
    return ChatbotConfig()


def get_config_dir() -> Path:
    """Get the configuration directory for storing user settings."""
    config_dir = Path.home() / ".config" / "ai-chatbot"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_default_token_file() -> str:
    """Get the default token file path."""
    return str(get_config_dir() / "token")


def get_default_backup_dir() -> str:
    """Get the default conversation backup directory."""
    backup_dir = get_config_dir() / "conversations"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return str(backup_dir)
