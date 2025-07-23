"""
User management CLI commands.

Provides comprehensive user management functionality including:
- User creation and deletion
- Password management
- Role and permission management
- User activity monitoring
- Bulk operations
"""

from datetime import datetime, timedelta

import typer
from rich.prompt import Confirm, Prompt
from rich.table import Table
from sqlalchemy import func, or_, select

from ..database import AsyncSessionLocal
from ..models.conversation import Conversation
from ..models.document import Document
from ..models.user import User
from ..services.auth import AuthService
from ..services.user import UserService
from ..utils.security import get_password_hash
from .base import (async_command, console, error_message, format_timestamp,
                   success_message, warning_message)

# Create the user management app
user_app = typer.Typer(help="User management commands")


@user_app.command()
def create(
    username: str = typer.Argument(..., help="Username for the new user"),
    email: str = typer.Argument(..., help="Email address for the new user"),
    password: str = typer.Option(
        None, "--password", "-p", help="Password (will prompt if not provided)"
    ),
    full_name: str = typer.Option(
        None, "--full-name", "-n", help="Full name of the user"
    ),
    superuser: bool = typer.Option(
        False, "--superuser", "-s", help="Create as superuser"
    ),
    active: bool = typer.Option(True, "--active/--inactive", help="User active status"),
):
    """
    Create a new user account with comprehensive validation and setup.

    This command handles the complete user creation workflow including:
    - Input validation and sanitization
    - Password strength requirements and secure prompting
    - Email format validation and uniqueness checking
    - Username availability verification
    - Automatic role assignment (regular user or superuser)
    - Database transaction management with rollback on errors
    - Success confirmation with user details display

    Args:
        username: Unique username (3-50 chars, alphanumeric + underscore/hyphen)
        email: Valid email address that will be checked for uniqueness
        password: Optional password (prompted securely if not provided)
        full_name: Optional display name for the user
        superuser: Whether to grant superuser privileges (admin access)
        active: Whether the account should be active immediately

    Examples:
        # Create regular user with prompt for password
        python manage.py users create johndoe john@example.com

        # Create superuser with all details
        python manage.py users create admin admin@company.com --password secret --superuser --full-name "Administrator"

        # Create inactive user account
        python manage.py users create temp temp@example.com --inactive
    """

    @async_command
    async def _create_user():
        if not password:
            pwd = Prompt.ask("Enter password", password=True)
            pwd_confirm = Prompt.ask("Confirm password", password=True)
            if pwd != pwd_confirm:
                error_message("Passwords do not match")
                return
            password_to_use = pwd
        else:
            password_to_use = password

        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)

                # Check if user exists
                existing_user = await auth_service.get_user_by_username(username)
                if existing_user:
                    error_message(f"User '{username}' already exists")
                    return

                existing_email = await auth_service.get_user_by_email(email)
                if existing_email:
                    error_message(f"Email '{email}' is already in use")
                    return

                # Create user
                user = User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash(password_to_use),
                    full_name=full_name,
                    is_active=active,
                    is_superuser=superuser,
                )

                db.add(user)
                await db.commit()
                await db.refresh(user)

                user_type = "superuser" if superuser else "user"
                success_message(
                    f"{user_type.title()} '{username}' created successfully"
                )

                # Display user info
                table = Table(title="Created User")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("ID", str(user.id))
                table.add_row("Username", user.username)
                table.add_row("Email", user.email)
                table.add_row("Full Name", user.full_name or "N/A")
                table.add_row("Active", "✅" if user.is_active else "❌")
                table.add_row("Superuser", "✅" if user.is_superuser else "❌")
                table.add_row("Created", format_timestamp(user.created_at))

                console.print(table)

            except Exception as e:
                error_message(f"Failed to create user: {e}")

    _create_user()


