"Management CLI for the AI chatbot platform."

import sys
from pathlib import Path
import typer
from rich.columns import Columns
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent.parent))
from app.cli.analytics import analytics_app
from app.cli.base import console, info_message, success_message
from app.cli.conversations import conversation_app
from app.cli.database import database_app
from app.cli.documents import document_app
from app.cli.mcp import mcp_app
from app.cli.profiles import profile_app
from app.cli.prompts import prompt_app
from app.cli.tasks import tasks_app
from app.cli.users import user_app

app = typer.Typer(
    help="🚀 AI Chatbot Platform - Comprehensive Management CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)
app.add_typer(user_app, name="users", help="👥 User management commands")
app.add_typer(document_app, name="documents", help="📄 Document management commands")
app.add_typer(
    conversation_app, name="conversations", help="💬 Conversation management commands"
)
app.add_typer(
    analytics_app, name="analytics", help="📊 Analytics and reporting commands"
)
app.add_typer(database_app, name="database", help="🗄️ Database management commands")
app.add_typer(tasks_app, name="tasks", help="⚙️ Background task management commands")
app.add_typer(mcp_app, name="mcp", help="🔌 MCP server and tool management commands")
app.add_typer(prompt_app, name="prompts", help="📝 Prompt management commands")
app.add_typer(
    profile_app, name="profiles", help="🎛️ LLM parameter profile management commands"
)


@app.command()
def version():
    "Version operation."
    from app.config import settings

    version_info = Panel(
        f"""[bold]AI Chatbot Platform Management CLI[/bold]

Application Version: [green]{settings.app_version}[/green]
Application Name: [blue]{settings.app_name}[/blue]
Debug Mode: [yellow]{('ON' if settings.debug else 'OFF')}[/yellow]
Database: [cyan]PostgreSQL[/cyan]
Background Tasks: [magenta]Celery[/magenta]""",
        title="📋 Version Information",
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(version_info)


@app.command()
def health():
    "Health operation."
    import asyncio
    from sqlalchemy import func, select, text
    from app.database import AsyncSessionLocal
    from app.models.user import User

    async def _health_check():
        "Health Check operation."
        health_status = {
            "database": False,
            "pgvector": False,
            "models": False,
            "config": False,
        }
        try:
            async with AsyncSessionLocal() as db:
                (await db.execute(select(func.count(User.id))))
                health_status["database"] = True
                vector_check = await db.execute(
                    text(
                        "\n                    SELECT EXISTS(\n                        SELECT 1 FROM pg_extension WHERE extname = 'vector'\n                    )\n                "
                    )
                )
                health_status["pgvector"] = vector_check.scalar()
                tables_check = await db.execute(
                    text(
                        "\n                    SELECT COUNT(*) FROM information_schema.tables \n                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'\n                "
                    )
                )
                health_status["models"] = tables_check.scalar() > 0
        except Exception as e:
            console.print(f"[red]Database health check failed: {e}[/red]")
        from app.config import settings

        required_settings = ["database_url", "secret_key", "openai_api_key"]
        config_ok = all(
            (getattr(settings, setting, None) for setting in required_settings)
        )
        health_status["config"] = config_ok
        results = []
        db_status = "🟢 Connected" if health_status["database"] else "🔴 Failed"
        results.append(
            Panel(
                f"Connection: {db_status}",
                title="Database",
                border_style=("green" if health_status["database"] else "red"),
            )
        )
        vector_status = (
            "🟢 Available" if health_status["pgvector"] else "🟡 Not installed"
        )
        results.append(
            Panel(
                f"Extension: {vector_status}",
                title="Vector Search",
                border_style=("green" if health_status["pgvector"] else "yellow"),
            )
        )
        models_status = "🟢 Ready" if health_status["models"] else "🔴 Missing"
        results.append(
            Panel(
                f"Tables: {models_status}",
                title="Data Models",
                border_style=("green" if health_status["models"] else "red"),
            )
        )
        config_status = "🟢 Valid" if health_status["config"] else "🔴 Invalid"
        results.append(
            Panel(
                f"Settings: {config_status}",
                title="Configuration",
                border_style=("green" if health_status["config"] else "red"),
            )
        )
        console.print(
            Panel(
                "System Health Check Results",
                title="🏥 Health Status",
                border_style="bright_blue",
            )
        )
        console.print(Columns(results, equal=True))
        overall_healthy = all(health_status.values())
        if overall_healthy:
            success_message("System is healthy and ready to use!")
        else:
            console.print(
                "\n[yellow]⚠️ Some components need attention. Check the results above.[/yellow]"
            )

    asyncio.run(_health_check())


@app.command()
def quickstart():
    "Quickstart operation."
    quickstart_guide = '\n[bold]🚀 AI Chatbot Platform Management CLI - Quick Start[/bold]\n\n[yellow]1. First Time Setup:[/yellow]\n   • Initialize database: [cyan]python manage.py database init[/cyan]\n   • Create admin user: [cyan]python manage.py users create myadmin admin@mycompany.com --superuser[/cyan]\n   • Check system health: [cyan]python manage.py health[/cyan]\n   • Set up default data: [cyan]python scripts/setup_registry_data.py[/cyan]\n\n[yellow]2. User Management:[/yellow]\n   • List users: [cyan]python manage.py users list[/cyan]\n   • Create user: [cyan]python manage.py users create john john@example.com[/cyan]\n   • Show user details: [cyan]python manage.py users show john[/cyan]\n   • Reset password: [cyan]python manage.py users reset-password john[/cyan]\n\n[yellow]3. Document Management:[/yellow]\n   • Upload document: [cyan]python manage.py documents upload /path/to/file.pdf[/cyan]\n   • List documents: [cyan]python manage.py documents list --status completed[/cyan]\n   • Search documents: [cyan]python manage.py documents search "machine learning"[/cyan]\n   • Show document: [cyan]python manage.py documents show 123[/cyan]\n\n[yellow]4. Conversation Management:[/yellow]\n   • List conversations: [cyan]python manage.py conversations list --user john[/cyan]\n   • Show conversation: [cyan]python manage.py conversations show 456 --messages[/cyan]\n   • Export chat: [cyan]python manage.py conversations export 456 --format json[/cyan]\n\n[yellow]5. MCP Server & Tool Management:[/yellow]\n   • List servers: [cyan]python manage.py mcp list-servers --detailed[/cyan]\n   • Add server: [cyan]python manage.py mcp add-server myserver http://localhost:9000/mcp[/cyan]\n   • Enable/disable server: [cyan]python manage.py mcp enable-server myserver[/cyan]\n   • List tools: [cyan]python manage.py mcp list-tools --enabled-only[/cyan]\n   • Tool statistics: [cyan]python manage.py mcp stats[/cyan]\n\n[yellow]6. Prompt Management:[/yellow]\n   • List prompts: [cyan]python manage.py prompts list[/cyan]\n   • Add prompt: [cyan]python manage.py prompts add myprompt --title "My Prompt" --content "You are..."[/cyan]\n   • Set default: [cyan]python manage.py prompts set-default myprompt[/cyan]\n   • Show statistics: [cyan]python manage.py prompts stats[/cyan]\n\n[yellow]7. LLM Profile Management:[/yellow]\n   • List profiles: [cyan]python manage.py profiles list[/cyan]\n   • Create profile: [cyan]python manage.py profiles add creative --title "Creative" --temperature 1.0[/cyan]\n   • Set default: [cyan]python manage.py profiles set-default balanced[/cyan]\n   • Clone profile: [cyan]python manage.py profiles clone creative creative-v2[/cyan]\n\n[yellow]8. Analytics & Monitoring:[/yellow]\n   • System overview: [cyan]python manage.py analytics overview[/cyan]\n   • Usage statistics: [cyan]python manage.py analytics usage --period 7d[/cyan]\n   • Performance metrics: [cyan]python manage.py analytics performance[/cyan]\n   • User analytics: [cyan]python manage.py analytics users --metric messages[/cyan]\n\n[yellow]9. Database Management:[/yellow]\n   • Check status: [cyan]python manage.py database status[/cyan]\n   • Run migrations: [cyan]python manage.py database upgrade[/cyan]\n   • Create backup: [cyan]python manage.py database backup[/cyan]\n   • List tables: [cyan]python manage.py database tables[/cyan]\n\n[yellow]10. Background Tasks:[/yellow]\n   • Check status: [cyan]python manage.py tasks status[/cyan]\n   • View workers: [cyan]python manage.py tasks workers[/cyan]\n   • Monitor queues: [cyan]python manage.py tasks queue[/cyan]\n   • Retry failed: [cyan]python manage.py tasks retry-failed[/cyan]\n\n[green]💡 Pro Tips:[/green]\n   • Use [cyan]--help[/cyan] with any command for detailed options\n   • Most commands support filtering and search options\n   • Use [cyan]python manage.py [command] [subcommand] --help[/cyan] for specific help\n   • Check system health regularly with [cyan]python manage.py health[/cyan]\n   • Monitor tool usage with [cyan]python manage.py mcp stats[/cyan]\n   • Customize prompts and profiles for different use cases\n\n[blue]📚 Need more help?[/blue]\n   • Run [cyan]python manage.py --help[/cyan] for all available commands\n   • Use [cyan]python manage.py [module] --help[/cyan] for module-specific commands\n   • Each command has detailed help with [cyan]--help[/cyan]\n'
    console.print(
        Panel(
            quickstart_guide,
            title="🚀 Quick Start Guide",
            border_style="bright_green",
            padding=(1, 2),
        )
    )


@app.command()
def examples():
    "Examples operation."
    examples_text = '\n[bold]📚 Practical Usage Examples[/bold]\n\n[yellow]👤 User Management Examples:[/yellow]\n   # Create a regular user\n   python manage.py users create alice alice@company.com "SecurePass123"\n   \n   # Create a superuser\n   python manage.py users create admin admin@company.com --superuser\n   \n   # List active users only\n   python manage.py users list --active-only --limit 20\n   \n   # Search for users\n   python manage.py users list --search "alice" --sort-by created\n   \n   # Show detailed user info\n   python manage.py users show alice\n\n[yellow]📄 Document Management Examples:[/yellow]\n   # Upload and process a document\n   python manage.py documents upload ./research.pdf --title "Research Paper" --user alice --process\n   \n   # List documents by status\n   python manage.py documents list --status completed --user alice\n   \n   # Search documents semantically  \n   python manage.py documents search "machine learning algorithms" --limit 5 --threshold 0.8\n   \n   # Reprocess a failed document\n   python manage.py documents reprocess 123\n   \n   # Clean up old failed documents\n   python manage.py documents cleanup --status failed --older-than 30\n\n[yellow]💬 Conversation Management Examples:[/yellow]\n   # List user\'s conversations\n   python manage.py conversations list --user alice --active-only\n   \n   # Show conversation with recent messages\n   python manage.py conversations show 456 --messages --message-limit 20\n   \n   # Export conversation to different formats\n   python manage.py conversations export 456 --format json --output chat_backup.json\n   python manage.py conversations export 456 --format txt --output chat_log.txt\n   \n   # Search conversations and messages\n   python manage.py conversations search "API documentation" --user alice\n   \n   # Archive old inactive conversations\n   python manage.py conversations archive --older-than 90 --inactive-only\n\n[yellow]📊 Analytics Examples:[/yellow]\n   # System health overview\n   python manage.py analytics overview\n   \n   # Usage trends for different periods\n   python manage.py analytics usage --period 30d --detailed\n   python manage.py analytics trends --days 14\n   \n   # User activity analysis\n   python manage.py analytics users --top 10 --metric messages\n   python manage.py analytics users --top 5 --metric documents\n   \n   # Export comprehensive report\n   python manage.py analytics export-report --output monthly_report.json --details\n\n[yellow]🗄️ Database Management Examples:[/yellow]\n   # Check database health\n   python manage.py database status\n   \n   # Run migrations\n   python manage.py database upgrade head\n   \n   # Create backups\n   python manage.py database backup --output backup_$(date +%Y%m%d).sql\n   python manage.py database backup --schema-only --output schema_backup.sql\n   \n   # Optimize performance\n   python manage.py database vacuum\n   python manage.py database analyze\n   \n   # Custom queries\n   python manage.py database query "SELECT COUNT(*) FROM users WHERE is_active = true"\n\n[yellow]⚙️ Background Tasks Examples:[/yellow]\n   # Monitor task system\n   python manage.py tasks status\n   python manage.py tasks workers\n   python manage.py tasks active\n   \n   # Schedule custom tasks\n   python manage.py tasks schedule process_document \'["document_123"]\' --delay 30\n   \n   # Handle failed tasks\n   python manage.py tasks retry-failed\n   python manage.py tasks stats\n   \n   # Real-time monitoring\n   python manage.py tasks monitor --refresh 10 --duration 300\n\n[green]💡 Advanced Workflows:[/green]\n\n   # Complete user onboarding\n   python manage.py users create newuser new@company.com "TempPass123"\n   python manage.py documents upload ./welcome.pdf --user newuser --process\n   python manage.py analytics users --top 1 --metric documents\n\n   # System maintenance routine\n   python manage.py health\n   python manage.py database vacuum\n   python manage.py tasks retry-failed\n   python manage.py documents cleanup --status failed --older-than 7\n   python manage.py conversations archive --older-than 180\n\n   # Generate monthly report\n   python manage.py analytics usage --period 30d --detailed\n   python manage.py analytics performance\n   python manage.py analytics export-report --output monthly_$(date +%Y%m).json --details\n\n[blue]🔧 Automation Examples:[/blue]\n\n   # Daily maintenance script\n   #!/bin/bash\n   echo "Running daily maintenance..."\n   python manage.py health\n   python manage.py tasks retry-failed\n   python manage.py database vacuum\n   \n   # Weekly backup script  \n   #!/bin/bash\n   BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"\n   python manage.py database backup --output $BACKUP_FILE\n   echo "Backup created: $BACKUP_FILE"\n'
    console.print(
        Panel(
            examples_text,
            title="📚 Usage Examples",
            border_style="bright_cyan",
            padding=(1, 2),
        )
    )


@app.command()
def status():
    "Status operation."
    import asyncio
    from datetime import datetime

    async def _system_status():
        "System Status operation."
        console.print(
            Panel(
                f"""[bold]AI Chatbot Platform System Status[/bold]
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}""",
                title="🖥️ System Status",
                border_style="bright_blue",
            )
        )
        try:
            from sqlalchemy import func, select
            from app.database import AsyncSessionLocal
            from app.models.conversation import Conversation
            from app.models.document import Document, FileStatus
            from app.models.user import User

            async with AsyncSessionLocal() as db:
                total_users = await db.scalar(select(func.count(User.id)))
                active_users = await db.scalar(
                    select(func.count(User.id)).where((User.is_active == True))
                )
                total_docs = await db.scalar(select(func.count(Document.id)))
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        (Document.status == FileStatus.COMPLETED)
                    )
                )
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                user_panel = Panel(
                    f"""Total: [green]{(total_users or 0)}[/green]
Active: [blue]{(active_users or 0)}[/blue]""",
                    title="👥 Users",
                    border_style="green",
                )
                doc_panel = Panel(
                    f"""Total: [green]{(total_docs or 0)}[/green]
Processed: [blue]{(completed_docs or 0)}[/blue]""",
                    title="📄 Documents",
                    border_style="blue",
                )
                conv_panel = Panel(
                    f"Total: [green]{(total_convs or 0)}[/green]",
                    title="💬 Conversations",
                    border_style="yellow",
                )
                console.print(Columns([user_panel, doc_panel, conv_panel]))
                processing_rate = (
                    ((completed_docs / max(total_docs, 1)) * 100) if total_docs else 0
                )
                status_indicators = []
                if processing_rate > 90:
                    status_indicators.append("🟢 Document Processing: Excellent")
                elif processing_rate > 70:
                    status_indicators.append("🟡 Document Processing: Good")
                else:
                    status_indicators.append("🔴 Document Processing: Needs Attention")
                if total_users and (total_users > 0):
                    status_indicators.append("🟢 User System: Active")
                else:
                    status_indicators.append("🟡 User System: No users registered")
                health_panel = Panel(
                    "\n".join(status_indicators),
                    title="🔋 Health Indicators",
                    border_style="cyan",
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
