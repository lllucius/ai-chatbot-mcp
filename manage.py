#!/usr/bin/python3
"""
Enhanced Management CLI for the AI Chatbot Platform.

This is a comprehensive command-line interface that provides full-featured
management capabilities for all aspects of the AI chatbot platform including
users, documents, conversations, analytics, database operations, and background tasks.

The CLI is designed with a modular architecture where each functional area
is handled by a separate module, but all commands are accessible through
a single driver command.

Usage:
    python manage users create john john@example.com
    python manage documents list --status completed
    python manage conversations export 123
    python manage analytics overview
    python manage database backup
    python manage tasks status

Features:
- User management (creation, deletion, roles, statistics)
- Document management (upload, processing, search, cleanup)
- Conversation management (export, import, search, analytics)
- System analytics (usage trends, performance metrics)
- Database management (migrations, backup, maintenance)
- Background task management (monitoring, scheduling, retry)
"""

# Add the app directory to the Python path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import typer
from rich.columns import Columns
from rich.panel import Panel

from app.cli.analytics import analytics_app
from app.cli.base import console, info_message, success_message
from app.cli.conversations import conversation_app
from app.cli.database import database_app
from app.cli.documents import document_app
from app.cli.mcp import mcp_app
from app.cli.profiles import profile_app
from app.cli.prompts import prompt_app
from app.cli.tasks import tasks_app
# Import CLI modules
from app.cli.users import user_app

# Create the main Typer app
app = typer.Typer(
    help="🚀 AI Chatbot Platform - Comprehensive Management CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich"
)

# Add sub-applications
app.add_typer(user_app, name="users", help="👥 User management commands")
app.add_typer(document_app, name="documents", help="📄 Document management commands")  
app.add_typer(conversation_app, name="conversations", help="💬 Conversation management commands")
app.add_typer(analytics_app, name="analytics", help="📊 Analytics and reporting commands")
app.add_typer(database_app, name="database", help="🗄️ Database management commands")
app.add_typer(tasks_app, name="tasks", help="⚙️ Background task management commands")
app.add_typer(mcp_app, name="mcp", help="🔌 MCP server and tool management commands")
app.add_typer(prompt_app, name="prompts", help="📝 Prompt management commands")
app.add_typer(profile_app, name="profiles", help="🎛️ LLM parameter profile management commands")


@app.command()
def version():
    """Show version information."""
    from app.config import settings
    
    version_info = Panel(
        f"[bold]AI Chatbot Platform Management CLI[/bold]\n\n"
        f"Application Version: [green]{settings.app_version}[/green]\n"
        f"Application Name: [blue]{settings.app_name}[/blue]\n"
        f"Debug Mode: [yellow]{'ON' if settings.debug else 'OFF'}[/yellow]\n"
        f"Database: [cyan]PostgreSQL[/cyan]\n"
        f"Background Tasks: [magenta]Celery[/magenta]",
        title="📋 Version Information",
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(version_info)


@app.command()
def health():
    """Perform comprehensive system health check."""
    
    import asyncio

    from sqlalchemy import func, select, text

    from app.database import AsyncSessionLocal
    from app.models.user import User
    
    async def _health_check():
        health_status = {
            "database": False,
            "pgvector": False,
            "models": False,
            "config": False
        }
        
        try:
            # Database connection test
            async with AsyncSessionLocal() as db:
                await db.execute(select(func.count(User.id)))
                health_status["database"] = True
                
                # Check pgvector extension
                vector_check = await db.execute(text("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'vector'
                    )
                """))
                health_status["pgvector"] = vector_check.scalar()
                
                # Check if tables exist
                tables_check = await db.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """))
                health_status["models"] = tables_check.scalar() > 0
                
        except Exception as e:
            console.print(f"[red]Database health check failed: {e}[/red]")
        
        # Configuration check
        from app.config import settings
        required_settings = ["database_url", "secret_key", "openai_api_key"]
        config_ok = all(getattr(settings, setting, None) for setting in required_settings)
        health_status["config"] = config_ok
        
        # Display results
        results = []
        
        # Database
        db_status = "🟢 Connected" if health_status["database"] else "🔴 Failed"
        results.append(Panel(f"Connection: {db_status}", title="Database", border_style="green" if health_status["database"] else "red"))
        
        # pgvector
        vector_status = "🟢 Available" if health_status["pgvector"] else "🟡 Not installed"
        results.append(Panel(f"Extension: {vector_status}", title="Vector Search", border_style="green" if health_status["pgvector"] else "yellow"))
        
        # Models
        models_status = "🟢 Ready" if health_status["models"] else "🔴 Missing"
        results.append(Panel(f"Tables: {models_status}", title="Data Models", border_style="green" if health_status["models"] else "red"))
        
        # Config
        config_status = "🟢 Valid" if health_status["config"] else "🔴 Invalid"
        results.append(Panel(f"Settings: {config_status}", title="Configuration", border_style="green" if health_status["config"] else "red"))
        
        console.print(Panel(
            "System Health Check Results", 
            title="🏥 Health Status",
            border_style="bright_blue"
        ))
        console.print(Columns(results, equal=True))
        
        # Overall status
        overall_healthy = all(health_status.values())
        if overall_healthy:
            success_message("System is healthy and ready to use!")
        else:
            console.print("\n[yellow]⚠️ Some components need attention. Check the results above.[/yellow]")
    
    asyncio.run(_health_check())


