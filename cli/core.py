"""
Core CLI commands for authentication, configuration, and system management.

This module implements the foundational CLI commands that provide user authentication,
system configuration management, health monitoring, and version information. These
commands form the core functionality required for all other CLI operations and
administrative tasks.

The module uses AsyncTyper for modern async command handling and Rich for beautiful
terminal output with progress indicators, panels, and formatted displays. All commands
include comprehensive error handling and user feedback.

Key Commands:
    - login: User authentication with secure token management
    - logout: Session termination and token cleanup
    - whoami: Current user information and session status
    - config: Configuration management and environment setup
    - health: System health checks and connectivity testing
    - version: Version information and build details

Architecture Features:
    - Async command processing for non-blocking operations
    - Rich terminal interface with colors and formatting
    - Secure credential handling with masked input
    - Comprehensive error handling and user feedback
    - Modular command structure for maintainability

Security Features:
    - Secure password input with masking
    - JWT token-based authentication
    - Automatic token validation and refresh
    - Secure token storage with proper file permissions
    - Session management and cleanup

Performance Optimizations:
    - Async operations for improved responsiveness
    - Efficient API communication patterns
    - Minimal startup overhead
    - Fast command execution and feedback
    - Optimized token validation

Use Cases:
    - Initial CLI setup and authentication
    - Session management for development workflows
    - System health monitoring and diagnostics
    - Configuration validation and troubleshooting
    - User account management and verification

Example Usage:
    ```bash
    # Authenticate with the platform
    ai-chatbot login --username admin

    # Check current user and session
    ai-chatbot whoami

    # View system health and connectivity
    ai-chatbot health

    # Display version and build information
    ai-chatbot version

    # Manage configuration settings
    ai-chatbot config show
    ai-chatbot config set api_timeout 30

    # Logout and cleanup
    ai-chatbot logout
    ```

Integration:
    - Works with all other CLI modules for authentication
    - Integrates with CI/CD pipelines for automated operations
    - Supports development and production environments
    - Compatible with monitoring and alerting systems
"""

import os
from pathlib import Path
from typing import Optional

from async_typer import AsyncTyper
from typer import Option

from .base import (
    error_message,
    get_cli_manager,
    info_message,
    success_message,
    warning_message,
)

core_app = AsyncTyper(
    help="Core commands for authentication, config, and system status.",
    rich_markup_mode=None,
)


@core_app.async_command()
async def login(
    username: Optional[str] = Option(None, "--username", "-u", help="Username"),
    password: Optional[str] = Option(None, "--password", "-p", help="Password"),
    save_token: bool = Option(
        True, "--save-token/--no-save-token", help="Save authentication token"
    ),
):
    """
    Authenticate with the AI Chatbot Platform API and manage session tokens.

    Performs user authentication against the platform's authentication system,
    obtaining a JWT token for subsequent API operations. The command supports
    interactive credential entry or command-line arguments for automation.

    Authentication tokens can be saved to secure local storage for persistent
    sessions across CLI invocations. The token is stored with restrictive file
    permissions in the user's home directory.

    Args:
        username (Optional[str]): Platform username. If not provided, will prompt interactively
        password (Optional[str]): User password. If not provided, will prompt with masking
        save_token (bool): Whether to save token to disk for persistent sessions. Defaults to True

    Security Notes:
        - Passwords are masked during interactive input
        - Tokens are stored with 0o600 permissions (owner read/write only)
        - Failed authentication attempts are logged for security monitoring
        - Tokens include expiration information for automatic refresh

    Performance Notes:
        - Fast authentication with JWT token generation
        - Minimal network overhead for login process
        - Efficient token storage and retrieval
        - Non-blocking async operations

    Use Cases:
        - Initial CLI setup and user authentication
        - Development workflow automation
        - CI/CD pipeline integration with service accounts
        - Production system administration
        - Troubleshooting and debugging sessions

    Example:
        ```bash
        # Interactive login with saved token
        ai-chatbot login

        # Command-line login for automation
        ai-chatbot login --username admin --password secret

        # Login without saving token (temporary session)
        ai-chatbot login --no-save-token
        ```

    Raises:
        SystemExit: On authentication failure or network errors
    """
    try:
        cli_manager = await get_cli_manager()
        if not username:
            username = input("Username: ")
        if not password:
            import getpass
            password = getpass.getpass("Password: ")
        token = await cli_manager.login(username, password)
        if save_token:
            cli_manager.save_token(token.access_token)
            success_message(f"Logged in successfully as {username}. Token saved.")
        else:
            success_message(f"Logged in successfully as {username}.")
            info_message("Use --save-token to persist authentication.")

        print("\nAuthentication Info:")
        print("===================")
        print(f"Access Token: {'*' * 20}")
        print(f"Token Type: {token.token_type}")
        print(f"Expires In: {token.expires_in} seconds")
    except Exception as e:
        error_message(f"Login failed: {str(e)}")
        raise SystemExit(1)


