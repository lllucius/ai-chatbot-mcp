"""
Async user management commands for the API-based CLI.

This module provides all user management functionality through the async SDK,
duplicating the functionality of the original CLI but using the async SDK client.
"""

from typing import Optional
from uuid import UUID

from async_typer import AsyncTyper
from rich.prompt import Prompt
from rich.table import Table
from typer import Argument, Option

from client.ai_chatbot_sdk import ApiError, RegisterRequest

from .base import (
    console,
    display_key_value_pairs,
    error_message,
    format_timestamp,
    get_sdk,
    info_message,
    success_message,
)

user_app = AsyncTyper(help="👥 User management commands")


@user_app.async_command()
async def create(
    username: str = Argument(..., help="Username for the new user"),
    email: str = Argument(..., help="Email address for the new user"),
    password: Optional[str] = Option(
        None, "--password", "-p", help="Password (will prompt if not provided)"
    ),
    full_name: Optional[str] = Option(
        None, "--full-name", help="Full name of the user"
    ),
    superuser: bool = Option(False, "--superuser", help="Create as superuser"),
):
    """
    Create a new user account with comprehensive validation and setup.
    """
    try:
        sdk = await get_sdk()

        # Prompt for password if not provided
        if not password:
            user_password = Prompt.ask("Password", password=True)
        else:
            user_password = password

        register_data = RegisterRequest(
            username=username, email=email, password=user_password, full_name=full_name
        )

        user = await sdk.auth.register(register_data)

        success_message(f"User '{username}' created successfully")

        user_info = {
            "ID": str(user.id),
            "Username": user.username,
            "Email": user.email,
            "Full Name": user.full_name or "Not set",
            "Active": "Yes" if user.is_active else "No",
            "Superuser": "Yes" if user.is_superuser else "No",
            "Created": (
                format_timestamp(user.created_at.isoformat())
                if user.created_at
                else "Unknown"
            ),
        }
        display_key_value_pairs(user_info, "User Details")

        # Promote to superuser if requested and not already superuser
        if superuser and not user.is_superuser:
            try:
                promote_result = await sdk.admin.promote_user(user.id)
                if getattr(promote_result, "success", False):
                    success_message(f"User '{username}' promoted to superuser")
                else:
                    error_message(
                        f"Failed to promote user to superuser: {getattr(promote_result, 'message', '')}"
                    )
            except ApiError as e:
                error_message(f"Failed to promote user to superuser: {str(e)}")

    except ApiError as e:
        error_message(f"Failed to create user: {e}")
        raise SystemExit(1)
    except Exception as e:
        error_message(f"Unexpected error: {e}")
        raise SystemExit(1)


@user_app.async_command()
async def list(
    page: int = Option(1, "--page", "-p", help="Page number"),
    size: int = Option(20, "--size", "-s", help="Items per page"),
    active_only: bool = Option(False, "--active-only", help="Show only active users"),
    superuser_only: bool = Option(
        False, "--superuser-only", help="Show only superusers"
    ),
    search: Optional[str] = Option(
        None, "--search", help="Search users by username or email"
    ),
):
    """List all users with comprehensive filtering and detailed display."""
    try:
        sdk = await get_sdk()
        users_response = await sdk.users.list(
            page=page,
            size=size,
            active_only=active_only if active_only else None,
            superuser_only=superuser_only if superuser_only else None,
        )
        users = users_response.items
        pagination = users_response.pagination

        # Filter by search if provided
        if search:
            users = [
                u
                for u in users
                if search.lower() in u.username.lower()
                or search.lower() in u.email.lower()
            ]

        if not users:
            info_message("No users found matching the criteria")
            return

        table = Table(
            title=f"Users (Page {pagination.page} of {pagination.total} total)"
        )
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
                format_timestamp(
                    user.created_at.isoformat() if user.created_at else ""
                ),
            )

        console.print(table)
        if getattr(pagination, "total", 0) > size:
            info_message(f"Showing {len(users)} of {pagination.total} total users")

    except ApiError as e:
        error_message(f"Failed to list users: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise SystemExit(1)


@user_app.async_command()
async def show(
    username_or_id: str = Argument(..., help="Username or user ID to display"),
):
    """Display detailed information about a specific user."""
    try:
        sdk = await get_sdk()
        user = None
        try:
            user_id = UUID(username_or_id)
            user = await sdk.users.get(user_id)
        except ValueError:
            users_response = await sdk.users.list(page=1, size=100)
            matching_users = [
                u for u in users_response.items if u.username == username_or_id
            ]
            if not matching_users:
                error_message(f"User '{username_or_id}' not found")
                return
            user = matching_users[0]

        user_info = {
            "ID": str(user.id),
            "Username": user.username,
            "Email": user.email,
            "Full Name": user.full_name or "Not specified",
            "Active": "Yes" if user.is_active else "No",
            "Superuser": "Yes" if user.is_superuser else "No",
            "Created": format_timestamp(
                user.created_at.isoformat() if user.created_at else ""
            ),
        }

        display_key_value_pairs(user_info, f"User Details: {user.username}")

    except ApiError as e:
        error_message(f"Failed to get user: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise SystemExit(1)


@user_app.async_command()
async def stats():
    """Display user statistics and analytics."""
    try:
        sdk = await get_sdk()
        stats = await sdk.admin.get_user_stats()

        stats_info = {
            "Total Users": stats.get("total_users", 0),
            "Active Users": stats.get("active_users", 0),
            "Inactive Users": stats.get("total_users", 0)
            - stats.get("active_users", 0),
            "Superusers": stats.get("superusers", 0),
            "New Users Today": stats.get("new_users_today", 0),
            "New Users This Week": stats.get("new_users_week", 0),
            "New Users This Month": stats.get("new_users_month", 0),
        }

        display_key_value_pairs(stats_info, "User Statistics")

    except ApiError as e:
        error_message(f"Failed to get user statistics: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise SystemExit(1)
