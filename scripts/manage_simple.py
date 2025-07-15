"""
Simple management CLI for the AI Chatbot Platform.

This script provides basic administrative commands for user management,
system statistics, and maintenance operations.

Generated on: 2025-07-14 03:21:19 UTC
Current User: lllucius
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.services.auth import AuthService
from app.services.user import UserService
from app.utils.security import get_password_hash
from app.utils.logging import setup_logging
from sqlalchemy import select, func

import logging
logger = logging.getLogger(__name__)


class ManagementCLI:
    """Simple CLI for management operations."""
    
    def __init__(self):
        """Initialize CLI."""
        setup_logging()
    
    async def create_user(self, username: str, email: str, password: str, is_superuser: bool = False):
        """Create a new user."""
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                
                # Check if user exists
                existing_user = await auth_service.get_user_by_username(username)
                if existing_user:
                    print(f"❌ User '{username}' already exists")
                    return False
                
                existing_email = await auth_service.get_user_by_email(email)
                if existing_email:
                    print(f"❌ Email '{email}' already in use")
                    return False
                
                # Create user
                user = User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash(password),
                    is_active=True,
                    is_superuser=is_superuser
                )
                
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                user_type = "superuser" if is_superuser else "user"
                print(f"✅ {user_type.title()} '{username}' created successfully")
                return True
                
            except Exception as e:
                print(f"❌ Failed to create user: {e}")
                return False
    
    async def list_users(self, active_only: bool = False):
        """List all users."""
        async with AsyncSessionLocal() as db:
            try:
                user_service = UserService(db)
                users, total = await user_service.list_users(
                    page=1, 
                    size=100, 
                    active_only=active_only
                )
                
                if not users:
                    print("📭 No users found")
                    return
                
                print(f"👥 Found {total} users:")
                print("-" * 80)
                print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Active':<8} {'Super':<8} {'Created'}")
                print("-" * 80)
                
                for user in users:
                    created = user.created_at.strftime("%Y-%m-%d")
                    active = "✅" if user.is_active else "❌"
                    super_user = "⭐" if user.is_superuser else ""
                    
                    print(f"{user.id:<5} {user.username:<20} {user.email:<30} {active:<8} {super_user:<8} {created}")
                
            except Exception as e:
                print(f"❌ Failed to list users: {e}")
    
    async def reset_password(self, username: str, new_password: str):
        """Reset user password."""
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)
                
                if not user:
                    print(f"❌ User '{username}' not found")
                    return False
                
                user.hashed_password = get_password_hash(new_password)
                await db.commit()
                
                print(f"✅ Password reset for user '{username}'")
                return True
                
            except Exception as e:
                print(f"❌ Failed to reset password: {e}")
                return False
    
    async def deactivate_user(self, username: str):
        """Deactivate a user."""
        async with AsyncSessionLocal() as db:
            try:
                auth_service = AuthService(db)
                user = await auth_service.get_user_by_username(username)
                
                if not user:
                    print(f"❌ User '{username}' not found")
                    return False
                
                user.is_active = False
                await db.commit()
                
                print(f"✅ User '{username}' deactivated")
                return True
                
            except Exception as e:
                print(f"❌ Failed to deactivate user: {e}")
                return False
    
    async def get_stats(self):
        """Get system statistics."""
        async with AsyncSessionLocal() as db:
            try:
                # User stats
                total_users = await db.scalar(select(func.count(User.id)))
                active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
                superusers = await db.scalar(select(func.count(User.id)).where(User.is_superuser == True))
                
                # Document stats
                total_docs = await db.scalar(select(func.count(Document.id)))
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.processing_status == "completed")
                )
                
                # Conversation stats
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                active_convs = await db.scalar(
                    select(func.count(Conversation.id)).where(Conversation.is_active == True)
                )
                
                print("📊 SYSTEM STATISTICS")
                print("=" * 50)
                print("👥 Users:")
                print(f"   Total: {total_users}")
                print(f"   Active: {active_users}")
                print(f"   Superusers: {superusers}")
                print()
                print("📄 Documents:")
                print(f"   Total: {total_docs}")
                print(f"   Processed: {completed_docs}")
                print()
                print("💬 Conversations:")
                print(f"   Total: {total_convs}")
                print(f"   Active: {active_convs}")
                print()
                print("⚙️  Configuration:")
                print(f"   App Version: {settings.app_version}")
                print(f"   Debug Mode: {'ON' if settings.debug else 'OFF'}")
                print(f"   Upload Dir: {settings.upload_directory}")
                print(f"   Max File Size: {settings.max_file_size:,} bytes")
                print("=" * 50)
                
            except Exception as e:
                print(f"❌ Failed to get statistics: {e}")
    
    async def init_db(self):
        """Initialize database."""
        try:
            from app.database import init_db
            await init_db()
            print("✅ Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    
    def show_examples(self):
        """Show usage examples."""
        print("🔧 MANAGEMENT CLI EXAMPLES")
        print("=" * 50)
        print("Create a regular user:")
        print("  python scripts/manage_simple.py create-user john john@example.com SecurePass123")
        print()
        print("Create a superuser:")
        print("  python scripts/manage_simple.py create-superuser admin admin@example.com AdminPass123")
        print()
        print("List all users:")
        print("  python scripts/manage_simple.py list-users")
        print()
        print("List only active users:")
        print("  python scripts/manage_simple.py list-users --active-only")
        print()
        print("Reset user password:")
        print("  python scripts/manage_simple.py reset-password john NewPassword123")
        print()
        print("Deactivate a user:")
        print("  python scripts/manage_simple.py deactivate-user john")
        print()
        print("Show system statistics:")
        print("  python scripts/manage_simple.py stats")
        print()
        print("Initialize database:")
        print("  python scripts/manage_simple.py init-db")
        print("=" * 50)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AI Chatbot Platform Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create user command
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument("username", help="Username")
    create_user_parser.add_argument("email", help="Email address")
    create_user_parser.add_argument("password", help="Password")
    
    # Create superuser command
    create_super_parser = subparsers.add_parser("create-superuser", help="Create a new superuser")
    create_super_parser.add_argument("username", help="Username")
    create_super_parser.add_argument("email", help="Email address")
    create_super_parser.add_argument("password", help="Password")
    
    # List users command
    list_users_parser = subparsers.add_parser("list-users", help="List all users")
    list_users_parser.add_argument("--active-only", action="store_true", help="Show only active users")
    
    # Reset password command
    reset_pass_parser = subparsers.add_parser("reset-password", help="Reset user password")
    reset_pass_parser.add_argument("username", help="Username")
    reset_pass_parser.add_argument("password", help="New password")
    
    # Deactivate user command
    deactivate_parser = subparsers.add_parser("deactivate-user", help="Deactivate a user")
    deactivate_parser.add_argument("username", help="Username")
    
    # Stats command
    subparsers.add_parser("stats", help="Show system statistics")
    
    # Init DB command
    subparsers.add_parser("init-db", help="Initialize database")
    
    # Examples command
    subparsers.add_parser("examples", help="Show usage examples")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ManagementCLI()
    
    if args.command == "create-user":
        await cli.create_user(args.username, args.email, args.password, False)
    elif args.command == "create-superuser":
        await cli.create_user(args.username, args.email, args.password, True)
    elif args.command == "list-users":
        await cli.list_users(args.active_only)
    elif args.command == "reset-password":
        await cli.reset_password(args.username, args.password)
    elif args.command == "deactivate-user":
        await cli.deactivate_user(args.username)
    elif args.command == "stats":
        await cli.get_stats()
    elif args.command == "init-db":
        await cli.init_db()
    elif args.command == "examples":
        cli.show_examples()


if __name__ == "__main__":
    asyncio.run(main())