"""
LLM profile management commands for the API-based CLI.

This module provides LLM parameter profile management functionality through API calls.
"""

import asyncio
import typer
from .base import get_client_with_auth, handle_api_response, console, error_message

profile_app = typer.Typer(help="🎛️ LLM parameter profile management commands")


@profile_app.command()
def list():
    """List all LLM parameter profiles."""
    
    async def _list_profiles():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/profiles/")
            data = handle_api_response(response, "listing profiles")
            
            if data:
                from rich.table import Table
                from .base import format_timestamp
                
                profiles = data.get("items", []) if isinstance(data, dict) else data
                
                table = Table(title=f"LLM Profiles ({len(profiles)} total)")
                table.add_column("Name", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Model", style="blue")
                table.add_column("Temperature", style="green")
                table.add_column("Default", style="yellow")
                table.add_column("Active", style="magenta")
                
                for profile in profiles:
                    params = profile.get("parameters", {})
                    table.add_row(
                        profile.get("name", ""),
                        profile.get("title", ""),
                        params.get("model", ""),
                        str(params.get("temperature", "")),
                        "Yes" if profile.get("is_default") else "No",
                        "Yes" if profile.get("is_active") else "No"
                    )
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to list profiles: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_list_profiles())


@profile_app.command()
def show(
    profile_name: str = typer.Argument(..., help="Profile name to show"),
):
    """Show detailed information about a specific LLM profile."""
    
    async def _show_profile():
        client = get_client_with_auth()
        
        try:
            response = await client.get(f"/api/v1/profiles/{profile_name}")
            data = handle_api_response(response, "getting profile details")
            
            if data:
                from rich.table import Table
                from rich.panel import Panel
                from .base import format_timestamp
                
                # Basic info
                table = Table(title="Profile Details")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Name", data.get("name", ""))
                table.add_row("Title", data.get("title", ""))
                table.add_row("Description", data.get("description", ""))
                table.add_row("Default", "Yes" if data.get("is_default") else "No")
                table.add_row("Active", "Yes" if data.get("is_active") else "No")
                table.add_row("Created", format_timestamp(data.get("created_at", "")))
                
                console.print(table)
                
                # Parameters
                params = data.get("parameters", {})
                if params:
                    param_content = "\n".join([
                        f"[cyan]{key}:[/cyan] {value}" 
                        for key, value in params.items()
                    ])
                    
                    param_panel = Panel(
                        param_content,
                        title="LLM Parameters",
                        border_style="blue",
                        expand=False
                    )
                    console.print(param_panel)
        
        except Exception as e:
            error_message(f"Failed to show profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_profile())


@profile_app.command()
def add(
    name: str = typer.Argument(..., help="Profile name"),
    title: str = typer.Option(..., "--title", help="Profile title"),
    model: str = typer.Option("gpt-4", "--model", help="LLM model"),
    temperature: float = typer.Option(0.7, "--temperature", help="Temperature (0.0-2.0)"),
    max_tokens: int = typer.Option(None, "--max-tokens", help="Maximum tokens"),
    top_p: float = typer.Option(None, "--top-p", help="Top P (0.0-1.0)"),
    frequency_penalty: float = typer.Option(None, "--frequency-penalty", help="Frequency penalty"),
    presence_penalty: float = typer.Option(None, "--presence-penalty", help="Presence penalty"),
    description: str = typer.Option("", "--description", help="Profile description"),
):
    """Add a new LLM parameter profile."""
    
    async def _add_profile():
        client = get_client_with_auth()
        
        try:
            # Build parameters
            parameters = {
                "model": model,
                "temperature": temperature
            }
            
            if max_tokens is not None:
                parameters["max_tokens"] = max_tokens
            if top_p is not None:
                parameters["top_p"] = top_p
            if frequency_penalty is not None:
                parameters["frequency_penalty"] = frequency_penalty
            if presence_penalty is not None:
                parameters["presence_penalty"] = presence_penalty
            
            profile_data = {
                "name": name,
                "title": title,
                "description": description,
                "parameters": parameters,
                "is_active": True
            }
            
            response = await client.post("/api/v1/profiles/", data=profile_data)
            handle_api_response(response, "adding profile")
        
        except Exception as e:
            error_message(f"Failed to add profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_add_profile())


@profile_app.command()
def update(
    profile_name: str = typer.Argument(..., help="Profile name to update"),
    title: str = typer.Option(None, "--title", help="New title"),
    model: str = typer.Option(None, "--model", help="New model"),
    temperature: float = typer.Option(None, "--temperature", help="New temperature"),
    max_tokens: int = typer.Option(None, "--max-tokens", help="New max tokens"),
    description: str = typer.Option(None, "--description", help="New description"),
):
    """Update an existing LLM profile."""
    
    async def _update_profile():
        client = get_client_with_auth()
        
        try:
            update_data = {}
            
            if title:
                update_data["title"] = title
            if description:
                update_data["description"] = description
            
            # Build parameters update
            if any([model, temperature is not None, max_tokens is not None]):
                # Get current profile first
                current_response = await client.get(f"/api/v1/profiles/{profile_name}")
                if not current_response:
                    error_message("Profile not found")
                    return
                
                current_params = current_response.get("parameters", {})
                
                if model:
                    current_params["model"] = model
                if temperature is not None:
                    current_params["temperature"] = temperature
                if max_tokens is not None:
                    current_params["max_tokens"] = max_tokens
                
                update_data["parameters"] = current_params
            
            if not update_data:
                error_message("No update fields provided")
                return
            
            response = await client.put(f"/api/v1/profiles/{profile_name}", data=update_data)
            handle_api_response(response, "updating profile")
        
        except Exception as e:
            error_message(f"Failed to update profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_update_profile())


@profile_app.command()
def remove(
    profile_name: str = typer.Argument(..., help="Profile name to remove"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Remove an LLM profile."""
    
    async def _remove_profile():
        from .base import confirm_action
        
        if not force:
            if not confirm_action(f"Are you sure you want to remove profile '{profile_name}'?"):
                return
        
        client = get_client_with_auth()
        
        try:
            response = await client.delete(f"/api/v1/profiles/{profile_name}")
            handle_api_response(response, "removing profile")
        
        except Exception as e:
            error_message(f"Failed to remove profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_remove_profile())


@profile_app.command("set-default")
def set_default(
    profile_name: str = typer.Argument(..., help="Profile name to set as default"),
):
    """Set a profile as the default."""
    
    async def _set_default():
        client = get_client_with_auth()
        
        try:
            response = await client.post(f"/api/v1/profiles/{profile_name}/set-default")
            handle_api_response(response, "setting default profile")
        
        except Exception as e:
            error_message(f"Failed to set default profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_set_default())


@profile_app.command()
def activate(
    profile_name: str = typer.Argument(..., help="Profile name to activate"),
):
    """Activate a profile."""
    
    async def _activate_profile():
        client = get_client_with_auth()
        
        try:
            update_data = {"is_active": True}
            response = await client.put(f"/api/v1/profiles/{profile_name}", data=update_data)
            handle_api_response(response, "activating profile")
        
        except Exception as e:
            error_message(f"Failed to activate profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_activate_profile())


@profile_app.command()
def deactivate(
    profile_name: str = typer.Argument(..., help="Profile name to deactivate"),
):
    """Deactivate a profile."""
    
    async def _deactivate_profile():
        client = get_client_with_auth()
        
        try:
            update_data = {"is_active": False}
            response = await client.put(f"/api/v1/profiles/{profile_name}", data=update_data)
            handle_api_response(response, "deactivating profile")
        
        except Exception as e:
            error_message(f"Failed to deactivate profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_deactivate_profile())


@profile_app.command()
def clone(
    source_profile: str = typer.Argument(..., help="Source profile name to clone"),
    new_profile: str = typer.Argument(..., help="New profile name"),
    title: str = typer.Option(None, "--title", help="Title for new profile"),
):
    """Clone an existing profile with a new name."""
    
    async def _clone_profile():
        client = get_client_with_auth()
        
        try:
            # Get source profile
            source_response = await client.get(f"/api/v1/profiles/{source_profile}")
            if not source_response:
                error_message(f"Source profile '{source_profile}' not found")
                return
            
            # Create new profile with cloned data
            new_data = {
                "name": new_profile,
                "title": title or f"{source_response.get('title', '')} (Copy)",
                "description": source_response.get("description", ""),
                "parameters": source_response.get("parameters", {}),
                "is_active": True,
                "is_default": False  # Clone should not be default
            }
            
            response = await client.post("/api/v1/profiles/", data=new_data)
            handle_api_response(response, "cloning profile")
        
        except Exception as e:
            error_message(f"Failed to clone profile: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_clone_profile())


@profile_app.command()
def stats():
    """Show LLM profile usage statistics."""
    
    async def _show_stats():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/profiles/stats/")
            data = handle_api_response(response, "getting profile statistics")
            
            if data:
                from rich.panel import Panel
                from rich.columns import Columns
                
                # Basic stats
                basic_panel = Panel(
                    f"Total Profiles: [green]{data.get('total_profiles', 0)}[/green]\n"
                    f"Active: [blue]{data.get('active_profiles', 0)}[/blue]\n"
                    f"Default: [yellow]{data.get('default_profile', 'None')}[/yellow]",
                    title="📊 Profile Stats",
                    border_style="cyan"
                )
                
                # Model distribution
                models = data.get("model_distribution", {})
                model_content = "\n".join([
                    f"{model}: [green]{count}[/green]" 
                    for model, count in models.items()
                ]) if models else "No data"
                
                model_panel = Panel(
                    model_content,
                    title="🤖 Models",
                    border_style="green"
                )
                
                console.print(Columns([basic_panel, model_panel]))
                
                # Usage stats (if available)
                usage = data.get("usage_stats", {})
                if usage:
                    from rich.table import Table
                    
                    table = Table(title="Most Used Profiles")
                    table.add_column("Profile", style="cyan")
                    table.add_column("Usage Count", style="green")
                    
                    for profile_name, count in usage.items():
                        table.add_row(profile_name, str(count))
                    
                    console.print(table)
        
        except Exception as e:
            error_message(f"Failed to get profile statistics: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_stats())