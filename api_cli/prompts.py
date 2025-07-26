"""
Prompt management commands for the API-based CLI.

This module provides prompt management functionality through API calls.
"""

import typer
from .base import get_sdk_with_auth, console, error_message, success_message

prompt_app = typer.Typer(help="📝 Prompt management commands")


@prompt_app.command()
def list():
    """List all prompts."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.prompts.list_prompts()
        
        if data:
            from rich.table import Table
            from .base import format_timestamp
            
            prompts = data.get("items", []) if isinstance(data, dict) else data
            
            table = Table(title=f"Prompts ({len(prompts)} total)")
            table.add_column("Name", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Category", style="blue")
            table.add_column("Default", style="green")
            table.add_column("Active", style="yellow")
            
            for prompt in prompts:
                table.add_row(
                    prompt.get("name", ""),
                    prompt.get("title", ""),
                    prompt.get("category", ""),
                    "Yes" if prompt.get("is_default") else "No",
                    "Yes" if prompt.get("is_active") else "No"
                )
            
            console.print(table)
    
    except Exception as e:
        error_message(f"Failed to list prompts: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def show(
    prompt_name: str = typer.Argument(..., help="Prompt name to show"),
):
    """Show detailed information about a specific prompt."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.prompts.get_prompt(prompt_name)
        
        if data:
            from rich.table import Table
            from rich.panel import Panel
            from .base import format_timestamp
            
            table = Table(title="Prompt Details")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Name", data.get("name", ""))
            table.add_row("Title", data.get("title", ""))
            table.add_row("Category", data.get("category", ""))
            table.add_row("Description", data.get("description", ""))
            table.add_row("Default", "Yes" if data.get("is_default") else "No")
            table.add_row("Active", "Yes" if data.get("is_active") else "No")
            table.add_row("Created", format_timestamp(data.get("created_at", "")))
            
            console.print(table)
            
            # Show content in a panel
            content = data.get("content", "")
            if content:
                content_panel = Panel(
                    content,
                    title="Prompt Content",
                    border_style="blue",
                    expand=False
                )
                console.print(content_panel)
            
            # Show tags if any
            tags = data.get("tags", [])
            if tags:
                console.print(f"\n[bold]Tags:[/bold] {', '.join(tags)}")
    
    except Exception as e:
        error_message(f"Failed to show prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def add(
    name: str = typer.Argument(..., help="Prompt name"),
    title: str = typer.Option(..., "--title", help="Prompt title"),
    content: str = typer.Option(..., "--content", help="Prompt content"),
    category: str = typer.Option("general", "--category", help="Prompt category"),
    description: str = typer.Option("", "--description", help="Prompt description"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
):
    """Add a new prompt."""
    
    try:
        sdk = get_sdk_with_auth()
        
        from client.ai_chatbot_sdk import PromptCreate
        
        prompt_data = PromptCreate(
            name=name,
            title=title,
            content=content,
            category=category,
            description=description,
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
        )
        
        result = sdk.prompts.create_prompt(prompt_data)
        success_message(f"Prompt '{name}' added successfully")
    
    except Exception as e:
        error_message(f"Failed to add prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def update(
    prompt_name: str = typer.Argument(..., help="Prompt name to update"),
    title: str = typer.Option(None, "--title", help="New title"),
    content: str = typer.Option(None, "--content", help="New content"),
    category: str = typer.Option(None, "--category", help="New category"),
    description: str = typer.Option(None, "--description", help="New description"),
    tags: str = typer.Option(None, "--tags", help="Comma-separated tags"),
):
    """Update an existing prompt."""
    
    try:
        sdk = get_sdk_with_auth()
        
        update_data = {}
        
        if title:
            update_data["title"] = title
        if content:
            update_data["content"] = content
        if category:
            update_data["category"] = category
        if description:
            update_data["description"] = description
        if tags:
            update_data["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        if not update_data:
            error_message("No update fields provided")
            return
        
        result = sdk.prompts.update_prompt(prompt_name, update_data)
        success_message(f"Prompt '{prompt_name}' updated successfully")
    
    except Exception as e:
        error_message(f"Failed to update prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def remove(
    prompt_name: str = typer.Argument(..., help="Prompt name to remove"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Remove a prompt."""
    
    try:
        from .base import confirm_action
        
        if not force:
            if not confirm_action(f"Are you sure you want to remove prompt '{prompt_name}'?"):
                return
        
        sdk = get_sdk_with_auth()
        
        result = sdk.prompts.delete_prompt(prompt_name)
        success_message(f"Prompt '{prompt_name}' removed successfully")
    
    except Exception as e:
        error_message(f"Failed to remove prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command("set-default")
def set_default(
    prompt_name: str = typer.Argument(..., help="Prompt name to set as default"),
):
    """Set a prompt as the default."""
    
    try:
        sdk = get_sdk_with_auth()
        
        result = sdk.prompts.set_default_prompt(prompt_name)
        success_message(f"Prompt '{prompt_name}' set as default")
    
    except Exception as e:
        error_message(f"Failed to set default prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def activate(
    prompt_name: str = typer.Argument(..., help="Prompt name to activate"),
):
    """Activate a prompt."""
    
    try:
        sdk = get_sdk_with_auth()
        
        update_data = {"is_active": True}
        result = sdk.prompts.update_prompt(prompt_name, update_data)
        success_message(f"Prompt '{prompt_name}' activated")
    
    except Exception as e:
        error_message(f"Failed to activate prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def deactivate(
    prompt_name: str = typer.Argument(..., help="Prompt name to deactivate"),
):
    """Deactivate a prompt."""
    
    try:
        sdk = get_sdk_with_auth()
        
        update_data = {"is_active": False}
        result = sdk.prompts.update_prompt(prompt_name, update_data)
        success_message(f"Prompt '{prompt_name}' deactivated")
    
    except Exception as e:
        error_message(f"Failed to deactivate prompt: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def categories():
    """List all available prompt categories."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.prompts.get_categories()
        
        if data:
            from rich.table import Table
            
            categories = data.get("categories", [])
            
            table = Table(title="Prompt Categories")
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="green")
            
            for cat in categories:
                table.add_row(
                    cat.get("name", ""),
                    str(cat.get("count", 0))
                )
            
            console.print(table)
    
    except Exception as e:
        error_message(f"Failed to get categories: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def tags():
    """List all available prompt tags."""
    
    try:
        # This would need to be implemented in the API
        # For now, just show a placeholder
        console.print("[yellow]Tag listing not yet implemented in API[/yellow]")
    
    except Exception as e:
        error_message(f"Failed to get tags: {str(e)}")
        raise typer.Exit(1)


@prompt_app.command()
def stats():
    """Show prompt usage statistics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.prompts.get_prompt_stats()
        
        if data:
            from rich.panel import Panel
            from rich.columns import Columns
            
            # Basic stats
            basic_panel = Panel(
                f"Total Prompts: [green]{data.get('total_prompts', 0)}[/green]\n"
                f"Active: [blue]{data.get('active_prompts', 0)}[/blue]\n"
                f"Categories: [yellow]{data.get('total_categories', 0)}[/yellow]",
                title="📊 Prompt Stats",
                border_style="cyan"
            )
            
            # Usage stats (if available)
            usage_panel = Panel(
                f"Default Prompt: [green]{data.get('default_prompt', 'None')}[/green]\n"
                f"Most Used: [blue]{data.get('most_used_prompt', 'N/A')}[/blue]",
                title="📈 Usage",
                border_style="green"
            )
            
            console.print(Columns([basic_panel, usage_panel]))
    
    except Exception as e:
        error_message(f"Failed to get prompt statistics: {str(e)}")
        raise typer.Exit(1)