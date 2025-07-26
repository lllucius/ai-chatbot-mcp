#!/usr/bin/env python3
"""
API-based Management CLI for the AI Chatbot Platform.

This is a comprehensive command-line interface that provides full-featured
management capabilities using the platform's REST API endpoints. It duplicates
all functionality of the original manage.py script but operates through the API
layer instead of direct database access.

The CLI is designed with a modular architecture where each functional area
is handled by a separate module, but all commands are accessible through
a single driver command.

Usage:
    python api_manage.py users create john john@example.com
    python api_manage.py documents list --status completed
    python api_manage.py conversations export 123
    python api_manage.py analytics overview
    python api_manage.py database backup
    python api_manage.py tasks status

Features:
- User management (creation, deletion, roles, statistics)
- Document management (upload, processing, search, cleanup)
- Conversation management (export, import, search, analytics)
- System analytics (usage trends, performance metrics)
- Database management (migrations, backup, maintenance)
- Background task management (monitoring, scheduling, retry)
- MCP server and tool management
- Prompt and profile management
- Full API compatibility with existing CLI syntax

Requirements:
- FastAPI server must be running
- Valid authentication credentials
- Proper environment configuration
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from api_cli.auth import get_auth_manager
from api_cli.base import APIClient, console, error_message, info_message, success_message
from api_cli.analytics import analytics_app
from api_cli.conversations import conversation_app
from api_cli.database import database_app
from api_cli.documents import document_app
from api_cli.mcp import mcp_app
from api_cli.prompts import prompt_app
from api_cli.profiles import profile_app
from api_cli.tasks import tasks_app
from api_cli.users import user_app

# Create the main Typer app
app = typer.Typer(
    help="🚀 AI Chatbot Platform - API-based Management CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

# Add sub-applications
app.add_typer(user_app, name="users", help="👥 User management commands")
app.add_typer(document_app, name="documents", help="📄 Document management commands")
app.add_typer(
    conversation_app, name="conversations", help="💬 Conversation management commands"
)
app.add_typer(
    analytics_app, name="analytics", help="📊 Analytics and reporting commands"
)
app.add_typer(database_app, name="database", help="🗄️ Database management commands")
app.add_typer(tasks_app, name="tasks", help="⚙️ Background task management commands")
app.add_typer(mcp_app, name="mcp", help="🔌 MCP server and tool management commands")
app.add_typer(prompt_app, name="prompts", help="📝 Prompt management commands")
app.add_typer(
    profile_app, name="profiles", help="🎛️ LLM parameter profile management commands"
)


@app.command()
def login(
    username: str = typer.Option(None, "--username", "-u", help="Username"),
    password: str = typer.Option(None, "--password", "-p", help="Password"),
    save_token: bool = typer.Option(True, "--save-token/--no-save-token", help="Save authentication token"),
):
    """Login to the API and save authentication token."""
    try:
        auth_manager = get_auth_manager()
        
        # Prompt for credentials if not provided
        if not username:
            username = Prompt.ask("Username")
        
        if not password:
            password = Prompt.ask("Password", password=True)
        
        # Attempt login
        token_data = asyncio.run(auth_manager.login(username, password))
        
        if save_token:
            auth_manager.save_token(token_data["access_token"])
            success_message(f"Logged in successfully as {username}. Token saved.")
        else:
            success_message(f"Logged in successfully as {username}.")
            info_message("Use --save-token to persist authentication.")
        
        # Display token info
        info_panel = Panel(
            f"Access Token: [green]{'*' * 20}[/green]\n"
            f"Token Type: [blue]{token_data.get('token_type', 'bearer')}[/blue]\n"
            f"Expires In: [yellow]{token_data.get('expires_in', 'Unknown')} seconds[/yellow]",
            title="🔐 Authentication Info",
            border_style="green",
        )
        console.print(info_panel)
        
    except Exception as e:
        error_message(f"Login failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def logout():
    """Logout and remove saved authentication token."""
    try:
        auth_manager = get_auth_manager()
        auth_manager.clear_token()
        success_message("Logged out successfully. Authentication token removed.")
    except Exception as e:
        error_message(f"Logout failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def auth_status():
    """Show current authentication status."""
    try:
        auth_manager = get_auth_manager()
        
        if auth_manager.has_token():
            # Try to validate token
            try:
                user_info = asyncio.run(auth_manager.get_current_user())
                
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
            info_message("Not authenticated. Use 'python api_manage.py login' to authenticate.")
            
    except Exception as e:
        error_message(f"Failed to check authentication status: {str(e)}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    try:
        # Get version info from API
        client = APIClient()
        response = asyncio.run(client.get("/"))
        
        if response:
            version_info = Panel(
                f"[bold]AI Chatbot Platform API CLI[/bold]\n\n"
                f"Application Name: [blue]{response.get('name', 'Unknown')}[/blue]\n"
                f"Application Version: [green]{response.get('version', 'Unknown')}[/green]\n"
                f"Description: [cyan]{response.get('description', 'N/A')}[/cyan]\n"
                f"API Status: [green]{response.get('status', 'Unknown')}[/green]\n"
                f"CLI Mode: [magenta]API-based[/magenta]",
                title="📋 Version Information",
                border_style="bright_blue",
                padding=(1, 2),
            )
            console.print(version_info)
        else:
            error_message("Failed to get version information from API")
            
    except Exception as e:
        error_message(f"Failed to get version information: {str(e)}")
        raise typer.Exit(1)


@app.command()
def health():
    """Perform comprehensive system health check."""
    try:
        client = APIClient()
        
        console.print(
            Panel(
                "Performing comprehensive health check...",
                title="🏥 Health Check",
                border_style="blue",
            )
        )
        
        # Check API connectivity
        try:
            ping_response = asyncio.run(client.get("/ping"))
            api_status = "🟢 Online" if ping_response and ping_response.get("status") == "ok" else "🔴 Offline"
        except Exception:
            api_status = "🔴 Offline"
        
        # Get detailed health information
        try:
            health_response = asyncio.run(client.get("/api/v1/health/detailed"))
            health_data = health_response if health_response else {}
        except Exception:
            health_data = {}
        
        # Create health status panels
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
        db_indicator = "🟢 Connected" if db_status.get("connected") else "🔴 Disconnected"
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
        perf_indicator = "🟢 Good" if perf_status.get("response_time", 0) < 1000 else "🟡 Slow"
        results.append(
            Panel(
                f"Response: {perf_indicator}",
                title="Performance",
                border_style="green" if "🟢" in perf_indicator else "yellow",
            )
        )
        
        # Display results
        from rich.columns import Columns
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
        raise typer.Exit(1)


@app.command()
def status():
    """Show overall system status summary."""
    try:
        client = APIClient()
        
        console.print(
            Panel(
                f"[bold]AI Chatbot Platform System Status[/bold]\n"
                f"Generated: {typer.get_app_dir('api-cli')}\n"
                f"Mode: API-based CLI",
                title="🖥️ System Status",
                border_style="bright_blue",
            )
        )
        
        # Get analytics overview
        try:
            overview_response = asyncio.run(client.get("/api/v1/analytics/overview"))
            if overview_response and overview_response.get("success"):
                data = overview_response["data"]
                
                # Create status table
                table = Table(title="System Overview")
                table.add_column("Component", style="cyan")
                table.add_column("Metric", style="white")
                table.add_column("Value", style="green")
                
                # Users
                users_data = data.get("users", {})
                table.add_row("Users", "Total", str(users_data.get("total", 0)))
                table.add_row("", "Active", str(users_data.get("active", 0)))
                
                # Documents
                docs_data = data.get("documents", {})
                table.add_row("Documents", "Total", str(docs_data.get("total", 0)))
                table.add_row("", "Processed", str(docs_data.get("processed", 0)))
                
                # Conversations
                convs_data = data.get("conversations", {})
                table.add_row("Conversations", "Total", str(convs_data.get("total", 0)))
                
                # Health Score
                health_data = data.get("system_health", {})
                table.add_row("Health", "Score", f"{health_data.get('score', 0)}/100")
                
                console.print(table)
            else:
                info_message("Unable to retrieve system status from API")
                
        except Exception as e:
            error_message(f"Failed to get system status: {str(e)}")
            
    except Exception as e:
        error_message(f"Status check failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def quickstart():
    """Show quick start guide and common commands."""
    quickstart_guide = """
