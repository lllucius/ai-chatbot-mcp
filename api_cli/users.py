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