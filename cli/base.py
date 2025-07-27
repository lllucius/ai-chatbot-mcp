"""
Base utilities for the async API-based CLI.

Provides shared error classes and console utilities for the CLI.
No authentication or SDK logic is included here.
"""
import json
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel

from client.ai_chatbot_sdk import AIChatbotSDK
from client.config import load_config

TOKEN_FILE = Path.home() / ".ai-chatbot-cli" / "token"

console = Console()

class APIError(Exception):
    """
    Custom exception for API errors.
    
    Attributes:
        status_code: HTTP status code if available
    """
    def __init__(self, message: str, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class CLIManager:
    """
    Manages authentication for the CLI, including token storage,
    login/logout, and user status queries.
    """

    def __init__(self):
        self.token_file = TOKEN_FILE
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._config = load_config()
        self._sdk = AIChatbotSDK(
            base_url=self._config.api_base_url,
            timeout=self._config.api_timeout
        )
        self._load_token()

    def _load_token(self):
        """Load token from file, if it exists."""
        try:
            if self.token_file.exists():
                with open(self.token_file, "r") as f:
                    data = json.load(f)
                    self._sdk.set_token(data.get("access_token"))
        except Exception:
            self._sdk.clear_token()

    def save_token(self, token: str):
        """
        Save the authentication token to file with restrictive permissions.
        """
        try:
            data = {"access_token": token}
            with open(self.token_file, "w") as f:
                json.dump(data, f)
            self.token_file.chmod(0o600)
        except Exception as e:
            raise APIError(f"Failed to save authentication token: {str(e)}")

    def get_token(self) -> Optional[str]:
        """
        Return the current authentication token, or None if not set.
        """
        try:
            return self._sdk.get_token()
        except Exception as e:
            raise APIError(f"Failed to retrieve authentication token: {str(e)}")

    def has_token(self) -> bool:
        """
        Return True if an authentication token is present.
        """
        return self.get_token() is not None

    def clear_token(self):
        """
        Remove the stored authentication token from disk and memory.
        """
        try:
            self._sdk.clear_token()
        except Exception as e:
            raise APIError(f"Failed to clear authentication token: {str(e)}")

    async def login(self, username: str, password: str) -> Dict[str, str]:
        """
        Authenticate with the API and return the token data.

        Args:
            username: API username
            password: API password

        Returns:
            dict: Token data with at least 'access_token'

        Raises:
            APIError: If authentication fails
        """
        try:
            return await self._sdk.auth.login(username, password)
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise APIError("Invalid username or password")
            elif "422" in error_msg or "validation" in error_msg.lower():
                raise APIError("Invalid login request format")
            else:
                raise APIError(f"Login failed: {error_msg}")

    async def logout(self):
        """
        Log out from the API and clear the stored token.
        """
        if not self.has_token():
            return
        try:
            self._sdk.auth.logout()  # Sync method
        except Exception:
            pass
        finally:
            self.clear_token()

    async def get_current_user(self) -> Dict[str, str]:
        """
        Return information about the current user.

        Returns:
            dict: User info (keys: username, email, etc.)

        Raises:
            APIError: If token is missing or invalid
        """
        if not self.has_token():
            raise APIError("Not authenticated")
        try:
            response = await self._sdk.auth.me()
            if not response:
                raise APIError("Failed to get user information")
            return response.model_dump()
        except Exception:
            self.clear_token()
            raise APIError("Authentication token is invalid or expired")

# Singleton pattern for CLI use
_cli_manager: Optional[CLIManager] = None

async def get_cli_manager() -> CLIManager:
    """
    Return the singleton AuthManager instance (for CLI modules).
    """
    global _cli_manager
    if _cli_manager is None:
        _cli_manager = CLIManager()
    return _cli_manager

async def get_sdk() -> AIChatbotSDK:
    """
    Return the AIChatbotSDK reference
    """
    return (await get_cli_manager())._sdk

def success_message(message: str):
    """
    Display a success message with a green checkmark.
    """
    console.print(f"[green]✓[/green] {message}")

def error_message(message: str):
    """
    Display an error message with a red X.
    """
    console.print(f"[red]✗[/red] {message}")

def info_message(message: str):
    """
    Display an informational message with a blue info icon.
    """
    console.print(f"[blue]ℹ[/blue] {message}")

def warning_message(message: str):
    """
    Display a warning message with a yellow warning icon.
    """
    console.print(f"[yellow]⚠[/yellow] {message}")

def format_json(data: dict) -> str:
    """
    Format a dictionary as pretty-printed JSON.
    """
    import json
    return json.dumps(data, indent=2, default=str)

def display_table_data(data: list, title: str = "Results"):
    """
    Display a list of dicts or values in a table format.
    """
    if not data:
        info_message("No data to display")
        return

    from rich.table import Table

    table = Table(title=title)

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

def display_key_value_pairs(data: dict, title: str = "Information"):
    """
    Display key-value pairs in a formatted panel.
    """
    content = "\n".join([f"[cyan]{key}:[/cyan] {value}" for key, value in data.items()])
    panel = Panel(content, title=title, border_style="blue", padding=(1, 2))
    console.print(panel)

def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask for user confirmation.
    """
    from rich.prompt import Confirm
    return Confirm.ask(message, default=default)

def paginate_results(data: list, page_size: int = 20) -> list:
    """
    Paginate results for display.
    """
    if len(data) <= page_size:
        return data
    total_pages = (len(data) + page_size - 1) // page_size
    info_message(f"Showing first {page_size} of {len(data)} results ({total_pages} pages total)")
    return data[:page_size]

def format_timestamp(timestamp: str) -> str:
    """
    Format ISO timestamp for display.
    """
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp

def format_file_size(size_bytes: int) -> str:
    """
    Format file size for display.
    """
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def handle_api_response(response: dict, operation: str = "operation"):
    """
    Handle API response and display appropriate messages.
    """
    if not response:
        error_message(f"No response received from API for {operation}")
        return None

    if response.get("success", True):
        if "message" in response:
            success_message(response["message"])
        return response.get("data", response)
    else:
        error_msg = response.get("message", response.get("detail", f"Unknown error in {operation}"))
        error_message(error_msg)
        return None
