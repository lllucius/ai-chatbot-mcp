"""
LLM profile management commands for the API-based CLI.

This module provides LLM parameter profile management functionality through API calls.
"""

import typer
from .base import get_sdk_with_auth, console, error_message, success_message

profile_app = typer.Typer(help="🎛️ LLM parameter profile management commands")


@profile_app.command()
def list():
    """List all LLM parameter profiles."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.profiles.list_profiles()
        
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


@profile_app.command()
def show(
    profile_name: str = typer.Argument(..., help="Profile name to show"),
):
    """Show detailed information about a specific LLM profile."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.profiles.get_profile(profile_name)
        
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
    
    try:
        sdk = get_sdk_with_auth()
        
        from client.ai_chatbot_sdk import LLMProfileCreate
        
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
        
        profile_data = LLMProfileCreate(
            name=name,
            title=title,
            description=description,
            model_name=model,
            parameters=parameters,
            is_default=False
        )
        
        result = sdk.profiles.create_profile(profile_data)
        success_message(f"Profile '{name}' created successfully")
    
    except Exception as e:
        error_message(f"Failed to add profile: {str(e)}")
        raise typer.Exit(1)


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
    
    try:
        sdk = get_sdk_with_auth()
        
        update_data = {}
        
        if title:
            update_data["title"] = title
        if description:
            update_data["description"] = description
        
        # Build parameters update
        if any([model, temperature is not None, max_tokens is not None]):
            # Get current profile first
            current_profile = sdk.profiles.get_profile(profile_name)
            current_params = current_profile.parameters
            
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
        
        result = sdk.profiles.update_profile(profile_name, update_data)
        success_message(f"Profile '{profile_name}' updated successfully")
    
    except Exception as e:
        error_message(f"Failed to update profile: {str(e)}")
        raise typer.Exit(1)


@profile_app.command()
def remove(
    profile_name: str = typer.Argument(..., help="Profile name to remove"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Remove an LLM profile."""
    
    try:
        from .base import confirm_action
        
        if not force:
            if not confirm_action(f"Are you sure you want to remove profile '{profile_name}'?"):
                return
        
        sdk = get_sdk_with_auth()
        
        result = sdk.profiles.delete_profile(profile_name)
        success_message(f"Profile '{profile_name}' removed successfully")
    
    except Exception as e:
        error_message(f"Failed to remove profile: {str(e)}")
        raise typer.Exit(1)


@profile_app.command("set-default")
def set_default(
    profile_name: str = typer.Argument(..., help="Profile name to set as default"),
):
    """Set a profile as the default."""
    
    try:
        sdk = get_sdk_with_auth()
        
        result = sdk.profiles.set_default_profile(profile_name)
        success_message(f"Profile '{profile_name}' set as default")
    
    except Exception as e:
        error_message(f"Failed to set default profile: {str(e)}")
        raise typer.Exit(1)


@profile_app.command()
def activate(
    profile_name: str = typer.Argument(..., help="Profile name to activate"),
):
    """Activate a profile."""
    
    try:
        sdk = get_sdk_with_auth()
        
        update_data = {"is_active": True}
        result = sdk.profiles.update_profile(profile_name, update_data)
        success_message(f"Profile '{profile_name}' activated")
    
    except Exception as e:
        error_message(f"Failed to activate profile: {str(e)}")
        raise typer.Exit(1)


@profile_app.command()
def deactivate(
    profile_name: str = typer.Argument(..., help="Profile name to deactivate"),
):
    """Deactivate a profile."""
    
    try:
        sdk = get_sdk_with_auth()
        
        update_data = {"is_active": False}
        result = sdk.profiles.update_profile(profile_name, update_data)
        success_message(f"Profile '{profile_name}' deactivated")
    
    except Exception as e:
        error_message(f"Failed to deactivate profile: {str(e)}")
        raise typer.Exit(1)


@profile_app.command()
def clone(
    source_profile: str = typer.Argument(..., help="Source profile name to clone"),
    new_profile: str = typer.Argument(..., help="New profile name"),
    title: str = typer.Option(None, "--title", help="Title for new profile"),
):
    """Clone an existing profile with a new name."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Get source profile
        source = sdk.profiles.get_profile(source_profile)
        
        from client.ai_chatbot_sdk import LLMProfileCreate
        
        # Create new profile with cloned data
        new_data = LLMProfileCreate(
            name=new_profile,
            title=title or f"{source.title} (Copy)",
            description=source.description,
            model_name=source.model_name,
            parameters=source.parameters,
            is_default=False  # Clone should not be default
        )
        
        result = sdk.profiles.create_profile(new_data)
        success_message(f"Profile '{new_profile}' cloned from '{source_profile}'")
    
    except Exception as e:
        error_message(f"Failed to clone profile: {str(e)}")
        raise typer.Exit(1)


@profile_app.command()
def stats():
    """Show LLM profile usage statistics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.profiles.get_profile_stats()
        
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