[bold]🚀 AI Chatbot Platform API CLI - Quick Start[/bold]

[yellow]1. Authentication:[/yellow]
   • Login: [cyan]python api_manage.py login[/cyan]
   • Check status: [cyan]python api_manage.py auth-status[/cyan]
   • Logout: [cyan]python api_manage.py logout[/cyan]

[yellow]2. First Time Setup:[/yellow]
   • Check system health: [cyan]python api_manage.py health[/cyan]
   • Initialize database: [cyan]python api_manage.py database init[/cyan]
   • Create admin user: [cyan]python api_manage.py users create admin admin@company.com --superuser[/cyan]

[yellow]3. User Management:[/yellow]
   • List users: [cyan]python api_manage.py users list[/cyan]
   • Create user: [cyan]python api_manage.py users create john john@example.com[/cyan]
   • Show user details: [cyan]python api_manage.py users show john[/cyan]
   • Reset password: [cyan]python api_manage.py users reset-password john[/cyan]

[yellow]4. Document Management:[/yellow]
   • Upload document: [cyan]python api_manage.py documents upload /path/to/file.pdf[/cyan]
   • List documents: [cyan]python api_manage.py documents list --status completed[/cyan]
   • Search documents: [cyan]python api_manage.py documents search "machine learning"[/cyan]
   • Clean up old files: [cyan]python api_manage.py documents cleanup --older-than 30[/cyan]

[yellow]5. Conversation Management:[/yellow]
   • List conversations: [cyan]python api_manage.py conversations list --user john[/cyan]
   • Export conversation: [cyan]python api_manage.py conversations export 456 --format json[/cyan]
   • Import conversation: [cyan]python api_manage.py conversations import backup.json[/cyan]
   • Search conversations: [cyan]python api_manage.py conversations search "API documentation"[/cyan]

