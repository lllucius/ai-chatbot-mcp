"""
Base API client and utilities for the async API-based CLI.

This module provides the core async API client functionality using the AI Chatbot SDK,
authentication handling, console utilities, and common functions used across all CLI modules.

All functions are async and use the async SDK for improved performance.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

# Import the async SDK and config
from client.ai_chatbot_sdk import AIChatbotSDK, ApiError
from client.config import load_config

# Initialize Rich console
console = Console()

# Global configuration instance
config = load_config()

# Configuration
API_BASE_URL = config.api_base_url
API_TIMEOUT = config.api_timeout
TOKEN_FILE = Path.home() / ".ai-chatbot-cli" / "token"


class APIClient:
    """
    Async SDK-based client for API interactions.
    
    Provides a unified interface for CLI modules to interact with the API
    using the async SDK with proper context management.
    """
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = API_TIMEOUT):
        """
        Initialize the async API client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._sdk = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._sdk = AIChatbotSDK(base_url=self.base_url, timeout=self.timeout)
        await self._sdk.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._sdk:
            await self._sdk.__aexit__(exc_type, exc_val, exc_tb)
        
    def set_token(self, token: str):
        """
        Set authentication token.
        
        Args:
            token: JWT token for authentication
        """
        if self._sdk:
            self._sdk.set_token(token)
        
    def get_sdk(self) -> AIChatbotSDK:
        """
        Get the underlying SDK instance.
        
        Returns:
            AIChatbotSDK: The async SDK instance
        """
        return self._sdk


# Global client instance (will be initialized per command)
_current_client: Optional[APIClient] = None


async def get_sdk_with_auth() -> AIChatbotSDK:
    """
    Get an authenticated SDK instance for use in CLI commands.
    
    This function loads a saved token and returns a ready-to-use SDK instance.
    
    Returns:
        AIChatbotSDK: Authenticated async SDK instance
        
    Raises:
        SystemExit: If authentication fails
    """
    global _current_client
    
    if not _current_client:
        _current_client = APIClient()
        await _current_client.__aenter__()
    
    # Load saved token
    token = load_token()
    if token:
        _current_client.set_token(token)
        
        # Verify token is still valid
        try:
            await _current_client.get_sdk().auth.me()
            return _current_client.get_sdk()
        except ApiError:
            error_message("Authentication token expired. Please login again.")
            raise SystemExit(1)
    else:
        error_message("No authentication token found. Please login first.")
        raise SystemExit(1)


def load_token() -> Optional[str]:
    """
    Load authentication token from file.
    
    Returns:
        str: The saved JWT token, or None if not found
    """
    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                return data.get('token')
    except Exception:
        pass
    return None


def save_token(token: str):
    """
    Save authentication token to file.
    
    Args:
        token: JWT token to save
    """
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            json.dump({'token': token}, f)
    except Exception as e:
        error_message(f"Failed to save token: {e}")


def clear_token():
    """Clear saved authentication token."""
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
    except Exception as e:
        error_message(f"Failed to clear token: {e}")


class APIError(Exception):
    """
    Custom exception for API errors.
    
    Attributes:
        status_code: HTTP status code if available
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
        """
        super().__init__(message)
        self.status_code = status_code


# Console utility functions
def success_message(message: str):
    """
    Display success message with green checkmark.
    
    Args:
        message: Success message to display
    """
    console.print(f"[green]✓[/green] {message}")


def error_message(message: str):
    """
    Display error message with red X.
    
    Args:
        message: Error message to display
    """
    console.print(f"[red]✗[/red] {message}")


def info_message(message: str):
    """
    Display info message with blue info icon.
    
    Args:
        message: Info message to display
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def warning_message(message: str):
    """
    Display warning message with yellow warning icon.
    
    Args:
        message: Warning message to display
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


def format_json(data: Dict[str, Any]) -> str:
    """
    Format JSON data for display.
    
    Args:
        data: Dictionary to format as JSON
        
    Returns:
        str: Formatted JSON string
    """
    return json.dumps(data, indent=2, default=str)

def display_table_data(data: list, title: str = "Results"):
    """Display data in a table format."""
    if not data:
        info_message("No data to display")
        return
    
    from rich.table import Table
    
    table = Table(title=title)
    
    # Get headers from first item
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        for header in headers:
            table.add_column(header.replace("_", " ").title(), style="cyan")
        
        for item in data:
            row = [str(item.get(header, "")) for header in headers]
            table.add_row(*row)
    else:
        table.add_column("Value", style="cyan")
        for item in data:
            table.add_row(str(item))
    
    console.print(table)

def display_key_value_pairs(data: Dict[str, Any], title: str = "Information"):
    """Display key-value pairs in a formatted panel."""
    content = "\n".join([f"[cyan]{key}:[/cyan] {value}" for key, value in data.items()])
    
    panel = Panel(
        content,
        title=title,
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)

def confirm_action(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    from rich.prompt import Confirm
    return Confirm.ask(message, default=default)

def paginate_results(data: list, page_size: int = 20) -> list:
    """Paginate results for display."""
    if len(data) <= page_size:
        return data
    
    total_pages = (len(data) + page_size - 1) // page_size
    
    info_message(f"Showing first {page_size} of {len(data)} results ({total_pages} pages total)")
    
    return data[:page_size]

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def format_file_size(size_bytes: int) -> str:
    """Format file size for display."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def handle_api_response(response: Optional[Dict[str, Any]], operation: str = "operation") -> Any:
    """Handle API response and display appropriate messages."""
    if not response:
        error_message(f"No response received from API for {operation}")
        return None
    
    if response.get("success", True):
        # Handle successful responses
        if "message" in response:
            success_message(response["message"])
        
        # Return data if present
        return response.get("data", response)
    else:
        # Handle error responses
        error_msg = response.get("message", response.get("detail", f"Unknown error in {operation}"))
        error_message(error_msg)
        return None

# Legacy function removed - use async get_sdk_with_auth() instead

# Legacy sync function removed - use async get_sdk_with_auth() instead


# Environment and configuration helpers (maintained for backward compatibility)
def load_environment():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv
    load_dotenv()

def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value from environment."""
    return os.getenv(key, default)

def save_config_value(key: str, value: str, config_file: str = ".env"):
    """Save configuration value to environment file."""
    config_path = Path(config_file)
    
    # Read existing config
    lines = []
    if config_path.exists():
        with open(config_path, "r") as f:
            lines = f.readlines()
    
    # Update or add the key
    key_found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            key_found = True
            break
    
    if not key_found:
        lines.append(f"{key}={value}\n")
    
    # Write back
    with open(config_path, "w") as f:
        f.writelines(lines)
