"""
User management commands for the API-based CLI.

This module provides all user management functionality through API calls,
duplicating the functionality of the original CLI but using REST endpoints.
"""

import asyncio
from typing import Optional

import typer
from rich.table import Table

from .base import (
    console, 
    error_message, 
    success_message, 
    info_message,
    get_client_with_auth,
    handle_api_response,
    display_table_data,
    confirm_action,
    format_timestamp
)

user_app = typer.Typer(help="👥 User management commands")


@user_app.command()
def create(
    username: str = typer.Argument(..., help="Username for the new user"),
    email: str = typer.Argument(..., help="Email address for the new user"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password (will prompt if not provided)"),
    full_name: Optional[str] = typer.Option(None, "--full-name", help="Full name of the user"),
    superuser: bool = typer.Option(False, "--superuser", help="Create as superuser"),
):
    """Create a new user account with comprehensive validation and setup."""
    
    async def _create_user():
        client = get_client_with_auth()
        
        # Prompt for password if not provided
        if not password:
            from rich.prompt import Prompt
            user_password = Prompt.ask("Password", password=True)
        else:
            user_password = password
        
        # Prepare user data
        user_data = {
            "username": username,
            "email": email,
            "password": user_password,
            "full_name": full_name,
            "is_superuser": superuser
        }
        
        try:
            # Create user via API
            response = await client.post("/api/v1/auth/register", data=user_data)
            user_data = handle_api_response(response, "user creation")
            
            if user_data:
                # Display user information
                table = Table(title="New User Created")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("ID", str(user_data.get("id", "")))
                table.add_row("Username", user_data.get("username", ""))
                table.add_row("Email", user_data.get("email", ""))
                table.add_row("Full Name", user_data.get("full_name", "") or "Not provided")
                table.add_row("Superuser", "Yes" if user_data.get("is_superuser") else "No")
                table.add_row("Active", "Yes" if user_data.get("is_active") else "No")
                table.add_row("Created", format_timestamp(user_data.get("created_at", "")))
                
                console.print(table)
                
                if superuser:
                    # Promote to superuser if requested
                    await client.post(f"/api/v1/admin/users/{user_data['id']}/promote")
                    success_message("User promoted to superuser successfully")
        
        except Exception as e:
            error_message(f"Failed to create user: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_create_user())


@user_app.command()
def list(
    active_only: bool = typer.Option(False, "--active-only", help="Show only active users"),
    search: Optional[str] = typer.Option(None, "--search", help="Search users by username or email"),
    limit: int = typer.Option(20, "--limit", help="Maximum number of users to show"),
    sort_by: str = typer.Option("created_at", "--sort-by", help="Sort field"),
):
    """List user accounts with filtering and search options."""
    
    async def _list_users():
        client = get_client_with_auth()
        
        # Build query parameters
        params = {
            "limit": limit,
            "sort_by": sort_by
        }
        
        if active_only:
            params["active_only"] = True
        
        if search:
            params["search"] = search
        
        try:
            response = await client.get("/api/v1/users/", params=params)
            data = handle_api_response(response, "listing users")
            
            if data and "items" in data:
                users = data["items"]
                
                if not users:
                    info_message("No users found matching the criteria")
                    return
                
                # Display users in table
                table = Table(title=f"Users ({len(users)} of {data.get('total', len(users))})")
                table.add_column("Username", style="cyan")
                table.add_column("Email", style="white")
                table.add_column("Full Name", style="blue")
                table.add_column("Superuser", style="yellow")
                table.add_column("Active", style="green")
                table.add_column("Created", style="dim")
                
                for user in users:
                    table.add_row(
                        user.get("username", ""),
                        user.get("email", ""),
                        user.get("full_name", "") or "—",
                        "Yes" if user.get("is_superuser") else "No",
                        "Yes" if user.get("is_active") else "No",
                        format_timestamp(user.get("created_at", ""))
                    )
                
                console.print(table)
                
                # Show pagination info if applicable
                if data.get("total", 0) > len(users):
                    info_message(f"Showing {len(users)} of {data['total']} total users")
        
        except Exception as e:
            error_message(f"Failed to list users: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_list_users())


@user_app.command()
def show(
    username: str = typer.Argument(..., help="Username to show details for"),
):
    """Show detailed information about a specific user."""
    
    async def _show_user():
        client = get_client_with_auth()
        
        try:
            # Get user by username (search first)
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Get detailed user info
            response = await client.get(f"/api/v1/users/{user_id}")
            user_data = handle_api_response(response, "getting user details")
            
            if user_data:
                # Display detailed user information
                table = Table(title=f"User Details: {username}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("ID", str(user_data.get("id", "")))
                table.add_row("Username", user_data.get("username", ""))
                table.add_row("Email", user_data.get("email", ""))
                table.add_row("Full Name", user_data.get("full_name", "") or "Not provided")
                table.add_row("Superuser", "Yes" if user_data.get("is_superuser") else "No")
                table.add_row("Active", "Yes" if user_data.get("is_active") else "No")
                table.add_row("Created", format_timestamp(user_data.get("created_at", "")))
                table.add_row("Last Updated", format_timestamp(user_data.get("updated_at", "")))
                table.add_row("Document Count", str(user_data.get("document_count", 0)))
                table.add_row("Conversation Count", str(user_data.get("conversation_count", 0)))
                table.add_row("Total Messages", str(user_data.get("total_messages", 0)))
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to show user details: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_user())


@user_app.command()
def delete(
    username: str = typer.Argument(..., help="Username to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Delete a user account and all associated data."""
    
    async def _delete_user():
        client = get_client_with_auth()
        
        try:
            # Find user first
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Confirm deletion
            if not force:
                if not confirm_action(f"Are you sure you want to delete user '{username}'? This action cannot be undone."):
                    info_message("User deletion cancelled")
                    return
            
            # Delete user
            response = await client.delete(f"/api/v1/users/{user_id}")
            handle_api_response(response, "user deletion")
        
        except Exception as e:
            error_message(f"Failed to delete user: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_delete_user())


@user_app.command("reset-password")
def reset_password(
    username: str = typer.Argument(..., help="Username whose password to reset"),
    new_password: Optional[str] = typer.Option(None, "--password", "-p", help="New password (will prompt if not provided)"),
):
    """Reset a user's password."""
    
    async def _reset_password():
        client = get_client_with_auth()
        
        # Get new password
        if not new_password:
            from rich.prompt import Prompt
            password = Prompt.ask("New password", password=True)
            confirm_password = Prompt.ask("Confirm password", password=True)
            
            if password != confirm_password:
                error_message("Passwords do not match")
                return
        else:
            password = new_password
        
        try:
            # Find user first
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Reset password
            response = await client.post(f"/api/v1/admin/users/{user_id}/reset-password", 
                                       params={"new_password": password})
            handle_api_response(response, "password reset")
        
        except Exception as e:
            error_message(f"Failed to reset password: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_reset_password())


@user_app.command()
def activate(
    username: str = typer.Argument(..., help="Username to activate"),
):
    """Activate a user account."""
    
    async def _activate_user():
        client = get_client_with_auth()
        
        try:
            # Find user first
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Activate user
            response = await client.post(f"/api/v1/admin/users/{user_id}/activate")
            handle_api_response(response, "user activation")
        
        except Exception as e:
            error_message(f"Failed to activate user: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_activate_user())


@user_app.command()
def deactivate(
    username: str = typer.Argument(..., help="Username to deactivate"),
):
    """Deactivate a user account."""
    
    async def _deactivate_user():
        client = get_client_with_auth()
        
        try:
            # Find user first
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Deactivate user
            response = await client.post(f"/api/v1/admin/users/{user_id}/deactivate")
            handle_api_response(response, "user deactivation")
        
        except Exception as e:
            error_message(f"Failed to deactivate user: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_deactivate_user())


@user_app.command()
def promote(
    username: str = typer.Argument(..., help="Username to promote to superuser"),
):
    """Promote a user to superuser status."""
    
    async def _promote_user():
        client = get_client_with_auth()
        
        try:
            # Find user first
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Promote user
            response = await client.post(f"/api/v1/admin/users/{user_id}/promote")
            handle_api_response(response, "user promotion")
        
        except Exception as e:
            error_message(f"Failed to promote user: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_promote_user())


@user_app.command()
def demote(
    username: str = typer.Argument(..., help="Username to demote from superuser"),
):
    """Demote a superuser to regular user status."""
    
    async def _demote_user():
        client = get_client_with_auth()
        
        try:
            # Find user first
            search_response = await client.get("/api/v1/users/", params={"search": username, "limit": 1})
            search_data = handle_api_response(search_response, "searching for user")
            
            if not search_data or not search_data.get("items"):
                error_message(f"User '{username}' not found")
                return
            
            user = search_data["items"][0]
            user_id = user["id"]
            
            # Demote user
            response = await client.post(f"/api/v1/admin/users/{user_id}/demote")
            handle_api_response(response, "user demotion")
        
        except Exception as e:
            error_message(f"Failed to demote user: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_demote_user())


@user_app.command()
def stats():
    """Display user statistics and summary."""
    
    async def _show_stats():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/admin/users/stats")
            data = handle_api_response(response, "getting user statistics")
            
            if data:
                # Display statistics
                from rich.panel import Panel
                from rich.columns import Columns
                
                # Basic stats
                basic_panel = Panel(
                    f"Total: [green]{data.get('total_users', 0)}[/green]\n"
                    f"Active: [blue]{data.get('active_users', 0)}[/blue]\n"
                    f"Inactive: [yellow]{data.get('inactive_users', 0)}[/yellow]\n"
                    f"Superusers: [red]{data.get('superusers', 0)}[/red]",
                    title="👥 User Counts",
                    border_style="cyan"
                )
                
                # Engagement stats
                engagement = data.get('engagement', {})
                engagement_panel = Panel(
                    f"With Documents: [green]{engagement.get('users_with_documents', 0)}[/green]\n"
                    f"With Conversations: [blue]{engagement.get('users_with_conversations', 0)}[/blue]\n"
                    f"Avg Docs/User: [yellow]{engagement.get('avg_documents_per_user', 0)}[/yellow]\n"
                    f"Avg Convs/User: [magenta]{engagement.get('avg_conversations_per_user', 0)}[/magenta]",
                    title="📊 Engagement",
                    border_style="green"
                )
                
                # Activity panel
                activity_panel = Panel(
                    f"Activity Rate: [green]{data.get('activity_rate', 0)}%[/green]\n"
                    f"Recent Registrations (30d): [blue]{data.get('recent_registrations_30d', 0)}[/blue]",
                    title="🎯 Activity",
                    border_style="yellow"
                )
                
                console.print(Columns([basic_panel, engagement_panel, activity_panel]))
                
                # Top users
                top_users = data.get('top_users_by_documents', [])
                if top_users:
                    table = Table(title="🏆 Top Users by Documents")
                    table.add_column("Username", style="cyan")
                    table.add_column("Documents", style="green")
                    
                    for user in top_users[:5]:
                        table.add_row(
                            user.get('username', ''),
                            str(user.get('document_count', 0))
                        )
                    
                    console.print(table)
        
        except Exception as e:
            error_message(f"Failed to get user statistics: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_stats())