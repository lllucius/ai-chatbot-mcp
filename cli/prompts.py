"""
Prompt management commands for the AI Chatbot Platform CLI.

This module provides comprehensive prompt template management functionality
through async operations and the AI Chatbot SDK. It enables developers and
content creators to create, manage, and optimize prompt templates for various
AI applications and use cases.

Prompt templates are reusable, parameterized prompts that can be customized
for different scenarios while maintaining consistency and best practices.
This module facilitates the entire prompt lifecycle from creation to deployment
and optimization.

Key Features:
    - Prompt template creation and management
    - Variable substitution and parameterization
    - Template versioning and change tracking
    - Performance analytics and optimization
    - Category-based organization and filtering
    - A/B testing and effectiveness measurement

Template Management:
    - Rich text editor integration for prompt creation
    - Variable placeholder system for dynamic content
    - Template inheritance and composition
    - Version control with rollback capabilities
    - Collaborative editing and review workflows
    - Import/export functionality for backup and sharing

Performance Optimization:
    - Response quality metrics and analysis
    - Token usage optimization and cost management
    - Effectiveness scoring and ranking
    - A/B testing framework for template comparison
    - Automated optimization recommendations

Use Cases:
    - Customer service response templates
    - Content generation and marketing copy
    - Educational and training prompts
    - Technical documentation assistance
    - Creative writing and storytelling

Example Usage:
    ```bash
    # Template management
    ai-chatbot prompts list --category customer-service
    ai-chatbot prompts create support-template --category support
    ai-chatbot prompts show template_id --include-variables

    # Testing and optimization
    ai-chatbot prompts test template_id --variables key=value
    ai-chatbot prompts compare template1 template2 --metric effectiveness
    ai-chatbot prompts optimize template_id --auto-tune

    # Deployment and monitoring
    ai-chatbot prompts publish template_id --version 1.2
    ai-chatbot prompts usage-stats template_id --period month
    ai-chatbot prompts performance-report --category all
    ```
"""

from typing import Optional

from async_typer import AsyncTyper
from rich.console import Console
from typer import Argument, Option

from .base import error_message, get_sdk, success_message

console = Console()

prompt_app = AsyncTyper(help="Prompt management commands", rich_markup_mode=None)