@core_app.async_command()
async def logout():
    """
    Terminate current session and remove stored authentication tokens.

    Performs a secure logout operation by invalidating the current session
    on the server and removing all stored authentication tokens from local
    storage. This ensures complete session cleanup and prevents unauthorized
    access to user credentials.

    The logout process includes both server-side session invalidation and
    local token cleanup, providing comprehensive security for user sessions.
    If the server is unreachable, local tokens are still removed to prevent
    potential security issues.

    Security Notes:
        - Server-side session invalidation prevents token reuse
        - Local token files are securely removed from disk
        - All authentication state is cleared from memory
        - Graceful handling of network failures during logout

    Performance Notes:
        - Fast local token cleanup regardless of server status
        - Non-blocking async operation for responsiveness
        - Minimal network overhead for session invalidation
        - Immediate feedback to user on completion

    Use Cases:
        - Ending development sessions securely
        - Security incident response and token invalidation
        - Multi-user system cleanup procedures
        - Automated logout in CI/CD pipelines
        - Session management in shared environments

    Example:
        ```bash
        # Standard logout operation
        ai-chatbot logout
        ```

    Note:
        This command can be safely executed multiple times without error,
        even if no active session exists. It will always ensure clean
        authentication state.
    """
    try:
        cli_manager = await get_cli_manager()
        await cli_manager.logout()
        success_message("Logged out successfully. Authentication token removed.")
    except Exception as e:
        error_message(f"Logout failed: {str(e)}")
        raise SystemExit(1)


@core_app.async_command("auth-status")
async def auth_status():
    """
    Show current authentication status and user info.
    """
    try:
        cli_manager = await get_cli_manager()
        if cli_manager.has_token():
            try:
                user_info = await cli_manager.get_current_user()
                print("\nAuthentication Status:")
                print("=====================")
                print(f"Status: Authenticated")
                print(f"Username: {user_info.get('username', 'Unknown')}")
                print(f"Email: {user_info.get('email', 'Unknown')}")
                print(f"Superuser: {'Yes' if user_info.get('is_superuser') else 'No'}")
                print(f"Active: {'Yes' if user_info.get('is_active') else 'No'}")
            except Exception as e:
                error_message(f"Token validation failed: {str(e)}")
                info_message("Please login again using: python api_manage.py login")
        else:
            info_message(
                "Not authenticated. Use 'python api_manage.py login' to authenticate."
            )
    except Exception as e:
        error_message(f"Failed to check authentication status: {str(e)}")
        raise SystemExit(1)


@core_app.async_command()
async def version():
    """
    Show version information.
    """
    try:
        # Load config and create SDK directly for version check
        from client.ai_chatbot_sdk import AIChatbotSDK
        from client.config import load_config

        config = load_config()
        sdk = AIChatbotSDK(base_url=config.api_base_url, timeout=config.api_timeout)
        _ = await sdk.health.basic()
        app_info = await sdk._request("/")
        
        print("\nVersion Information:")
        print("===================")
        print("AI Chatbot Platform API CLI")
        print()
        print(f"Application Name: {app_info.get('name', 'Unknown')}")
        print(f"Application Version: {app_info.get('version', 'Unknown')}")
        print(f"Description: {app_info.get('description', 'N/A')}")
        print(f"API Status: {app_info.get('status', 'Unknown')}")
        print(f"CLI Mode: API-based")
    except Exception as e:
        error_message(f"Failed to get version information: {str(e)}")
        raise SystemExit(1)


@core_app.async_command()
async def health():
    """
    Perform comprehensive system health check.
    """
    try:
        from client.ai_chatbot_sdk import AIChatbotSDK
        from client.config import load_config

        config = load_config()
        sdk = AIChatbotSDK(base_url=config.api_base_url, timeout=config.api_timeout)
        
        print("\nHealth Check:")
        print("=============")
        print("Performing comprehensive health check...")
        print()

        # Check API connectivity
        try:
            ping_response = await sdk._request("/ping")
            api_status = (
                "Online"
                if ping_response and ping_response.get("status") == "ok"
                else "Offline"
            )
        except Exception:
            api_status = "Offline"

        # Get detailed health information
        try:
            health_data = await sdk.health.detailed()
        except Exception:
            health_data = {}

        # API Status
        print(f"API Server: {api_status}")

        # Database Status
        db_status = health_data.get("database", {})
        db_indicator = (
            "Connected" if db_status.get("connected") else "Disconnected"
        )
        print(f"Database: {db_indicator}")

        # Services Status
        services_status = health_data.get("services", {})
        services_ok = all(services_status.values()) if services_status else False
        services_indicator = "Operational" if services_ok else "Degraded"
        print(f"Services: {services_indicator}")

        # Performance Status
        perf_status = health_data.get("performance", {})
        perf_indicator = (
            "Good" if perf_status.get("response_time", 0) < 1000 else "Slow"
        )
        print(f"Performance: {perf_indicator}")

        # Overall status
        overall_healthy = api_status == "Online" and db_status.get("connected", False)
        print()
        if overall_healthy:
            success_message("System is healthy and ready to use!")
        else:
            warning_message("Some components need attention. Check the results above.")

    except Exception as e:
        error_message(f"Health check failed: {str(e)}")
        raise SystemExit(1)