@app.command()
def quickstart():
    """Show quick start guide and common commands."""
    
    quickstart_guide = """
[bold]🚀 AI Chatbot Platform Management CLI - Quick Start[/bold]

[yellow]1. First Time Setup:[/yellow]
   • Initialize database: [cyan]python manage.py database init[/cyan]
   • Create admin user: [cyan]python manage.py users create myadmin admin@mycompany.com --superuser[/cyan]
   • Check system health: [cyan]python manage.py health[/cyan]
   • Set up default data: [cyan]python scripts/setup_registry_data.py[/cyan]

[yellow]2. User Management:[/yellow]
   • List users: [cyan]python manage.py users list[/cyan]
   • Create user: [cyan]python manage.py users create john john@example.com[/cyan]
   • Show user details: [cyan]python manage.py users show john[/cyan]
   • Reset password: [cyan]python manage.py users reset-password john[/cyan]

[yellow]3. Document Management:[/yellow]
   • Upload document: [cyan]python manage.py documents upload /path/to/file.pdf[/cyan]
   • List documents: [cyan]python manage.py documents list --status completed[/cyan]
   • Search documents: [cyan]python manage.py documents search "machine learning"[/cyan]
   • Show document: [cyan]python manage.py documents show 123[/cyan]

[yellow]4. Conversation Management:[/yellow]
   • List conversations: [cyan]python manage.py conversations list --user john[/cyan]
   • Show conversation: [cyan]python manage.py conversations show 456 --messages[/cyan]
   • Export chat: [cyan]python manage.py conversations export 456 --format json[/cyan]

[yellow]5. MCP Server & Tool Management:[/yellow]
   • List servers: [cyan]python manage.py mcp list-servers --detailed[/cyan]
   • Add server: [cyan]python manage.py mcp add-server myserver http://localhost:9000/mcp[/cyan]
   • Enable/disable server: [cyan]python manage.py mcp enable-server myserver[/cyan]
   • List tools: [cyan]python manage.py mcp list-tools --enabled-only[/cyan]
   • Tool statistics: [cyan]python manage.py mcp stats[/cyan]

[yellow]6. Prompt Management:[/yellow]
   • List prompts: [cyan]python manage.py prompts list[/cyan]
   • Add prompt: [cyan]python manage.py prompts add myprompt --title "My Prompt" --content "You are..."[/cyan]
   • Set default: [cyan]python manage.py prompts set-default myprompt[/cyan]
   • Show statistics: [cyan]python manage.py prompts stats[/cyan]

[yellow]7. LLM Profile Management:[/yellow]
   • List profiles: [cyan]python manage.py profiles list[/cyan]
   • Create profile: [cyan]python manage.py profiles add creative --title "Creative" --temperature 1.0[/cyan]
   • Set default: [cyan]python manage.py profiles set-default balanced[/cyan]
   • Clone profile: [cyan]python manage.py profiles clone creative creative-v2[/cyan]

[yellow]8. Analytics & Monitoring:[/yellow]
   • System overview: [cyan]python manage.py analytics overview[/cyan]
   • Usage statistics: [cyan]python manage.py analytics usage --period 7d[/cyan]
   • Performance metrics: [cyan]python manage.py analytics performance[/cyan]
   • User analytics: [cyan]python manage.py analytics users --metric messages[/cyan]

[yellow]9. Database Management:[/yellow]
   • Check status: [cyan]python manage.py database status[/cyan]
   • Run migrations: [cyan]python manage.py database upgrade[/cyan]
   • Create backup: [cyan]python manage.py database backup[/cyan]
   • List tables: [cyan]python manage.py database tables[/cyan]

[yellow]10. Background Tasks:[/yellow]
   • Check status: [cyan]python manage.py tasks status[/cyan]
   • View workers: [cyan]python manage.py tasks workers[/cyan]
   • Monitor queues: [cyan]python manage.py tasks queue[/cyan]
   • Retry failed: [cyan]python manage.py tasks retry-failed[/cyan]

[green]💡 Pro Tips:[/green]
   • Use [cyan]--help[/cyan] with any command for detailed options
   • Most commands support filtering and search options
   • Use [cyan]python manage.py [command] [subcommand] --help[/cyan] for specific help
   • Check system health regularly with [cyan]python manage.py health[/cyan]
   • Monitor tool usage with [cyan]python manage.py mcp stats[/cyan]
   • Customize prompts and profiles for different use cases

[blue]📚 Need more help?[/blue]
   • Run [cyan]python manage.py --help[/cyan] for all available commands
   • Use [cyan]python manage.py [module] --help[/cyan] for module-specific commands
   • Each command has detailed help with [cyan]--help[/cyan]
"""
    
    console.print(Panel(
        quickstart_guide,
        title="🚀 Quick Start Guide",
        border_style="bright_green",
        padding=(1, 2)
    ))


