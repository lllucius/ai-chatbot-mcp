#!/usr/bin/env python3
"""AI Chatbot Platform Management CLI - Main Entry Point.

This module serves as the primary entry point for the AI Chatbot Platform command-line
interface, providing a comprehensive management system for all platform operations
through a modern async architecture and intuitive sub-command structure.
"""
import sys

from async_typer import AsyncTyper

from cli.analytics import analytics_app
from cli.conversations import conversation_app
from cli.core import core_app  # New: core commands (login, auth-status, config, etc.)
from cli.database import database_app
from cli.documents import document_app
from cli.jobs import jobs_app
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
app.add_typer(jobs_app, name="jobs")
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
        print("\nFor help, run: python manage.py --help")
        sys.exit(1)