[yellow]6. Analytics & Monitoring:[/yellow]
   • System overview: [cyan]python api_manage.py analytics overview[/cyan]
   • Usage statistics: [cyan]python api_manage.py analytics usage --period 7d[/cyan]
   • Performance metrics: [cyan]python api_manage.py analytics performance[/cyan]
   • Export report: [cyan]python api_manage.py analytics export-report[/cyan]

[yellow]7. Database Management:[/yellow]
   • Check status: [cyan]python api_manage.py database status[/cyan]
   • Run migrations: [cyan]python api_manage.py database upgrade[/cyan]
   • Create backup: [cyan]python api_manage.py database backup[/cyan]
   • List tables: [cyan]python api_manage.py database tables[/cyan]

[yellow]8. Background Tasks:[/yellow]
   • Check status: [cyan]python api_manage.py tasks status[/cyan]
   • View workers: [cyan]python api_manage.py tasks workers[/cyan]
   • Monitor queues: [cyan]python api_manage.py tasks queue[/cyan]
   • Retry failed: [cyan]python api_manage.py tasks retry-failed[/cyan]

[yellow]9. Prompt & Profile Management:[/yellow]
   • List prompts: [cyan]python api_manage.py prompts list[/cyan]
   • Add prompt: [cyan]python api_manage.py prompts add myprompt --content "You are..."[/cyan]
   • List profiles: [cyan]python api_manage.py profiles list[/cyan]
   • Create profile: [cyan]python api_manage.py profiles add creative --temperature 1.0[/cyan]

[yellow]10. MCP Server & Tool Management:[/yellow]
   • List servers: [cyan]python api_manage.py mcp list-servers --detailed[/cyan]
   • Add server: [cyan]python api_manage.py mcp add-server myserver http://localhost:9000/mcp[/cyan]
   • Enable/disable server: [cyan]python api_manage.py mcp enable-server myserver[/cyan]
   • List tools: [cyan]python api_manage.py mcp list-tools --enabled-only[/cyan]
   • Tool statistics: [cyan]python api_manage.py mcp stats[/cyan]

[green]💡 Pro Tips:[/green]
   • All commands work through the API - server must be running
   • Use [cyan]--help[/cyan] with any command for detailed options
   • Login once and your token will be saved for subsequent commands
   • Check [cyan]python api_manage.py auth-status[/cyan] if you get authentication errors

[blue]📚 Need more help?[/blue]
   • Run [cyan]python api_manage.py --help[/cyan] for all available commands
   • Use [cyan]python api_manage.py [module] --help[/cyan] for module-specific commands
   • Each command has detailed help with [cyan]--help[/cyan]
"""

    console.print(
        Panel(
            quickstart_guide,
            title="🚀 API CLI Quick Start Guide",
            border_style="bright_green",
            padding=(1, 2),
        )
    )


@app.command()
def config():
    """Show current configuration and environment settings."""
    try:
        # Load environment configuration from main app .env file
        from dotenv import load_dotenv
        import os
        from pathlib import Path
        
        # Look for .env file in current directory first, then parent
        env_file = Path(".env")
        if not env_file.exists():
            env_file = Path(__file__).parent / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            info_message(f"Loaded configuration from: {env_file.absolute()}")
        else:
            warning_message("No .env file found, using environment variables only")
        
        # Get configuration values
        config_data = {
            "API Base URL": os.getenv("API_BASE_URL", "http://localhost:8000"),
            "API Timeout": f"{os.getenv('API_TIMEOUT', '30')} seconds",
            "Authentication": "Token-based" if get_auth_manager().has_token() else "Not authenticated",
            "Config File": str(env_file.absolute()) if env_file.exists() else "Not found",
            "Debug Mode": os.getenv("DEBUG", "false"),
            "Log Level": os.getenv("LOG_LEVEL", "INFO"),
            "Database URL": os.getenv("DATABASE_URL", "Not set")[:50] + "..." if len(os.getenv("DATABASE_URL", "")) > 50 else os.getenv("DATABASE_URL", "Not set"),
            "OpenAI Model": os.getenv("OPENAI_CHAT_MODEL", "Not set"),
            "Admin Username": os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
        }
        
        # Create configuration table
        table = Table(title="Configuration Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in config_data.items():
            table.add_row(key, str(value))
        
        console.print(table)
        
        # Show authentication status
        auth_manager = get_auth_manager()
        if auth_manager.has_token():
            success_message("Authentication token is present and will be used for API calls.")
        else:
            info_message("No authentication token found. Use 'python api_manage.py login' to authenticate.")
            # Show default admin credentials hint
            admin_user = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            info_message(f"Default admin username: {admin_user}")
            
    except Exception as e:
        error_message(f"Failed to show configuration: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]CLI Error: {e}[/red]")
        console.print("\n[dim]For help, run: python api_manage.py --help[/dim]")
        sys.exit(1)