@app.command() 
def examples():
    """Show practical usage examples for common tasks."""
    
    examples_text = """
[bold]📚 Practical Usage Examples[/bold]

[yellow]👤 User Management Examples:[/yellow]
   # Create a regular user
   python manage.py users create alice alice@company.com "SecurePass123"
   
   # Create a superuser
   python manage.py users create admin admin@company.com --superuser
   
   # List active users only
   python manage.py users list --active-only --limit 20
   
   # Search for users
   python manage.py users list --search "alice" --sort-by created
   
   # Show detailed user info
   python manage.py users show alice

[yellow]📄 Document Management Examples:[/yellow]
   # Upload and process a document
   python manage.py documents upload ./research.pdf --title "Research Paper" --user alice --process
   
   # List documents by status
   python manage.py documents list --status completed --user alice
   
   # Search documents semantically  
   python manage.py documents search "machine learning algorithms" --limit 5 --threshold 0.8
   
   # Reprocess a failed document
   python manage.py documents reprocess 123
   
   # Clean up old failed documents
   python manage.py documents cleanup --status failed --older-than 30

[yellow]💬 Conversation Management Examples:[/yellow]
   # List user's conversations
   python manage.py conversations list --user alice --active-only
   
   # Show conversation with recent messages
   python manage.py conversations show 456 --messages --message-limit 20
   
   # Export conversation to different formats
   python manage.py conversations export 456 --format json --output chat_backup.json
   python manage.py conversations export 456 --format txt --output chat_log.txt
   
   # Search conversations and messages
   python manage.py conversations search "API documentation" --user alice
   
   # Archive old inactive conversations
   python manage.py conversations archive --older-than 90 --inactive-only

[yellow]📊 Analytics Examples:[/yellow]
   # System health overview
   python manage.py analytics overview
   
   # Usage trends for different periods
   python manage.py analytics usage --period 30d --detailed
   python manage.py analytics trends --days 14
   
   # User activity analysis
   python manage.py analytics users --top 10 --metric messages
   python manage.py analytics users --top 5 --metric documents
   
   # Export comprehensive report
   python manage.py analytics export-report --output monthly_report.json --details

[yellow]🗄️ Database Management Examples:[/yellow]
   # Check database health
   python manage.py database status
   
   # Run migrations
   python manage.py database upgrade head
   
   # Create backups
   python manage.py database backup --output backup_$(date +%Y%m%d).sql
   python manage.py database backup --schema-only --output schema_backup.sql
   
   # Optimize performance
   python manage.py database vacuum
   python manage.py database analyze
   
   # Custom queries
   python manage.py database query "SELECT COUNT(*) FROM users WHERE is_active = true"

[yellow]⚙️ Background Tasks Examples:[/yellow]
   # Monitor task system
   python manage.py tasks status
   python manage.py tasks workers
   python manage.py tasks active
   
   # Schedule custom tasks
   python manage.py tasks schedule process_document '["document_123"]' --delay 30
   
   # Handle failed tasks
   python manage.py tasks retry-failed
   python manage.py tasks stats
   
   # Real-time monitoring
   python manage.py tasks monitor --refresh 10 --duration 300

[green]💡 Advanced Workflows:[/green]

   # Complete user onboarding
   python manage.py users create newuser new@company.com "TempPass123"
   python manage.py documents upload ./welcome.pdf --user newuser --process
   python manage.py analytics users --top 1 --metric documents

   # System maintenance routine
   python manage.py health
   python manage.py database vacuum
   python manage.py tasks retry-failed
   python manage.py documents cleanup --status failed --older-than 7
   python manage.py conversations archive --older-than 180

   # Generate monthly report
   python manage.py analytics usage --period 30d --detailed
   python manage.py analytics performance
   python manage.py analytics export-report --output monthly_$(date +%Y%m).json --details

[blue]🔧 Automation Examples:[/blue]

   # Daily maintenance script
   #!/bin/bash
   echo "Running daily maintenance..."
   python manage.py health
   python manage.py tasks retry-failed
   python manage.py database vacuum
   
   # Weekly backup script  
   #!/bin/bash
   BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
   python manage.py database backup --output $BACKUP_FILE
   echo "Backup created: $BACKUP_FILE"
"""
    
    console.print(Panel(
        examples_text,
        title="📚 Usage Examples",
        border_style="bright_cyan",
        padding=(1, 2)
    ))