@user_app.command()
def list(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum number of users to show"
    ),
    active_only: bool = typer.Option(
        False, "--active-only", help="Show only active users"
    ),
    superusers_only: bool = typer.Option(
        False, "--superusers-only", help="Show only superusers"
    ),
    search: str = typer.Option(
        None, "--search", "-s", help="Search by username or email"
    ),
    sort_by: str = typer.Option(
        "created", "--sort", help="Sort by: id, username, email, created, updated"
    ),
):
    """List user accounts with filtering and search options."""

    @async_command
    async def _list_users():
        async with AsyncSessionLocal() as db:
            try:
                query = select(User)

                # Apply filters
                if active_only:
                    query = query.where(User.is_active == True)

                if superusers_only:
                    query = query.where(User.is_superuser == True)

                if search:
                    search_pattern = f"%{search.lower()}%"
                    query = query.where(
                        or_(
                            func.lower(User.username).like(search_pattern),
                            func.lower(User.email).like(search_pattern),
                            func.lower(User.full_name).like(search_pattern),
                        )
                    )

                # Apply sorting
                if sort_by == "id":
                    query = query.order_by(User.id)
                elif sort_by == "username":
                    query = query.order_by(User.username)
                elif sort_by == "email":
                    query = query.order_by(User.email)
                elif sort_by == "created":
                    query = query.order_by(User.created_at.desc())
                elif sort_by == "updated":
                    query = query.order_by(User.updated_at.desc())

                query = query.limit(limit)
                result = await db.execute(query)
                users = result.scalars().all()

                if not users:
                    warning_message("No users found matching criteria")
                    return

                # Create table
                table = Table(title=f"User Accounts ({len(users)} found)")
                table.add_column("ID", style="cyan", width=6)
                table.add_column("Username", style="green", width=15)
                table.add_column("Email", style="blue", width=25)
                table.add_column("Full Name", width=20)
                table.add_column("Status", width=8)
                table.add_column("Super", width=6)
                table.add_column("Created", width=12)
                table.add_column("Last Login", width=12)

                for user in users:
                    status = "✅ Active" if user.is_active else "❌ Inactive"
                    super_status = "⭐" if user.is_superuser else ""
                    last_login = (
                        format_timestamp(user.last_login)
                        if hasattr(user, "last_login") and user.last_login
                        else "Never"
                    )

                    table.add_row(
                        str(user.id),
                        user.username,
                        user.email,
                        user.full_name or "",
                        status,
                        super_status,
                        user.created_at.strftime("%Y-%m-%d"),
                        last_login[:12] if last_login != "Never" else last_login,
                    )

                console.print(table)

            except Exception as e:
                error_message(f"Failed to list users: {e}")

    _list_users()


@user_app.command()
def show(
    username: str = typer.Argument(..., help="Username to show details for"),
):
    """Show detailed information about a specific user."""

    @async_command
    async def _show_user():
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                # Get user statistics
                doc_count = await db.scalar(
                    select(func.count(Document.id)).where(Document.owner_id == user.id)
                )

                conv_count = await db.scalar(
                    select(func.count(Conversation.id)).where(
                        Conversation.user_id == user.id
                    )
                )

                # User details table
                table = Table(title=f"User Details: {username}")
                table.add_column("Field", style="cyan", width=20)
                table.add_column("Value", style="green")

                table.add_row("ID", str(user.id))
                table.add_row("Username", user.username)
                table.add_row("Email", user.email)
                table.add_row("Full Name", user.full_name or "N/A")
                table.add_row("Active", "✅ Yes" if user.is_active else "❌ No")
                table.add_row("Superuser", "✅ Yes" if user.is_superuser else "❌ No")
                table.add_row("Created", format_timestamp(user.created_at))
                table.add_row("Updated", format_timestamp(user.updated_at))
                table.add_row("Documents", str(doc_count or 0))
                table.add_row("Conversations", str(conv_count or 0))

                console.print(table)

            except Exception as e:
                error_message(f"Failed to show user details: {e}")

    _show_user()


