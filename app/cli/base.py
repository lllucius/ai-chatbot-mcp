"""
Base CLI utilities and common functionality.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def async_command(func: Callable) -> Callable:
    """Decorator to run async functions in CLI commands."""
    def wrapper(*args, **kwargs):
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If there's already a running loop, we can't use asyncio.run()
            # Instead, create a task
            import concurrent.futures
            import threading
            
            # Run in a separate thread to avoid nested loop issues
            def run_in_thread():
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
        transient=True
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