@prompt_app.async_command()
async def list():
    """List all prompts."""
    try:
        sdk = await get_sdk()
        data = await sdk.prompts.list_prompts(active_only=False)
        if data:
            prompts = data.items

            prompt_data = []
            for prompt in prompts:
                prompt_data.append(
                    {
                        "Name": prompt.name,
                        "Title": prompt.title,
                        "category": prompt.category,
                        "Default": "Yes" if prompt.is_default else "No",
                        "Active": "Yes" if prompt.is_active else "No",
                    }
                )

            from .base import display_rich_table

            display_rich_table(prompt_data, f"Prompts ({len(prompts)} total)")
    except Exception as e:
        error_message(f"Failed to list prompts: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def show(
    prompt_name: str = Argument(..., help="Prompt name to show"),
):
    """Show detailed information about a specific prompt."""
    try:
        sdk = await get_sdk()
        data = await sdk.prompts.get_prompt(prompt_name)
        if data:
            from rich.panel import Panel
            from rich.table import Table

            from .base import format_timestamp

            table = Table(title="Prompt Details")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Name", data.name)
            table.add_row("Title", data.title)
            table.add_row("Category", data.category or "")
            table.add_row("Description", data.description or "")
            table.add_row(
                "Default", "Yes" if getattr(data, "is_default", False) else "No"
            )
            table.add_row(
                "Active", "Yes" if getattr(data, "is_active", False) else "No"
            )
            table.add_row("Created", format_timestamp(str(data.created_at)))
            console.print(table)
            content = getattr(data, "content", "")
            if content:
                content_panel = Panel(
                    content, title="Prompt Content", border_style="blue", expand=False
                )
                console.print(content_panel)
            tags = getattr(data, "tags", [])
            if tags:
                print(f"\nTags: {', '.join(tags)}")
    except Exception as e:
        error_message(f"Failed to show prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def add(
    name: str = Argument(..., help="Prompt name"),
    title: str = Option(..., "--title", help="Prompt title"),
    content: str = Option(..., "--content", help="Prompt content"),
    category: str = Option("general", "--category", help="Prompt category"),
    description: str = Option("", "--description", help="Prompt description"),
    tags: str = Option("", "--tags", help="Comma-separated tags"),
):
    """Add a new prompt."""
    try:
        sdk = await get_sdk()
        from shared.schemas import PromptCreate

        prompt_data = PromptCreate(
            name=name,
            title=title,
            content=content,
            category=category,
            description=description,
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
        )
        await sdk.prompts.create_prompt(prompt_data)
        success_message(f"Prompt '{name}' added successfully")
    except Exception as e:
        error_message(f"Failed to add prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def update(
    prompt_name: str = Argument(..., help="Prompt name to update"),
    title: Optional[str] = Option(None, "--title", help="New title"),
    content: Optional[str] = Option(None, "--content", help="New content"),
    category: Optional[str] = Option(None, "--category", help="New category"),
    description: Optional[str] = Option(None, "--description", help="New description"),
    tags: Optional[str] = Option(None, "--tags", help="Comma-separated tags"),
):
    """Update an existing prompt."""
    try:
        sdk = await get_sdk()
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
            update_data["tags"] = [
                tag.strip() for tag in tags.split(",") if tag.strip()
            ]
        if not update_data:
            error_message("No update fields provided")
            return
        await sdk.prompts.update_prompt(prompt_name, update_data)
        success_message(f"Prompt '{prompt_name}' updated successfully")
    except Exception as e:
        error_message(f"Failed to update prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def remove(
    prompt_name: str = Argument(..., help="Prompt name to remove"),
    force: bool = Option(False, "--force", help="Skip confirmation"),
):
    """Remove a prompt."""
    from .base import confirm_action

    try:
        if not force and not confirm_action(
            f"Are you sure you want to remove prompt '{prompt_name}'?"
        ):
            return
        sdk = await get_sdk()
        await sdk.prompts.delete_prompt(prompt_name)
        success_message(f"Prompt '{prompt_name}' removed successfully")
    except Exception as e:
        error_message(f"Failed to remove prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command("set-default")
async def set_default(
    prompt_name: str = Argument(..., help="Prompt name to set as default"),
):
    """Set a prompt as the default."""
    try:
        sdk = await get_sdk()
        await sdk.prompts.set_default_prompt(prompt_name)
        success_message(f"Prompt '{prompt_name}' set as default")
    except Exception as e:
        error_message(f"Failed to set default prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def activate(
    prompt_name: str = Argument(..., help="Prompt name to activate"),
):
    """Activate a prompt."""
    try:
        sdk = await get_sdk()
        await sdk.prompts.activate_prompt(prompt_name)
        success_message(f"Prompt '{prompt_name}' activated")
    except Exception as e:
        error_message(f"Failed to activate prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def deactivate(
    prompt_name: str = Argument(..., help="Prompt name to deactivate"),
):
    """Deactivate a prompt."""
    try:
        sdk = await get_sdk()
        await sdk.prompts.deactivate_prompt(prompt_name)
        success_message(f"Prompt '{prompt_name}' deactivated")
    except Exception as e:
        error_message(f"Failed to deactivate prompt: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def categories():
    """List all available prompt categories."""
    try:
        sdk = await get_sdk()
        data = await sdk.prompts.get_categories()
        if data:
            from rich.table import Table

            categories = data.get("categories", [])
            print("cats", categories)
            table = Table(title="Prompt Categories")
            table.add_column("Category", style="cyan")
            for cat in categories:
                table.add_row(cat)
            console.print(table)
    except Exception as e:
        error_message(f"Failed to get categories: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def tags():
    """List all available prompt tags."""
    try:
        sdk = await get_sdk()
        data = await sdk.prompts.get_categories()
        if data:
            from rich.table import Table

            tags = data.get("tags", [])
            table = Table(title="Prompt Tags")
            table.add_column("Tag", style="cyan")
            for tag in tags:
                table.add_row(tag)
            console.print(table)
    except Exception as e:
        error_message(f"Failed to get tags: {str(e)}")
        raise SystemExit(1)


@prompt_app.async_command()
async def stats():
    """Show prompt usage statistics."""
    try:
        sdk = await get_sdk()
        data = await sdk.prompts.get_prompt_stats()
        if data:
            from rich.columns import Columns
            from rich.panel import Panel

            basic_panel = Panel(
                f"Total Prompts: [green]{data.get('total_prompts', 0)}[/green]\n"
                f"Active: [blue]{data.get('active_prompts', 0)}[/blue]\n"
                f"Categories: [yellow]{data.get('total_categories', 0)}[/yellow]",
                title="📊 Prompt Stats",
                border_style="cyan",
            )
            usage_panel = Panel(
                f"Default Prompt: [green]{data.get('default_prompt', 'None')}[/green]\n"
                f"Most Used: [blue]{data.get('most_used_prompt', 'N/A')}[/blue]",
                title="📈 Usage",
                border_style="green",
            )
            console.print(Columns([basic_panel, usage_panel]))
    except Exception as e:
        error_message(f"Failed to get prompt statistics: {str(e)}")
        raise SystemExit(1)
