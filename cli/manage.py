#!/usr/bin/env python3
"""AI Chatbot Platform Management CLI - Main Entry Point.

This module serves as the primary entry point for the AI Chatbot Platform command-line
interface, providing a comprehensive management system for all platform operations
through a modern async architecture and intuitive sub-command structure.
"""
    - Prompts: Template management and customization
    - Profiles: User profile and preference management

Security Features:
    - JWT-based authentication with secure token storage
    - Role-based access control for administrative operations
    - Comprehensive audit logging for all CLI actions
    - Secure credential handling and validation
    - Session management with automatic token refresh

Performance Optimizations:
    - Async operations for non-blocking I/O and responsiveness
    - Efficient API communication with request batching
    - Lazy loading of heavy operations and large datasets
    - Progress indicators for long-running operations
    - Optimized startup time with modular command loading

Enterprise Features:
    - Comprehensive logging and monitoring integration
    - CI/CD pipeline compatibility for automation
    - Configuration management for multi-environment support
    - Bulk operations for large-scale administration
    - Integration with monitoring and alerting systems

Use Cases:
    - Development workflow automation and testing
    - Production system administration and monitoring
    - Data migration and bulk operation management
    - Troubleshooting and diagnostic operations
    - Integration testing and validation workflows

Example Usage:
    ```bash
    # Authentication and setup
    ai-chatbot login --username admin
    ai-chatbot config show

    # User management
    ai-chatbot users create john john@example.com
    ai-chatbot users list --active-only

    # Conversation operations
    ai-chatbot conversations create --title "Customer Support"
    ai-chatbot conversations list --page 1 --size 20

    # Analytics and monitoring
    ai-chatbot analytics dashboard --date-range 7d
    ai-chatbot health check --detailed

    # Database administration
    ai-chatbot database migrate --auto-approve
    ai-chatbot database backup --compress
    ```

Installation and Setup:
    The CLI is distributed as part of the ai-chatbot-mcp package:

    ```bash
    pip install ai-chatbot-mcp
    ai-chatbot --help
    ```

Configuration:
    Configuration is managed through environment variables and .env files:

    ```bash
    export API_BASE_URL="https://api.chatbot.example.com"
    export CLIENT_TIMEOUT=30
    ai-chatbot config show
    ```

Integration:
    - CI/CD pipelines for automated testing and deployment
    - Monitoring systems for health checks and alerts
    - Development tools for debugging and validation
    - Production operations for administration and maintenance
"""
import sys

from async_typer import AsyncTyper

from cli.analytics import analytics_app
from cli.conversations import conversation_app
from cli.core import core_app  # New: core commands (login, auth-status, config, etc.)
from cli.database import database_app
from cli.documents import document_app
from cli.mcp import mcp_app
from cli.profiles import profile_app
from cli.prompts import prompt_app
from cli.tasks import tasks_app
from cli.users import user_app

app = AsyncTyper(
    help="AI Chatbot Platform - API-based Management CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode=None,  # Disable rich markup completely
)

# Register sub-applications
app.add_typer(
    core_app, name=None
)  # core_app contains root commands (login, logout, etc.)
app.add_typer(user_app, name="users")
app.add_typer(document_app, name="documents")
app.add_typer(conversation_app, name="conversations")
app.add_typer(analytics_app, name="analytics")
app.add_typer(database_app, name="database")
app.add_typer(tasks_app, name="tasks")
app.add_typer(mcp_app, name="mcp")
app.add_typer(prompt_app, name="prompts")
app.add_typer(profile_app, name="profiles")

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"CLI Error: {e}")
        print("\nFor help, run: python api_manage.py --help")
        sys.exit(1)
