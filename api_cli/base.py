"""
Base API client and utilities for the API-based CLI.

This module provides the core API client functionality using the AI Chatbot SDK,
authentication handling, console utilities, and common functions used across all CLI modules.
"""

import json
import os
from typing import Any, Dict, Optional, Union
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# Import the SDK
from client.ai_chatbot_sdk import AIChatbotSDK, ApiError

# Initialize Rich console
console = Console()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
TOKEN_FILE = Path.home() / ".ai-chatbot-cli" / "token"


class APIClient:
    """SDK-based client for API interactions."""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._sdk = AIChatbotSDK(base_url=self.base_url)
        
    def set_token(self, token: str):
        """Set authentication token."""
        self._sdk.set_token(token)
        
    def get_sdk(self) -> AIChatbotSDK:
        """Get the underlying SDK instance."""
        return self._sdk
    
    # Legacy methods for backward compatibility
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make GET request using SDK."""
        try:
            return self._sdk._request(endpoint, params=params)
        except ApiError as e:
            raise APIError(str(e), status_code=e.status)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make POST request using SDK."""
        try:
            if files:
                # Handle file uploads
                return self._sdk._request(endpoint, method="POST", files=files, data=data)
            else:
                return self._sdk._request(endpoint, method="POST", json=data)
        except ApiError as e:
            raise APIError(str(e), status_code=e.status)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make PUT request using SDK."""
        try:
            return self._sdk._request(endpoint, method="PUT", json=data)
        except ApiError as e:
            raise APIError(str(e), status_code=e.status)
    
    async def delete(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make DELETE request using SDK."""
        try:
            return self._sdk._request(endpoint, method="DELETE")
        except ApiError as e:
            raise APIError(str(e), status_code=e.status)


class APIError(Exception):
    """Custom exception for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# Console utility functions
def success_message(message: str):
    """Display success message."""
    console.print(f"[green]✓[/green] {message}")

def error_message(message: str):
    """Display error message."""
    console.print(f"[red]✗[/red] {message}")

def info_message(message: str):
    """Display info message."""
    console.print(f"[blue]ℹ[/blue] {message}")

def warning_message(message: str):
    """Display warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")

def format_json(data: Dict[str, Any]) -> str:
    """Format JSON data for display."""
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

def get_client_with_auth() -> APIClient:
    """Get API client with authentication token."""
    from api_cli.auth import get_auth_manager
    
    client = APIClient()
    auth_manager = get_auth_manager()
    
    if auth_manager.has_token():
        token = auth_manager.get_token()
        client.set_token(token)
    else:
        error_message("Not authenticated. Please run 'python api_manage.py login' first.")
        import typer
        raise typer.Exit(1)
    
    return client

def get_sdk_with_auth() -> AIChatbotSDK:
    """Get authenticated SDK instance."""
    from api_cli.auth import get_auth_manager
    
    auth_manager = get_auth_manager()
    
    if auth_manager.has_token():
        token = auth_manager.get_token()
        sdk = AIChatbotSDK(base_url=API_BASE_URL)
        sdk.set_token(token)
        return sdk
    else:
        error_message("Not authenticated. Please run 'python api_manage.py login' first.")
        import typer
        raise typer.Exit(1)


# Environment and configuration helpers
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