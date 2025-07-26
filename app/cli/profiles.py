"""
LLM Profile management CLI commands.

This module provides comprehensive LLM parameter profile management functionality
through the command line interface.

"""

import asyncio
import json
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..services.llm_profile_service import LLMProfileService
from .base import console, error_message, get_service_context, info_message, success_message

# Create the LLM profile management app
profile_app = typer.Typer(
    help="🎛️ LLM parameter profile management commands", rich_markup_mode="rich"
)


@profile_app.command("list")
def list_profiles(
    active_only: bool = typer.Option(
        True, "--active-only/--include-inactive", help="Show only active profiles"
    ),
    search: Optional[str] = typer.Option(
        None, "--search", "-s", help="Search in name, title, and description"
    ),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """
    List all LLM parameter profiles.
    
    Displays LLM profiles with filtering options for active status and search terms.
    Shows profile details including parameters, usage statistics, and status.
    
    The service returns a tuple (profiles, total_count) which is properly unpacked
    to handle the list of profile objects correctly.
    """

    async def _list_profiles():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                profiles_result = await profile_service.list_profiles(active_only=active_only, search=search)
                # list_profiles returns a tuple (List[LLMProfile], int)
                profiles, total_count = profiles_result

            if not profiles:
                info_message("No LLM profiles found")
                return

            if detailed:
                for profile in profiles:
                    status_color = "green" if profile.is_active else "yellow"
                    default_marker = " (DEFAULT)" if profile.is_default else ""

                    # Build parameters display
                    params = []
                    if profile.temperature is not None:
                        params.append(f"Temperature: {profile.temperature}")
                    if profile.top_p is not None:
                        params.append(f"Top-p: {profile.top_p}")
                    if profile.top_k is not None:
                        params.append(f"Top-k: {profile.top_k}")
                    if profile.max_tokens is not None:
                        params.append(f"Max tokens: {profile.max_tokens}")
                    if profile.presence_penalty is not None:
                        params.append(f"Presence penalty: {profile.presence_penalty}")
                    if profile.frequency_penalty is not None:
                        params.append(f"Frequency penalty: {profile.frequency_penalty}")

                    params_str = ", ".join(params) if params else "No parameters set"

                    panel_content = f"""
[bold]Title:[/bold] {profile.title}
[bold]Active:[/bold] [{status_color}]{profile.is_active}[/{status_color}]
[bold]Default:[/bold] {'Yes' if profile.is_default else 'No'}
[bold]Usage Count:[/bold] {profile.usage_count}
[bold]Last Used:[/bold] {profile.last_used_at or 'Never'}
[bold]Description:[/bold] {profile.description or 'No description'}

[bold]Parameters:[/bold] {params_str}
"""

                    console.print(
                        Panel(
                            panel_content.strip(),
                            title=f"🎛️ {profile.name}{default_marker}",
                            border_style=status_color,
                        )
                    )
                    console.print()
            else:
                table = Table(title="LLM Profiles", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Title")
                table.add_column("Status")
                table.add_column("Usage")
                table.add_column("Last Used")
                table.add_column("Key Parameters")

                for profile in profiles:
                    status = "🟢 Active" if profile.is_active else "🟡 Inactive"
                    if profile.is_default:
                        status += " (DEFAULT)"

                    last_used = (
                        profile.last_used_at.strftime("%Y-%m-%d")
                        if profile.last_used_at
                        else "Never"
                    )

                    # Show key parameters
                    key_params = []
                    if profile.temperature is not None:
                        key_params.append(f"T:{profile.temperature}")
                    if profile.top_p is not None:
                        key_params.append(f"P:{profile.top_p}")
                    if profile.max_tokens is not None:
                        key_params.append(f"Max:{profile.max_tokens}")

                    params_str = ", ".join(key_params) if key_params else "None"

                    table.add_row(
                        profile.name,
                        profile.title,
                        status,
                        str(profile.usage_count),
                        last_used,
                        params_str,
                    )

                console.print(table)

        except Exception as e:
            error_message(f"Failed to list profiles: {e}")

    asyncio.run(_list_profiles())


@profile_app.command("show")
def show_profile(name: str = typer.Argument(..., help="Profile name")):
    """Show detailed information about a specific LLM profile."""

    async def _show_profile():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                profile = await profile_service.get_profile(name)
            if not profile:
                error_message(f"Profile not found: {name}")
                return

            status_color = "green" if profile.is_active else "yellow"
            default_marker = " (DEFAULT)" if profile.is_default else ""

            # Format all parameters
            params_content = []

            # Core parameters
            core_params = [
                ("Temperature", profile.temperature),
                ("Top-p", profile.top_p),
                ("Top-k", profile.top_k),
                ("Repeat Penalty", profile.repeat_penalty),
                ("Max Tokens", profile.max_tokens),
                ("Max New Tokens", profile.max_new_tokens),
                ("Context Length", profile.context_length),
                ("Presence Penalty", profile.presence_penalty),
                ("Frequency Penalty", profile.frequency_penalty),
            ]

            for param_name, value in core_params:
                if value is not None:
                    params_content.append(f"[bold]{param_name}:[/bold] {value}")

            if profile.stop:
                stop_str = (
                    json.dumps(profile.stop)
                    if isinstance(profile.stop, list)
                    else str(profile.stop)
                )
                params_content.append(f"[bold]Stop Sequences:[/bold] {stop_str}")

            if profile.other_params:
                params_content.append(
                    f"[bold]Other Parameters:[/bold] {json.dumps(profile.other_params, indent=2)}"
                )

            if not params_content:
                params_content.append("No parameters configured")

            panel_content = f"""
[bold]Name:[/bold] {profile.name}
[bold]Title:[/bold] {profile.title}
[bold]Active:[/bold] [{status_color}]{profile.is_active}[/{status_color}]
[bold]Default:[/bold] {'Yes' if profile.is_default else 'No'}
[bold]Usage Count:[/bold] {profile.usage_count}
[bold]Last Used:[/bold] {profile.last_used_at or 'Never'}
[bold]Created:[/bold] {profile.created_at}
[bold]Updated:[/bold] {profile.updated_at}
[bold]Description:[/bold] {profile.description or 'No description'}

[bold]Parameters:[/bold]
{chr(10).join(params_content)}
"""

            console.print(
                Panel(
                    panel_content.strip(),
                    title=f"🎛️ {profile.name}{default_marker}",
                    border_style=status_color,
                )
            )

        except Exception as e:
            error_message(f"Failed to show profile: {e}")

    asyncio.run(_show_profile())


@profile_app.command("add")
def add_profile(
    name: str = typer.Argument(..., help="Profile name/identifier"),
    title: str = typer.Option(..., "--title", "-t", help="Profile title"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Profile description"
    ),
    set_default: bool = typer.Option(False, "--default", help="Set as default profile"),
    inactive: bool = typer.Option(False, "--inactive", help="Create profile in inactive state"),
    # LLM Parameters
    temperature: Optional[float] = typer.Option(
        None, "--temperature", help="Temperature (0.0-2.0)"
    ),
    top_p: Optional[float] = typer.Option(None, "--top-p", help="Top-p nucleus sampling (0.0-1.0)"),
    top_k: Optional[int] = typer.Option(None, "--top-k", help="Top-k sampling"),
    repeat_penalty: Optional[float] = typer.Option(
        None, "--repeat-penalty", help="Repetition penalty"
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens", help="Maximum tokens to generate"
    ),
    max_new_tokens: Optional[int] = typer.Option(
        None, "--max-new-tokens", help="Maximum new tokens"
    ),
    context_length: Optional[int] = typer.Option(None, "--context-length", help="Context length"),
    presence_penalty: Optional[float] = typer.Option(
        None, "--presence-penalty", help="Presence penalty (-2.0 to 2.0)"
    ),
    frequency_penalty: Optional[float] = typer.Option(
        None, "--frequency-penalty", help="Frequency penalty (-2.0 to 2.0)"
    ),
    stop: Optional[str] = typer.Option(None, "--stop", help="Stop sequences (JSON array)"),
):
    """Add a new LLM parameter profile."""

    async def _add_profile():
        try:
            # Validate parameters
            parameters = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "max_tokens": max_tokens,
                "max_new_tokens": max_new_tokens,
                "context_length": context_length,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
            }

            # Parse stop sequences
            if stop:
                try:
                    parameters["stop"] = json.loads(stop)
                except json.JSONDecodeError:
                    error_message("Invalid JSON format for stop sequences")
                    return

            async with get_service_context(LLMProfileService) as profile_service:
                # Validate parameters
                errors = await profile_service.validate_parameters(**parameters)
                if errors:
                    error_message("Parameter validation errors:")
                    for param, error in errors.items():
                        console.print(f"  • {param}: {error}")
                    return

                # Filter out None values
                parameters = {k: v for k, v in parameters.items() if v is not None}

                profile = await profile_service.create_profile(
                    name=name,
                    title=title,
                    description=description,
                    is_default=set_default,
                    **parameters,
                )

                # Set active status
                if inactive:
                    await profile_service.deactivate_profile(name)

                success_message(f"Added LLM profile: {profile.name}")

        except Exception as e:
            error_message(f"Failed to add profile: {e}")

    asyncio.run(_add_profile())


@profile_app.command("update")
def update_profile(
    name: str = typer.Argument(..., help="Profile name"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    # LLM Parameters
    temperature: Optional[float] = typer.Option(
        None, "--temperature", help="Temperature (0.0-2.0)"
    ),
    top_p: Optional[float] = typer.Option(None, "--top-p", help="Top-p nucleus sampling (0.0-1.0)"),
    top_k: Optional[int] = typer.Option(None, "--top-k", help="Top-k sampling"),
    repeat_penalty: Optional[float] = typer.Option(
        None, "--repeat-penalty", help="Repetition penalty"
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens", help="Maximum tokens to generate"
    ),
    max_new_tokens: Optional[int] = typer.Option(
        None, "--max-new-tokens", help="Maximum new tokens"
    ),
    context_length: Optional[int] = typer.Option(None, "--context-length", help="Context length"),
    presence_penalty: Optional[float] = typer.Option(
        None, "--presence-penalty", help="Presence penalty (-2.0 to 2.0)"
    ),
    frequency_penalty: Optional[float] = typer.Option(
        None, "--frequency-penalty", help="Frequency penalty (-2.0 to 2.0)"
    ),
    stop: Optional[str] = typer.Option(None, "--stop", help="Stop sequences (JSON array)"),
    clear_stop: bool = typer.Option(False, "--clear-stop", help="Clear stop sequences"),
):
    """Update an existing LLM profile."""

    async def _update_profile():
        try:
            updates = {}

            if title is not None:
                updates["title"] = title
            if description is not None:
                updates["description"] = description

            # LLM parameters
            param_updates = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "max_tokens": max_tokens,
                "max_new_tokens": max_new_tokens,
                "context_length": context_length,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
            }

            # Parse stop sequences
            if stop:
                try:
                    param_updates["stop"] = json.loads(stop)
                except json.JSONDecodeError:
                    error_message("Invalid JSON format for stop sequences")
                    return
            elif clear_stop:
                param_updates["stop"] = None

            # Filter and validate parameters
            param_updates = {k: v for k, v in param_updates.items() if v is not None}
            
            async with get_service_context(LLMProfileService) as profile_service:
                if param_updates:
                    errors = await profile_service.validate_parameters(**param_updates)
                    if errors:
                        error_message("Parameter validation errors:")
                        for param, error in errors.items():
                            console.print(f"  • {param}: {error}")
                        return

                    updates.update(param_updates)

                if not updates:
                    error_message("No updates specified")
                    return

                profile = await profile_service.update_profile(name, **updates)
                if profile:
                    success_message(f"Updated LLM profile: {name}")
                else:
                    error_message(f"Profile not found: {name}")

        except Exception as e:
            error_message(f"Failed to update profile: {e}")

    asyncio.run(_update_profile())


@profile_app.command("remove")
def remove_profile(
    name: str = typer.Argument(..., help="Profile name"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation prompt"),
):
    """Remove an LLM profile."""

    async def _remove_profile():
        try:
            if not confirm:
                confirmed = typer.confirm(f"Are you sure you want to remove profile '{name}'?")
                if not confirmed:
                    info_message("Operation cancelled")
                    return

            async with get_service_context(LLMProfileService) as profile_service:
                success = await profile_service.delete_profile(name)
                if success:
                    success_message(f"Removed LLM profile: {name}")
                else:
                    error_message(f"Profile not found: {name}")

        except Exception as e:
            error_message(f"Failed to remove profile: {e}")

    asyncio.run(_remove_profile())


@profile_app.command("set-default")
def set_default_profile(name: str = typer.Argument(..., help="Profile name")):
    """Set a profile as the default."""

    async def _set_default():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                success = await profile_service.set_default_profile(name)
                if success:
                    success_message(f"Set default LLM profile: {name}")
                else:
                    error_message(f"Profile not found: {name}")

        except Exception as e:
            error_message(f"Failed to set default profile: {e}")

    asyncio.run(_set_default())


@profile_app.command("activate")
def activate_profile(name: str = typer.Argument(..., help="Profile name")):
    """Activate a profile."""

    async def _activate():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                success = await profile_service.activate_profile(name)
                if success:
                    success_message(f"Activated LLM profile: {name}")
                else:
                    error_message(f"Profile not found: {name}")

        except Exception as e:
            error_message(f"Failed to activate profile: {e}")

    asyncio.run(_activate())


@profile_app.command("deactivate")
def deactivate_profile(name: str = typer.Argument(..., help="Profile name")):
    """Deactivate a profile."""

    async def _deactivate():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                success = await profile_service.deactivate_profile(name)
                if success:
                    success_message(f"Deactivated LLM profile: {name}")
                else:
                    error_message(f"Profile not found: {name}")

        except Exception as e:
            error_message(f"Failed to deactivate profile: {e}")

    asyncio.run(_deactivate())


@profile_app.command("clone")
def clone_profile(
    source: str = typer.Argument(..., help="Source profile name"),
    new_name: str = typer.Argument(..., help="New profile name"),
    new_title: Optional[str] = typer.Option(None, "--title", "-t", help="New profile title"),
):
    """Clone an existing profile with a new name."""

    async def _clone_profile():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                profile = await profile_service.clone_profile(
                    source_name=source, new_name=new_name, new_title=new_title
                )

            if profile:
                success_message(f"Cloned profile '{source}' to '{new_name}'")
            else:
                error_message(f"Source profile not found: {source}")

        except Exception as e:
            error_message(f"Failed to clone profile: {e}")

    asyncio.run(_clone_profile())


@profile_app.command("stats")
def show_stats():
    """Show LLM profile usage statistics."""

    async def _show_stats():
        try:
            async with get_service_context(LLMProfileService) as profile_service:
                stats = await profile_service.get_profile_stats()

            # Overview panel
            overview_content = f"""
[bold]Total Profiles:[/bold] {stats['total_profiles']}
[bold]Active Profiles:[/bold] {stats['active_profiles']}
[bold]Inactive Profiles:[/bold] {stats['inactive_profiles']}
[bold]Default Profile:[/bold] {stats['default_profile'] or 'None set'}
"""

            console.print(
                Panel(
                    overview_content.strip(),
                    title="📊 LLM Profile Statistics",
                    border_style="blue",
                )
            )

            # Most used profiles
            if stats["most_used"]:
                table = Table(title="Most Used Profiles", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Title")
                table.add_column("Usage Count")
                table.add_column("Last Used")

                for profile in stats["most_used"]:
                    last_used = (
                        profile["last_used_at"].strftime("%Y-%m-%d")
                        if profile["last_used_at"]
                        else "Never"
                    )
                    table.add_row(
                        profile["name"],
                        profile["title"],
                        str(profile["usage_count"]),
                        last_used,
                    )

                console.print(table)

            # Recently used profiles
            if stats["recently_used"]:
                table = Table(title="Recently Used Profiles", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Title")
                table.add_column("Usage Count")
                table.add_column("Last Used")

                for profile in stats["recently_used"]:
                    last_used = (
                        profile["last_used_at"].strftime("%Y-%m-%d %H:%M")
                        if profile["last_used_at"]
                        else "Never"
                    )
                    table.add_row(
                        profile["name"],
                        profile["title"],
                        str(profile["usage_count"]),
                        last_used,
                    )

                console.print(table)

        except Exception as e:
            error_message(f"Failed to get statistics: {e}")

    asyncio.run(_show_stats())
