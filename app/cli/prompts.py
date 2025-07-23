"""
Prompt management CLI commands.

This module provides comprehensive prompt management functionality
through the command line interface.
"""

import asyncio
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..services.prompt_service import PromptService
from .base import console, error_message, info_message, success_message

# Create the prompt management app
prompt_app = typer.Typer(help="📝 Prompt management commands", rich_markup_mode="rich")


@prompt_app.command("list")
def list_prompts(
    active_only: bool = typer.Option(
        True, "--active-only/--include-inactive", help="Show only active prompts"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Filter by category"
    ),
    search: Optional[str] = typer.Option(
        None, "--search", "-s", help="Search in name, title, content, and tags"
    ),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed information"
    ),
):
    """List all prompts."""

    async def _list_prompts():
        try:
            prompts = await PromptService.list_prompts(
                active_only=active_only, category=category, search=search
            )

            if not prompts:
                info_message("No prompts found")
                return

            if detailed:
                for prompt in prompts:
                    status_color = "green" if prompt.is_active else "yellow"
                    default_marker = " (DEFAULT)" if prompt.is_default else ""

                    panel_content = f"""
[bold]Title:[/bold] {prompt.title}
[bold]Category:[/bold] {prompt.category or 'None'}
[bold]Tags:[/bold] {', '.join(prompt.tag_list) if prompt.tag_list else 'None'}
[bold]Active:[/bold] [{status_color}]{prompt.is_active}[/{status_color}]
[bold]Default:[/bold] {'Yes' if prompt.is_default else 'No'}
[bold]Usage Count:[/bold] {prompt.usage_count}
[bold]Last Used:[/bold] {prompt.last_used_at or 'Never'}
[bold]Description:[/bold] {prompt.description or 'No description'}

[bold]Content:[/bold]
{prompt.content[:200]}{"..." if len(prompt.content) > 200 else ""}
"""

                    console.print(
                        Panel(
                            panel_content.strip(),
                            title=f"📝 {prompt.name}{default_marker}",
                            border_style=status_color,
                        )
                    )
                    console.print()
            else:
                table = Table(title="Prompts", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Title")
                table.add_column("Category")
                table.add_column("Status")
                table.add_column("Usage")
                table.add_column("Last Used")

                for prompt in prompts:
                    status = "🟢 Active" if prompt.is_active else "🟡 Inactive"
                    if prompt.is_default:
                        status += " (DEFAULT)"

                    last_used = (
                        prompt.last_used_at.strftime("%Y-%m-%d")
                        if prompt.last_used_at
                        else "Never"
                    )

                    table.add_row(
                        prompt.name,
                        prompt.title,
                        prompt.category or "",
                        status,
                        str(prompt.usage_count),
                        last_used,
                    )

                console.print(table)

        except Exception as e:
            error_message(f"Failed to list prompts: {e}")

    asyncio.run(_list_prompts())


@prompt_app.command("show")
def show_prompt(name: str = typer.Argument(..., help="Prompt name")):
    """Show detailed information about a specific prompt."""

    async def _show_prompt():
        try:
            prompt = await PromptService.get_prompt(name)
            if not prompt:
                error_message(f"Prompt not found: {name}")
                return

            status_color = "green" if prompt.is_active else "yellow"
            default_marker = " (DEFAULT)" if prompt.is_default else ""

            panel_content = f"""
[bold]Name:[/bold] {prompt.name}
[bold]Title:[/bold] {prompt.title}
[bold]Category:[/bold] {prompt.category or 'None'}
[bold]Tags:[/bold] {', '.join(prompt.tag_list) if prompt.tag_list else 'None'}
[bold]Active:[/bold] [{status_color}]{prompt.is_active}[/{status_color}]
[bold]Default:[/bold] {'Yes' if prompt.is_default else 'No'}
[bold]Usage Count:[/bold] {prompt.usage_count}
[bold]Last Used:[/bold] {prompt.last_used_at or 'Never'}
[bold]Created:[/bold] {prompt.created_at}
[bold]Updated:[/bold] {prompt.updated_at}
[bold]Description:[/bold] {prompt.description or 'No description'}

[bold]Content:[/bold]
{prompt.content}
"""

            console.print(
                Panel(
                    panel_content.strip(),
                    title=f"📝 {prompt.name}{default_marker}",
                    border_style=status_color,
                )
            )

        except Exception as e:
            error_message(f"Failed to show prompt: {e}")

    asyncio.run(_show_prompt())


@prompt_app.command("add")
def add_prompt(
    name: str = typer.Argument(..., help="Prompt name/identifier"),
    title: str = typer.Option(..., "--title", "-t", help="Prompt title"),
    content: str = typer.Option(..., "--content", "-c", help="Prompt content"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Prompt description"
    ),
    category: Optional[str] = typer.Option(None, "--category", help="Prompt category"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    set_default: bool = typer.Option(False, "--default", help="Set as default prompt"),
    inactive: bool = typer.Option(
        False, "--inactive", help="Create prompt in inactive state"
    ),
):
    """Add a new prompt."""

    async def _add_prompt():
        try:
            tag_list = []
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

            prompt = await PromptService.create_prompt(
                name=name,
                title=title,
                content=content,
                description=description,
                is_default=set_default,
                category=category,
                tags=tag_list,
            )

            # Set active status
            if inactive:
                await PromptService.deactivate_prompt(name)

            success_message(f"Added prompt: {prompt.name}")

        except Exception as e:
            error_message(f"Failed to add prompt: {e}")

    asyncio.run(_add_prompt())


@prompt_app.command("update")
def update_prompt(
    name: str = typer.Argument(..., help="Prompt name"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="New content"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description"
    ),
    category: Optional[str] = typer.Option(None, "--category", help="New category"),
    tags: Optional[str] = typer.Option(None, "--tags", help="New comma-separated tags"),
    clear_category: bool = typer.Option(
        False, "--clear-category", help="Clear category"
    ),
    clear_tags: bool = typer.Option(False, "--clear-tags", help="Clear tags"),
):
    """Update an existing prompt."""

    async def _update_prompt():
        try:
            updates = {}

            if title is not None:
                updates["title"] = title
            if content is not None:
                updates["content"] = content
            if description is not None:
                updates["description"] = description
            if category is not None:
                updates["category"] = category
            if clear_category:
                updates["category"] = None
            if tags is not None:
                updates["tags"] = [
                    tag.strip() for tag in tags.split(",") if tag.strip()
                ]
            if clear_tags:
                updates["tags"] = []

            if not updates:
                error_message("No updates specified")
                return

            prompt = await PromptService.update_prompt(name, **updates)
            if prompt:
                success_message(f"Updated prompt: {name}")
            else:
                error_message(f"Prompt not found: {name}")

        except Exception as e:
            error_message(f"Failed to update prompt: {e}")

    asyncio.run(_update_prompt())


@prompt_app.command("remove")
def remove_prompt(
    name: str = typer.Argument(..., help="Prompt name"),
    confirm: bool = typer.Option(
        False, "--confirm", "-y", help="Skip confirmation prompt"
    ),
):
    """Remove a prompt."""

    async def _remove_prompt():
        try:
            if not confirm:
                confirmed = typer.confirm(
                    f"Are you sure you want to remove prompt '{name}'?"
                )
                if not confirmed:
                    info_message("Operation cancelled")
                    return

            success = await PromptService.delete_prompt(name)
            if success:
                success_message(f"Removed prompt: {name}")
            else:
                error_message(f"Prompt not found: {name}")

        except Exception as e:
            error_message(f"Failed to remove prompt: {e}")

    asyncio.run(_remove_prompt())


@prompt_app.command("set-default")
def set_default_prompt(name: str = typer.Argument(..., help="Prompt name")):
    """Set a prompt as the default."""

    async def _set_default():
        try:
            success = await PromptService.set_default_prompt(name)
            if success:
                success_message(f"Set default prompt: {name}")
            else:
                error_message(f"Prompt not found: {name}")

        except Exception as e:
            error_message(f"Failed to set default prompt: {e}")

    asyncio.run(_set_default())


@prompt_app.command("activate")
def activate_prompt(name: str = typer.Argument(..., help="Prompt name")):
    """Activate a prompt."""

    async def _activate():
        try:
            success = await PromptService.activate_prompt(name)
            if success:
                success_message(f"Activated prompt: {name}")
            else:
                error_message(f"Prompt not found: {name}")

        except Exception as e:
            error_message(f"Failed to activate prompt: {e}")

    asyncio.run(_activate())


@prompt_app.command("deactivate")
def deactivate_prompt(name: str = typer.Argument(..., help="Prompt name")):
    """Deactivate a prompt."""

    async def _deactivate():
        try:
            success = await PromptService.deactivate_prompt(name)
            if success:
                success_message(f"Deactivated prompt: {name}")
            else:
                error_message(f"Prompt not found: {name}")

        except Exception as e:
            error_message(f"Failed to deactivate prompt: {e}")

    asyncio.run(_deactivate())


@prompt_app.command("categories")
def list_categories():
    """List all available prompt categories."""

    async def _list_categories():
        try:
            categories = await PromptService.get_categories()

            if not categories:
                info_message("No categories found")
                return

            console.print("Available Categories:")
            for category in categories:
                console.print(f"  • {category}")

        except Exception as e:
            error_message(f"Failed to list categories: {e}")

    asyncio.run(_list_categories())


@prompt_app.command("tags")
def list_tags():
    """List all available prompt tags."""

    async def _list_tags():
        try:
            tags = await PromptService.get_all_tags()

            if not tags:
                info_message("No tags found")
                return

            console.print("Available Tags:")
            for tag in tags:
                console.print(f"  • {tag}")

        except Exception as e:
            error_message(f"Failed to list tags: {e}")

    asyncio.run(_list_tags())


@prompt_app.command("stats")
def show_stats():
    """Show prompt usage statistics."""

    async def _show_stats():
        try:
            stats = await PromptService.get_prompt_stats()

            # Overview panel
            overview_content = f"""
[bold]Total Prompts:[/bold] {stats['total_prompts']}
[bold]Active Prompts:[/bold] {stats['active_prompts']}
[bold]Inactive Prompts:[/bold] {stats['inactive_prompts']}
[bold]Default Prompt:[/bold] {stats['default_prompt'] or 'None set'}
[bold]Categories:[/bold] {len(stats['categories'])}
[bold]Total Tags:[/bold] {stats['total_tags']}
"""

            console.print(
                Panel(
                    overview_content.strip(),
                    title="📊 Prompt Statistics",
                    border_style="blue",
                )
            )

            # Most used prompts
            if stats["most_used"]:
                table = Table(title="Most Used Prompts", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Title")
                table.add_column("Usage Count")
                table.add_column("Last Used")

                for prompt in stats["most_used"]:
                    last_used = (
                        prompt["last_used_at"].strftime("%Y-%m-%d")
                        if prompt["last_used_at"]
                        else "Never"
                    )
                    table.add_row(
                        prompt["name"],
                        prompt["title"],
                        str(prompt["usage_count"]),
                        last_used,
                    )

                console.print(table)

            # Recently used prompts
            if stats["recently_used"]:
                table = Table(title="Recently Used Prompts", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Title")
                table.add_column("Usage Count")
                table.add_column("Last Used")

                for prompt in stats["recently_used"]:
                    last_used = (
                        prompt["last_used_at"].strftime("%Y-%m-%d %H:%M")
                        if prompt["last_used_at"]
                        else "Never"
                    )
                    table.add_row(
                        prompt["name"],
                        prompt["title"],
                        str(prompt["usage_count"]),
                        last_used,
                    )

                console.print(table)

        except Exception as e:
            error_message(f"Failed to get statistics: {e}")

    asyncio.run(_show_stats())
