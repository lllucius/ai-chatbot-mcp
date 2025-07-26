"""
User management commands for the API-based CLI.

This module provides all user management functionality through the SDK,
duplicating the functionality of the original CLI but using the SDK client.
"""

from typing import Optional
from uuid import UUID

import typer
from rich.table import Table

from client.ai_chatbot_sdk import RegisterRequest, UserUpdate, ApiError
from .base import (
    console, 
    error_message, 
    success_message, 
    info_message,
    get_sdk_with_auth,
    display_key_value_pairs,
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
    
    try:
        sdk = get_sdk_with_auth()
        
        # Prompt for password if not provided
        if not password:
            from rich.prompt import Prompt
            user_password = Prompt.ask("Password", password=True)
        else:
            user_password = password
        
        # Create user registration request
        register_data = RegisterRequest(
            username=username,
            email=email,
            password=user_password,
            full_name=full_name
        )
        
        # Register the user
        user = sdk.auth.register(register_data)
        
        success_message(f"User '{username}' created successfully")
        
        # Display user info
        user_info = {
            "ID": str(user.id),
            "Username": user.username,
            "Email": user.email,
            "Full Name": user.full_name or "Not specified",
            "Active": "Yes" if user.is_active else "No",
            "Superuser": "Yes" if user.is_superuser else "No",
            "Created": format_timestamp(user.created_at.isoformat() if user.created_at else "")
        }
        
        display_key_value_pairs(user_info, "User Created")
        
        # Promote to superuser if requested
        if superuser and not user.is_superuser:
            try:
                promote_result = sdk.admin.promote_user(user.id)
                if promote_result.success:
                    success_message(f"User '{username}' promoted to superuser")
                else:
                    error_message(f"Failed to promote user to superuser: {promote_result.message}")
            except ApiError as e:
                error_message(f"Failed to promote user to superuser: {str(e)}")
                
    except ApiError as e:
        error_message(f"Failed to create user: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@user_app.command()
def list(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(20, "--size", "-s", help="Items per page"),
    active_only: bool = typer.Option(False, "--active-only", help="Show only active users"),
    superuser_only: bool = typer.Option(False, "--superuser-only", help="Show only superusers"),
    search: Optional[str] = typer.Option(None, "--search", help="Search users by username or email"),
):
    """List all users with comprehensive filtering and detailed display."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Get users using SDK
        users_response = sdk.users.list(
            page=page, 
            size=size,
            active_only=active_only if active_only else None,
            superuser_only=superuser_only if superuser_only else None
        )
        
        if not users_response.success:
            error_message("Failed to retrieve users")
            return
            
        users = users_response.items
        pagination = users_response.pagination
        
        # Filter by search if provided
        if search:
            users = [u for u in users if search.lower() in u.username.lower() or search.lower() in u.email.lower()]
        
        if not users:
            info_message("No users found matching the criteria")
            return
        
        # Create and display table
        table = Table(title=f"Users (Page {pagination.page} of {pagination.total} total)")
        
        table.add_column("ID", style="dim")
        table.add_column("Username", style="cyan")
        table.add_column("Email", style="blue")
        table.add_column("Full Name", style="green")
        table.add_column("Active", style="yellow")
        table.add_column("Superuser", style="red")
        table.add_column("Created", style="magenta")
        
        for user in users:
            table.add_row(
                str(user.id)[:8] + "...",
                user.username,
                user.email,
                user.full_name or "-",
                "✓" if user.is_active else "✗",
                "✓" if user.is_superuser else "✗",
                format_timestamp(user.created_at.isoformat() if user.created_at else "")
            )
        
        console.print(table)
        
        # Show pagination info
        if pagination.total > size:
            info_message(f"Showing {len(users)} of {pagination.total} total users")
            
    except ApiError as e:
        error_message(f"Failed to list users: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@user_app.command()
def show(
    username_or_id: str = typer.Argument(..., help="Username or user ID to display"),
):
    """Display detailed information about a specific user."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Try to parse as UUID first, then treat as username
        try:
            user_id = UUID(username_or_id)
            user = sdk.users.get(user_id)
        except ValueError:
            # Not a UUID, search by username
            users_response = sdk.users.list(page=1, size=100)
            matching_users = [u for u in users_response.items if u.username == username_or_id]
            
            if not matching_users:
                error_message(f"User '{username_or_id}' not found")
                return
            
            user = matching_users[0]
        
        # Display user information
        user_info = {
            "ID": str(user.id),
            "Username": user.username,
            "Email": user.email,
            "Full Name": user.full_name or "Not specified",
            "Active": "Yes" if user.is_active else "No",
            "Superuser": "Yes" if user.is_superuser else "No",
            "Created": format_timestamp(user.created_at.isoformat() if user.created_at else "")
        }
        
        display_key_value_pairs(user_info, f"User Details: {user.username}")
        
    except ApiError as e:
        error_message(f"Failed to get user: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@user_app.command()
def update(
    username_or_id: str = typer.Argument(..., help="Username or user ID to update"),
    email: Optional[str] = typer.Option(None, "--email", help="New email address"),
    full_name: Optional[str] = typer.Option(None, "--full-name", help="New full name"),
    activate: bool = typer.Option(False, "--activate", help="Activate the user"),
    deactivate: bool = typer.Option(False, "--deactivate", help="Deactivate the user"),
):
    """Update user profile information."""
    
    if activate and deactivate:
        error_message("Cannot activate and deactivate at the same time")
        return
    
    try:
        sdk = get_sdk_with_auth()
        
        # Find the user
        try:
            user_id = UUID(username_or_id)
            user = sdk.users.get(user_id)
        except ValueError:
            users_response = sdk.users.list(page=1, size=100)
            matching_users = [u for u in users_response.items if u.username == username_or_id]
            
            if not matching_users:
                error_message(f"User '{username_or_id}' not found")
                return
            
            user = matching_users[0]
            user_id = user.id
        
        # Prepare update data
        update_data = UserUpdate()
        
        if email:
            update_data.email = email
            
        if full_name:
            update_data.full_name = full_name
            
        if activate:
            update_data.is_active = True
        elif deactivate:
            update_data.is_active = False
        
        # Update user
        updated_user = sdk.users.update(user_id, update_data)
        
        success_message(f"User '{user.username}' updated successfully")
        
        # Display updated info
        user_info = {
            "ID": str(updated_user.id),
            "Username": updated_user.username,
            "Email": updated_user.email,
            "Full Name": updated_user.full_name or "Not specified",
            "Active": "Yes" if updated_user.is_active else "No",
            "Superuser": "Yes" if updated_user.is_superuser else "No"
        }
        
        display_key_value_pairs(user_info, "Updated User")
        
    except ApiError as e:
        error_message(f"Failed to update user: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@user_app.command("reset-password")
def reset_password(
    username_or_id: str = typer.Argument(..., help="Username or user ID"),
    new_password: Optional[str] = typer.Option(None, "--password", help="New password (will prompt if not provided)"),
):
    """Reset a user's password."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Find the user
        try:
            user_id = UUID(username_or_id)
            user = sdk.users.get(user_id)
        except ValueError:
            users_response = sdk.users.list(page=1, size=100)
            matching_users = [u for u in users_response.items if u.username == username_or_id]
            
            if not matching_users:
                error_message(f"User '{username_or_id}' not found")
                return
            
            user = matching_users[0]
            user_id = user.id
        
        # Get password if not provided
        if not new_password:
            from rich.prompt import Prompt
            new_password = Prompt.ask("New password", password=True)
        
        # Reset password using admin endpoint
        result = sdk.admin.reset_user_password(user_id, new_password)
        
        if result.success:
            success_message(f"Password reset for user '{user.username}'")
        else:
            error_message(f"Failed to reset password: {result.message}")
            
    except ApiError as e:
        error_message(f"Failed to reset password: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@user_app.command()
def delete(
    username_or_id: str = typer.Argument(..., help="Username or user ID to delete"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Delete a user account."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Find the user
        try:
            user_id = UUID(username_or_id)
            user = sdk.users.get(user_id)
        except ValueError:
            users_response = sdk.users.list(page=1, size=100)
            matching_users = [u for u in users_response.items if u.username == username_or_id]
            
            if not matching_users:
                error_message(f"User '{username_or_id}' not found")
                return
            
            user = matching_users[0]
            user_id = user.id
        
        # Confirm deletion
        if not confirm:
            if not confirm_action(f"Delete user '{user.username}'? This action cannot be undone."):
                info_message("Deletion cancelled")
                return
        
        # Delete user
        result = sdk.users.delete(user_id)
        
        if result.success:
            success_message(f"User '{user.username}' deleted successfully")
        else:
            error_message(f"Failed to delete user: {result.message}")
            
    except ApiError as e:
        error_message(f"Failed to delete user: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@user_app.command()
def stats():
    """Display user statistics and analytics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Get user statistics from admin endpoint
        stats = sdk.admin.get_user_stats()
        
        # Display statistics
        stats_info = {
            "Total Users": stats.get("total_users", 0),
            "Active Users": stats.get("active_users", 0),
            "Inactive Users": stats.get("total_users", 0) - stats.get("active_users", 0),
            "Superusers": stats.get("superusers", 0),
            "New Users Today": stats.get("new_users_today", 0),
            "New Users This Week": stats.get("new_users_week", 0),
            "New Users This Month": stats.get("new_users_month", 0)
        }
        
        display_key_value_pairs(stats_info, "User Statistics")
        
    except ApiError as e:
        error_message(f"Failed to get user statistics: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
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