@app.command()
def status():
    """Show overall system status summary."""
    
    import asyncio
    from datetime import datetime
    
    async def _system_status():
        console.print(Panel(
            f"[bold]AI Chatbot Platform System Status[/bold]\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            title="🖥️ System Status",
            border_style="bright_blue"
        ))
        
        try:
            from sqlalchemy import func, select

            from app.database import AsyncSessionLocal
            from app.models.conversation import Conversation
            from app.models.document import Document, FileStatus
            from app.models.user import User
            
            async with AsyncSessionLocal() as db:
                # Quick stats
                total_users = await db.scalar(select(func.count(User.id)))
                active_users = await db.scalar(
                    select(func.count(User.id)).where(User.is_active == True)
                )
                
                total_docs = await db.scalar(select(func.count(Document.id)))
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.status == FileStatus.COMPLETED)
                )
                
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                
                # Create status panels
                user_panel = Panel(
                    f"Total: [green]{total_users or 0}[/green]\n"
                    f"Active: [blue]{active_users or 0}[/blue]",
                    title="👥 Users",
                    border_style="green"
                )
                
                doc_panel = Panel(
                    f"Total: [green]{total_docs or 0}[/green]\n"
                    f"Processed: [blue]{completed_docs or 0}[/blue]",
                    title="📄 Documents", 
                    border_style="blue"
                )
                
                conv_panel = Panel(
                    f"Total: [green]{total_convs or 0}[/green]",
                    title="💬 Conversations",
                    border_style="yellow"
                )
                
                console.print(Columns([user_panel, doc_panel, conv_panel]))
                
                # System health indicators
                processing_rate = (completed_docs / max(total_docs, 1)) * 100 if total_docs else 0
                
                status_indicators = []
                if processing_rate > 90:
                    status_indicators.append("🟢 Document Processing: Excellent")
                elif processing_rate > 70:
                    status_indicators.append("🟡 Document Processing: Good")
                else:
                    status_indicators.append("🔴 Document Processing: Needs Attention")
                
                if total_users and total_users > 0:
                    status_indicators.append("🟢 User System: Active")
                else:
                    status_indicators.append("🟡 User System: No users registered")
                
                health_panel = Panel(
                    "\n".join(status_indicators),
                    title="🔋 Health Indicators",
                    border_style="cyan"
                )
                console.print(health_panel)
                
        except Exception as e:
            console.print(f"[red]Error getting system status: {e}[/red]")
            info_message("Use 'python manage.py health' for detailed diagnostics")
    
    asyncio.run(_system_status())


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]CLI Error: {e}[/red]")
        console.print("\n[dim]For help, run: python manage.py --help[/dim]")
        sys.exit(1)
