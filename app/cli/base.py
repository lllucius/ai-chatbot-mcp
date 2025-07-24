"Command-line interface for base management."

import asyncio
from contextlib import asynccontextmanager
from typing import Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def async_command(func: Callable) -> Callable:
    "Async Command operation."

    def wrapper(*args, **kwargs):
        "Wrapper operation."
        try:
            asyncio.get_running_loop()
            import concurrent.futures

            def run_in_thread():
                "Run In Thread operation."
                return asyncio.run(func(*args, **kwargs))

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        except RuntimeError:
            return asyncio.run(func(*args, **kwargs))

    return wrapper


@asynccontextmanager
async def progress_context(description: str):
    "Progress Context operation."
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(description, total=None)
        try:
            (yield progress)
        finally:
            progress.remove_task(task)


def success_message(message: str):
    "Success Message operation."
    console.print(f"[green]✅ {message}[/green]")


def error_message(message: str):
    "Error Message operation."
    console.print(f"[red]❌ {message}[/red]")


def warning_message(message: str):
    "Warning Message operation."
    console.print(f"[yellow]⚠️ {message}[/yellow]")


def info_message(message: str):
    "Info Message operation."
    console.print(f"[blue]ℹ️ {message}[/blue]")


def format_timestamp(dt) -> str:
    "Format Timestamp operation."
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    return "N/A"


def format_size(size_bytes: int) -> str:
    "Format Size operation."
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while (size_bytes >= 1024) and (i < (len(size_names) - 1)):
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"
