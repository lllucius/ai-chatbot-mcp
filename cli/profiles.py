"""
LLM profile management commands for the API-based CLI.

All commands use async/await and the async SDK client.
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Argument, Option

from .base import console, error_message, get_sdk_with_auth, success_message

profile_app = AsyncTyper(help="🎛️ LLM parameter profile management commands")


@profile_app.async_command()
async def list(
    active_only: bool = Option(False, "--active-only", help="Show only active profiles"),
    search: Optional[str] = Option(None, "--search", help="Search profiles by name"),
):
    """List all LLM profiles with optional filtering."""
    try:
        sdk = await get_sdk_with_auth()
        data = await sdk.profiles.list_profiles(active_only=active_only, search=search)
        if data:
            from rich.table import Table
            profiles = data.get("profiles", [])
            table = Table(title=f"LLM Profiles ({len(profiles)} total)")
            table.add_column("Name", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Model", style="blue")
            table.add_column("Default", style="green")
            table.add_column("Active", style="yellow")
            for profile in profiles:
                table.add_row(
                    profile.get("name", ""),
                    profile.get("title", ""),
                    profile.get("model_name", ""),
                    "Yes" if profile.get("is_default") else "No",
                    "Yes" if profile.get("is_active") else "No"
                )
            console.print(table)
        else:
            console.print("[yellow]No profiles found.[/yellow]")
    except Exception as e:
        error_message(f"Failed to list profiles: {str(e)}")
        raise SystemExit(1)


@profile_app.async_command()
async def show(
    profile_name: str = Argument(..., help="Profile name to show"),
):
    """Show detailed information about a specific LLM profile."""
    try:
        sdk = await get_sdk_with_auth()
        data = await sdk.profiles.get_profile(profile_name)
        if data:
            from rich.table import Table
            table = Table(title="Profile Details")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Name", data.name)
            table.add_row("Title", data.title)
            table.add_row("Model", data.model_name)
            table.add_row("Default", "Yes" if getattr(data, "is_default", False) else "No")
            table.add_row("Active", "Yes" if getattr(data, "is_active", False) else "No")
            table.add_row("Description", data.description or "")
            table.add_row("Parameters", str(data.parameters or ""))
            table.add_row("Created", str(data.created_at))
            table.add_row("Updated", str(data.updated_at))
            console.print(table)
    except Exception as e:
        error_message(f"Failed to show profile: {str(e)}")
        raise SystemExit(1)


@profile_app.async_command()
async def add(
    name: str = Argument(..., help="Profile name"),
    title: str = Option(..., "--title", help="Profile title"),
    model_name: str = Option(..., "--model", help="OpenAI model name"),
    parameters: str = Option("{}", "--parameters", help="Model parameters as JSON"),
    description: Optional[str] = Option("", "--description", help="Profile description"),
    is_default: bool = Option(False, "--default", help="Set as default profile"),
):
    """Add a new LLM profile."""
    try:
        import json
        sdk = await get_sdk_with_auth()
        from client.ai_chatbot_sdk import LLMProfileCreate
        params = json.loads(parameters) if parameters else {}
        profile_data = LLMProfileCreate(
            name=name,
            title=title,
            model_name=model_name,
            parameters=params,
            description=description,
            is_default=is_default,
        )
        await sdk.profiles.create_profile(profile_data)
        success_message(f"Profile '{name}' added successfully")
    except Exception as e:
        error_message(f"Failed to add profile: {str(e)}")
        raise SystemExit(1)


@profile_app.async_command()
async def update(
    profile_name: str = Argument(..., help="Profile name to update"),
    title: Optional[str] = Option(None, "--title", help="New title"),
    model_name: Optional[str] = Option(None, "--model", help="OpenAI model name"),
    parameters: Optional[str] = Option(None, "--parameters", help="Model parameters as JSON"),
    description: Optional[str] = Option(None, "--description", help="New description"),
    is_default: Optional[bool] = Option(None, "--default/--no-default", help="Set as default profile"),
):
    """Update an existing LLM profile."""
    try:
        import json
        sdk = await get_sdk_with_auth()
        update_data = {}
        if title:
            update_data["title"] = title
        if model_name:
            update_data["model_name"] = model_name
        if parameters:
            update_data["parameters"] = json.loads(parameters)
        if description:
            update_data["description"] = description
        if is_default is not None:
            update_data["is_default"] = is_default
        if not update_data:
            error_message("No update fields provided")
            return
        await sdk.profiles.update_profile(profile_name, update_data)
        success_message(f"Profile '{profile_name}' updated successfully")
    except Exception as e:
        error_message(f"Failed to update profile: {str(e)}")
        raise SystemExit(1)


@profile_app.async_command()
async def remove(
    profile_name: str = Argument(..., help="Profile name to remove"),
    force: bool = Option(False, "--force", help="Skip confirmation"),
):
    """Remove a profile."""
    from .base import confirm_action
    try:
        if not force:
            if not confirm_action(f"Are you sure you want to remove profile '{profile_name}'?"):
                return
        sdk = await get_sdk_with_auth()
        await sdk.profiles.delete_profile(profile_name)
        success_message(f"Profile '{profile_name}' removed successfully")
    except Exception as e:
        error_message(f"Failed to remove profile: {str(e)}")
        raise SystemExit(1)


@profile_app.async_command("set-default")
async def set_default(
    profile_name: str = Argument(..., help="Profile name to set as default"),
):
    """Set a profile as the default."""
    try:
        sdk = await get_sdk_with_auth()
        await sdk.profiles.set_default_profile(profile_name)
        success_message(f"Profile '{profile_name}' set as default")
    except Exception as e:
        error_message(f"Failed to set default profile: {str(e)}")
        raise SystemExit(1)


@profile_app.async_command()
async def stats():
    """Show profile usage statistics."""
    try:
        sdk = await get_sdk_with_auth()
        data = await sdk.profiles.get_profile_stats()
        if data:
            from rich.columns import Columns
            from rich.panel import Panel
            basic_panel = Panel(
                f"Total Profiles: [green]{data.get('total_profiles', 0)}[/green]\n"
                f"Active: [blue]{data.get('active_profiles', 0)}[/blue]",
                title="📊 Profile Stats",
                border_style="cyan"
            )
            usage_panel = Panel(
                f"Default Profile: [green]{data.get('default_profile', 'None')}[/green]\n"
                f"Most Used: [blue]{data.get('most_used_profile', 'N/A')}[/blue]",
                title="📈 Usage",
                border_style="green"
            )
            console.print(Columns([basic_panel, usage_panel]))
    except Exception as e:
        error_message(f"Failed to get profile statistics: {str(e)}")
        raise SystemExit(1)