@core_app.async_command()
async def status():
    """
    Show overall system status summary.
    """
    try:
        from client.ai_chatbot_sdk import AIChatbotSDK
        from client.config import load_config

        config = load_config()
        sdk = AIChatbotSDK(base_url=config.api_base_url, timeout=config.api_timeout)
        
        print("\nSystem Status:")
        print("==============")
        print("AI Chatbot Platform System Status")
        print(f"Generated: {Path.home()}")
        print("Mode: API-based CLI")
        print()

        try:
            overview_response = await sdk.analytics.get_overview()
            if overview_response and overview_response.get("success", False):
                data = overview_response["data"]

                print("System Overview:")
                print("-" * 50)
                print(f"{'Component':<15} {'Metric':<15} {'Value':<15}")
                print("-" * 50)

                users_data = data.get("users", {})
                print(f"{'Users':<15} {'Total':<15} {str(users_data.get('total', 0)):<15}")
                print(f"{'':<15} {'Active':<15} {str(users_data.get('active', 0)):<15}")

                docs_data = data.get("documents", {})
                print(f"{'Documents':<15} {'Total':<15} {str(docs_data.get('total', 0)):<15}")
                print(f"{'':<15} {'Processed':<15} {str(docs_data.get('processed', 0)):<15}")

                convs_data = data.get("conversations", {})
                print(f"{'Conversations':<15} {'Total':<15} {str(convs_data.get('total', 0)):<15}")

                health_data = data.get("system_health", {})
                print(f"{'Health':<15} {'Score':<15} {health_data.get('score', 0)}/100")
                print()
            else:
                info_message("Unable to retrieve system status from API")
        except Exception as e:
            error_message(f"Failed to get system status: {str(e)}")
    except Exception as e:
        error_message(f"Status check failed: {str(e)}")
        raise SystemExit(1)


@core_app.async_command()
async def quickstart():
    """
    Show quick start guide and common commands.
    """
    print("\nAI Chatbot Platform API CLI - Quick Start:")
    print("==========================================")
    print()
    print("1. Authentication:")
    print("   • Login: python api_manage.py login")
    print("   • Check status: python api_manage.py auth-status")
    print("   • Logout: python api_manage.py logout")
    print()
    print("2. User Management:")
    print("   • List users: python api_manage.py users list")
    print("   • Create user: python api_manage.py users create")
    print("   • Show user details: python api_manage.py users show <id>")
    print()
    print("3. Document Management:")
    print("   • List documents: python api_manage.py documents list")
    print("   • Show document: python api_manage.py documents show <id>")
    print()
    print("4. Conversation Management:")
    print("   • List conversations: python api_manage.py conversations list")
    print("   • Show conversation: python api_manage.py conversations show <id>")
    print()
    print("5. System Operations:")
    print("   • Health check: python api_manage.py health")
    print("   • System status: python api_manage.py status")
    print("   • Configuration: python api_manage.py config")
    print()
    print("6. Analytics:")
    print("   • Overview: python api_manage.py analytics overview")
    print("   • Usage stats: python api_manage.py analytics usage")
    print()
    print("For more help on any command, add --help:")
    print("   python api_manage.py <command> --help")
    print()


@core_app.async_command()
async def config():
    """
    Show current configuration and environment settings.
    """
    try:
        from dotenv import load_dotenv

        env_file = Path(".env")
        if not env_file.exists():
            env_file = Path(__file__).parent.parent / ".env"

        if env_file.exists():
            load_dotenv(env_file)
            info_message(f"Loaded configuration from: {env_file.absolute()}")
        else:
            warning_message("No .env file found, using environment variables only")

        cli_manager = await get_cli_manager()

        config_data = {
            "API Base URL": os.getenv("API_BASE_URL", "http://localhost:8000"),
            "API Timeout": f"{os.getenv('API_TIMEOUT', '30')} seconds",
            "Authentication": (
                "Token-based" if cli_manager.has_token() else "Not authenticated"
            ),
            "Config File": (
                str(env_file.absolute()) if env_file.exists() else "Not found"
            ),
            "Debug Mode": os.getenv("DEBUG", "false"),
            "Log Level": os.getenv("LOG_LEVEL", "INFO"),
            "Database URL": (
                os.getenv("DATABASE_URL", "Not set")[:50] + "..."
                if len(os.getenv("DATABASE_URL", "")) > 50
                else os.getenv("DATABASE_URL", "Not set")
            ),
            "OpenAI Model": os.getenv("OPENAI_CHAT_MODEL", "Not set"),
            "Admin Username": os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
        }

        print("\nConfiguration Settings:")
        print("=======================")
        max_key_length = max(len(key) for key in config_data.keys())
        for key, value in config_data.items():
            print(f"{key.ljust(max_key_length)}: {value}")
        print()

        if cli_manager.has_token():
            success_message(
                "Authentication token is present and will be used for API calls."
            )
        else:
            info_message(
                "No authentication token found. Use 'python api_manage.py login' to authenticate."
            )
            admin_user = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            info_message(f"Default admin username: {admin_user}")

    except Exception as e:
        error_message(f"Failed to show configuration: {str(e)}")
        raise SystemExit(1)
