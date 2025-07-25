"""
Base CLI utilities and common functionality.

This module provides common utilities for CLI commands including async command
handling, progress indicators, and console output utilities.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..database import AsyncSessionLocal
from ..services.conversation import ConversationService
from ..services.llm_profile_service import LLMProfileService
from ..services.prompt_service import PromptService
from ..services.user import UserService

console = Console()


async def get_prompt_service():
    """Get a PromptService instance with database session."""
    db = AsyncSessionLocal()
    try:
        return PromptService(db)
    except Exception:
        await db.close()
        raise


async def get_profile_service():
    """Get a LLMProfileService instance with database session."""
    db = AsyncSessionLocal()
    try:
        return LLMProfileService(db)
    except Exception:
        await db.close()
        raise


async def get_user_service():
    """Get a UserService instance with database session."""
    db = AsyncSessionLocal()
    try:
        return UserService(db)
    except Exception:
        await db.close()
        raise


async def get_conversation_service():
    """Get a ConversationService instance with database session."""
    db = AsyncSessionLocal()
    try:
        return ConversationService(db)
    except Exception:
        await db.close()
        raise


@asynccontextmanager
async def get_service_context(service_class):
    """Context manager for service instances that handles cleanup."""
    db = AsyncSessionLocal()
    try:
        service = service_class(db)
        yield service
    finally:
        await db.close()


def async_command(func: Callable) -> Callable:
    """
    Decorator to enable async functions in Typer CLI commands.

    Handles the complexity of running async functions in CLI environments where
    an event loop may or may not already be running. Uses thread pool execution
    to avoid nested event loop issues that commonly occur in CLI applications.

    Args:
        func: Async function to wrap for CLI usage

    Returns:
        Callable: Synchronous wrapper function that can be used with Typer

    Example:
        @async_command
        async def my_cli_command():
            await some_async_operation()
    """

    def wrapper(*args, **kwargs):
        """
        Synchronous wrapper that executes the async function.

        Attempts to handle different event loop scenarios gracefully.
        """
        try:
            # Try to get the current event loop
            asyncio.get_running_loop()
            # If there's already a running loop, we can't use asyncio.run()
            # Instead, create a task
            import concurrent.futures

            # Run in a separate thread to avoid nested loop issues
            def run_in_thread():
                """Execute the async function in a new event loop."""
                return asyncio.run(func(*args, **kwargs))

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(func(*args, **kwargs))

    return wrapper


@asynccontextmanager
async def progress_context(description: str):
    """Context manager for showing progress during operations."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(description, total=None)
        try:
            yield progress
        finally:
            progress.remove_task(task)


def success_message(message: str):
    """Display a success message."""
    console.print(f"[green]✅ {message}[/green]")


def error_message(message: str):
    """Display an error message."""
    console.print(f"[red]❌ {message}[/red]")


def warning_message(message: str):
    """Display a warning message."""
    console.print(f"[yellow]⚠️ {message}[/yellow]")


def info_message(message: str):
    """Display an info message."""
    console.print(f"[blue]ℹ️ {message}[/blue]")


def format_timestamp(dt) -> str:
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    return "N/A"


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"
