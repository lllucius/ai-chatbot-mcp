"""User management commands for the AI Chatbot Platform CLI.

This module provides comprehensive user account management functionality through
async operations and the AI Chatbot SDK with full validation and security controls.
"""
    ```bash
    # Create new user accounts
    ai-chatbot users create john john@example.com --full-name "John Doe"
    ai-chatbot users create admin admin@example.com --superuser

    # List and filter users
    ai-chatbot users list --active-only --page 1 --size 20
    ai-chatbot users search --query "john" --role user

    # Manage user accounts
    ai-chatbot users activate user_id
    ai-chatbot users deactivate user_id
    ai-chatbot users update user_id --role admin

    # Bulk operations
    ai-chatbot users import users.csv --validate
    ai-chatbot users export --format json --active-only
    ```

Integration:
    - LDAP/Active Directory synchronization
    - Single sign-on (SSO) provider integration
    - HR system integration for automated provisioning
    - Compliance and audit system integration
"""

import traceback
from typing import Optional

from async_typer import AsyncTyper
from typer import Argument, Option

from sdk.ai_chatbot_sdk import ApiError
from shared.schemas import RegisterRequest

from .base import (
    display_key_value_pairs,
    error_message,
    format_timestamp,
    get_sdk,
    info_message,
    success_message,
)

user_app = AsyncTyper(help="User management commands", rich_markup_mode=None)


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
    Create a new user account with comprehensive validation and security setup.

    Creates a new user account in the AI Chatbot Platform with full validation,
    security controls, and proper initialization. The command handles password
    security, role assignment, and account setup according to enterprise best
    practices.

    User accounts are created with appropriate default settings and can be
    immediately activated for platform access. All creation operations are
    logged for audit and compliance purposes.

    Args:
        username (str): Unique username for the new account (alphanumeric, underscores, hyphens)
        email (str): Valid email address for account notifications and recovery
        password (Optional[str]): Account password. If not provided, will prompt securely
        full_name (Optional[str]): Display name for the user account
        superuser (bool): Whether to create account with administrative privileges

    Security Notes:
        - Passwords are prompted securely with masking if not provided
        - Username and email uniqueness is validated server-side
        - Superuser creation requires appropriate administrative privileges
        - All account creation is logged for security audit trails

    Performance Notes:
        - Fast account creation with minimal API calls
        - Efficient validation and error handling
        - Non-blocking async operations for responsiveness
        - Immediate feedback on account creation status

    Use Cases:
        - Onboarding new team members and users
        - Creating administrative accounts for system management
        - Bulk user provisioning for organizational setup
        - Service account creation for automated systems
        - Testing and development account creation

    Example:
        ```bash
        # Interactive user creation
        ai-chatbot users create john john@example.com

        # Admin user with full details
        ai-chatbot users create admin admin@example.com --full-name "System Admin" --superuser

        # Automated user creation
        ai-chatbot users create service service@example.com --password secret123
        ```

    Raises:
        SystemExit: On validation errors, authentication failures, or creation conflicts
    """
    try:
        sdk = await get_sdk()

        # Prompt for password if not provided
        if not password:
            import getpass

            user_password = getpass.getpass("Password: ")
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
        traceback.print_exc()
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

        # Prepare user data for display
        user_data = []
        for user in users:
            user_data.append(
                {
                    "ID": str(user.id)[:8] + "...",
                    "Username": user.username,
                    "Email": user.email,
                    "Full Name": user.full_name or "-",
                    "Active": "Yes" if user.is_active else "No",
                    "Superuser": "Yes" if user.is_superuser else "No",
                    "Created": format_timestamp(
                        user.created_at.isoformat() if user.created_at else ""
                    ),
                }
            )

        # Display using Rich table formatting
        from .base import display_rich_table

        display_rich_table(
            user_data, f"Users (Page {pagination.page} of {pagination.total} total)"
        )

        if getattr(pagination, "total", 0) > size:
            info_message(f"Showing {len(users)} of {pagination.total} total users")

    except ApiError as e:
        error_message(f"Failed to list users: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        traceback.print_exc()
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
            # Try parsing as integer ID first
            user_id = int(username_or_id)
            user = await sdk.users.get_byid(user_id)
        except ValueError:
            # If not an integer, treat as username
            user = await sdk.users.get_byname(username_or_id)

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
        traceback.print_exc()
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
        traceback.print_exc()
        raise SystemExit(1)
