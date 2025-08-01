"""
Core CLI commands for authentication, config, health, version, and help.

Implements all root-level commands using async-typer.
"""

import os
from pathlib import Path
from typing import Optional

from async_typer import AsyncTyper
from rich.columns import Columns
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from typer import Option

from .base import (
    console,
    error_message,
    get_cli_manager,
    info_message,
    success_message,
    warning_message,
)

core_app = AsyncTyper(
    help="Core commands for authentication, config, and system status."
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
    Authenticate with the API and optionally save the authentication token.
    """
    try:
        cli_manager = await get_cli_manager()
        if not username:
            username = Prompt.ask("Username")
        if not password:
            password = Prompt.ask("Password", password=True)
        token = await cli_manager.login(username, password)
        if save_token:
            cli_manager.save_token(token.access_token)
            success_message(f"Logged in successfully as {username}. Token saved.")
        else:
            success_message(f"Logged in successfully as {username}.")
            info_message("Use --save-token to persist authentication.")

        info_panel = Panel(
            f"Access Token: [green]{'*' * 20}[/green]\n"
            f"Token Type: [blue]{token.token_type}[/blue]\n"
            f"Expires In: [yellow]{token.expires_in} seconds[/yellow]",
            title="🔐 Authentication Info",
            border_style="green",
        )
        console.print(info_panel)
    except Exception as e:
        error_message(f"Login failed: {str(e)}")
        raise SystemExit(1)


@core_app.async_command()
async def logout():
    """
    Log out and remove the saved authentication token.
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
                status_panel = Panel(
                    f"Status: [green]Authenticated[/green]\n"
                    f"Username: [blue]{user_info.get('username', 'Unknown')}[/blue]\n"
                    f"Email: [cyan]{user_info.get('email', 'Unknown')}[/cyan]\n"
                    f"Superuser: [yellow]{'Yes' if user_info.get('is_superuser') else 'No'}[/yellow]\n"
                    f"Active: [green]{'Yes' if user_info.get('is_active') else 'No'}[/green]",
                    title="🔐 Authentication Status",
                    border_style="green",
                )
                console.print(status_panel)
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
        version_info = Panel(
            f"[bold]AI Chatbot Platform API CLI[/bold]\n\n"
            f"Application Name: [blue]{app_info.get('name', 'Unknown')}[/blue]\n"
            f"Application Version: [green]{app_info.get('version', 'Unknown')}[/green]\n"
            f"Description: [cyan]{app_info.get('description', 'N/A')}[/cyan]\n"
            f"API Status: [green]{app_info.get('status', 'Unknown')}[/green]\n"
            f"CLI Mode: [magenta]API-based[/magenta]",
            title="📋 Version Information",
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(version_info)
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
        console.print(
            Panel(
                "Performing comprehensive health check...",
                title="🏥 Health Check",
                border_style="blue",
            )
        )

        # Check API connectivity
        try:
            ping_response = await sdk._request("/ping")
            api_status = (
                "🟢 Online"
                if ping_response and ping_response.get("status") == "ok"
                else "🔴 Offline"
            )
        except Exception:
            api_status = "🔴 Offline"

        # Get detailed health information
        try:
            health_data = await sdk.health.detailed()
        except Exception:
            health_data = {}

        results = []

        # API Status
        results.append(
            Panel(
                f"Status: {api_status}",
                title="API Server",
                border_style="green" if "🟢" in api_status else "red",
            )
        )

        # Database Status
        db_status = health_data.get("database", {})
        db_indicator = (
            "🟢 Connected" if db_status.get("connected") else "🔴 Disconnected"
        )
        results.append(
            Panel(
                f"Connection: {db_indicator}",
                title="Database",
                border_style="green" if "🟢" in db_indicator else "red",
            )
        )

        # Services Status
        services_status = health_data.get("services", {})
        services_ok = all(services_status.values()) if services_status else False
        services_indicator = "🟢 Operational" if services_ok else "🟡 Degraded"
        results.append(
            Panel(
                f"Status: {services_indicator}",
                title="Services",
                border_style="green" if services_ok else "yellow",
            )
        )

        # Performance Status
        perf_status = health_data.get("performance", {})
        perf_indicator = (
            "🟢 Good" if perf_status.get("response_time", 0) < 1000 else "🟡 Slow"
        )
        results.append(
            Panel(
                f"Response: {perf_indicator}",
                title="Performance",
                border_style="green" if "🟢" in perf_indicator else "yellow",
            )
        )

        console.print(Columns(results, equal=True))

        # Overall status
        overall_healthy = "🟢" in api_status and db_status.get("connected", False)
        if overall_healthy:
            success_message("System is healthy and ready to use!")
        else:
            console.print(
                "\n[yellow]⚠️ Some components need attention. Check the results above.[/yellow]"
            )

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
        console.print(
            Panel(
                f"[bold]AI Chatbot Platform System Status[/bold]\n"
                f"Generated: {Path.home()}\n"
                f"Mode: API-based CLI",
                title="🖥️ System Status",
                border_style="bright_blue",
            )
        )

        try:
            overview_response = await sdk.analytics.get_overview()
            if overview_response and overview_response.get("success", False):
                data = overview_response["data"]

                table = Table(title="System Overview")
                table.add_column("Component", style="cyan")
                table.add_column("Metric", style="white")
                table.add_column("Value", style="green")

                users_data = data.get("users", {})
                table.add_row("Users", "Total", str(users_data.get("total", 0)))
                table.add_row("", "Active", str(users_data.get("active", 0)))

                docs_data = data.get("documents", {})
                table.add_row("Documents", "Total", str(docs_data.get("total", 0)))
                table.add_row("", "Processed", str(docs_data.get("processed", 0)))

                convs_data = data.get("conversations", {})
                table.add_row("Conversations", "Total", str(convs_data.get("total", 0)))

                health_data = data.get("system_health", {})
                table.add_row("Health", "Score", f"{health_data.get('score', 0)}/100")

                console.print(table)
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
    quickstart_guide = """
[bold]🚀 AI Chatbot Platform API CLI - Quick Start[/bold]

[yellow]1. Authentication:[/yellow]
   • Login: [cyan]python api_manage.py login[/cyan]
   • Check status: [cyan]python api_manage.py auth-status[/cyan]
   • Logout: [cyan]python api_manage.py logout[/cyan]
...
"""
    console.print(
        Panel(
            quickstart_guide,
            title="🚀 API CLI Quick Start Guide",
            border_style="bright_green",
            padding=(1, 2),
        )
    )


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

        table = Table(title="Configuration Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        for key, value in config_data.items():
            table.add_row(key, str(value))
        console.print(table)

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