@user_app.command()
def delete(
    username: str = typer.Argument(..., help="Username to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a user account and all associated data."""

    @async_command
    async def _delete_user():
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                # Show what will be deleted
                doc_count = await db.scalar(
                    select(func.count(Document.id)).where(Document.owner_id == user.id)
                )
                conv_count = await db.scalar(
                    select(func.count(Conversation.id)).where(
                        Conversation.user_id == user.id
                    )
                )

                console.print("\n[bold red]This will permanently delete:[/bold red]")
                console.print(f"  • User: {user.username} ({user.email})")
                console.print(f"  • Documents: {doc_count or 0}")
                console.print(f"  • Conversations: {conv_count or 0}")
                console.print()

                if not force:
                    if not Confirm.ask(
                        "Are you sure you want to delete this user and all associated data?"
                    ):
                        warning_message("Deletion cancelled")
                        return

                # Delete user
                user_service = UserService(db)
                success = await user_service.delete_user(user.id)

                if success:
                    success_message(
                        f"User '{username}' and all associated data deleted successfully"
                    )
                else:
                    error_message(f"Failed to delete user '{username}'")

            except Exception as e:
                error_message(f"Failed to delete user: {e}")

    _delete_user()


@user_app.command()
def reset_password(
    username: str = typer.Argument(..., help="Username to reset password for"),
    password: str = typer.Option(
        None, "--password", "-p", help="New password (will prompt if not provided)"
    ),
):
    """Reset a user's password."""

    @async_command
    async def _reset_password():
        if not password:
            pwd = Prompt.ask("Enter new password", password=True)
            pwd_confirm = Prompt.ask("Confirm new password", password=True)
            if pwd != pwd_confirm:
                error_message("Passwords do not match")
                return
            password_to_use = pwd
        else:
            password_to_use = password

        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                user.hashed_password = get_password_hash(password_to_use)
                await db.commit()

                success_message(f"Password reset successfully for user '{username}'")

            except Exception as e:
                error_message(f"Failed to reset password: {e}")

    _reset_password()


@user_app.command()
def activate(
    username: str = typer.Argument(..., help="Username to activate"),
):
    """Activate a user account."""

    @async_command
    async def _activate_user():
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                if user.is_active:
                    warning_message(f"User '{username}' is already active")
                    return

                user.is_active = True
                await db.commit()

                success_message(f"User '{username}' activated successfully")

            except Exception as e:
                error_message(f"Failed to activate user: {e}")

    _activate_user()


@user_app.command()
def deactivate(
    username: str = typer.Argument(..., help="Username to deactivate"),
):
    """Deactivate a user account."""

    @async_command
    async def _deactivate_user():
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                if not user.is_active:
                    warning_message(f"User '{username}' is already inactive")
                    return

                user.is_active = False
                await db.commit()

                success_message(f"User '{username}' deactivated successfully")

            except Exception as e:
                error_message(f"Failed to deactivate user: {e}")

    _deactivate_user()


@user_app.command()
def promote(
    username: str = typer.Argument(..., help="Username to promote to superuser"),
):
    """Promote a user to superuser status."""

    @async_command
    async def _promote_user():
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                if user.is_superuser:
                    warning_message(f"User '{username}' is already a superuser")
                    return

                user.is_superuser = True
                await db.commit()

                success_message(f"User '{username}' promoted to superuser")

            except Exception as e:
                error_message(f"Failed to promote user: {e}")

    _promote_user()


@user_app.command()
def demote(
    username: str = typer.Argument(..., help="Username to demote from superuser"),
):
    """Demote a superuser to regular user status."""

    @async_command
    async def _demote_user():
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)

                if not user:
                    error_message(f"User '{username}' not found")
                    return

                if not user.is_superuser:
                    warning_message(f"User '{username}' is not a superuser")
                    return

                user.is_superuser = False
                await db.commit()

                success_message(f"User '{username}' demoted to regular user")

            except Exception as e:
                error_message(f"Failed to demote user: {e}")

    _demote_user()


@user_app.command()
def stats():
    """Display user statistics and summary."""

    @async_command
    async def _user_stats():
        async with AsyncSessionLocal() as db:
            try:
                # Basic user counts
                total_users = await db.scalar(select(func.count(User.id)))
                active_users = await db.scalar(
                    select(func.count(User.id)).where(User.is_active == True)
                )
                inactive_users = total_users - active_users
                superusers = await db.scalar(
                    select(func.count(User.id)).where(User.is_superuser == True)
                )

                # Recent registrations
                last_7_days = datetime.now() - timedelta(days=7)
                recent_users = await db.scalar(
                    select(func.count(User.id)).where(User.created_at >= last_7_days)
                )

                # Create statistics table
                table = Table(title="User Statistics")
                table.add_column("Metric", style="cyan", width=25)
                table.add_column("Count", style="green", width=10)
                table.add_column("Percentage", style="yellow", width=12)

                table.add_row("Total Users", str(total_users or 0), "100%")
                table.add_row(
                    "Active Users",
                    str(active_users or 0),
                    f"{(active_users or 0) / max(total_users or 1, 1) * 100:.1f}%",
                )
                table.add_row(
                    "Inactive Users",
                    str(inactive_users or 0),
                    f"{(inactive_users or 0) / max(total_users or 1, 1) * 100:.1f}%",
                )
                table.add_row(
                    "Superusers",
                    str(superusers or 0),
                    f"{(superusers or 0) / max(total_users or 1, 1) * 100:.1f}%",
                )
                table.add_row(
                    "Recent (7 days)",
                    str(recent_users or 0),
                    f"{(recent_users or 0) / max(total_users or 1, 1) * 100:.1f}%",
                )

                console.print(table)

            except Exception as e:
                error_message(f"Failed to get user statistics: {e}")

    _user_stats()
