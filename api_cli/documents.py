"""
Document management commands for the API-based CLI.

This module provides document management functionality through API calls.
"""

import asyncio
import typer
from pathlib import Path
from .base import get_client_with_auth, handle_api_response, console, error_message

document_app = typer.Typer(help="📄 Document management commands")


@document_app.command()
def upload(
    file_path: str = typer.Argument(..., help="Path to file to upload"),
    title: str = typer.Option(None, "--title", help="Document title"),
    auto_process: bool = typer.Option(True, "--process/--no-process", help="Auto-process document"),
    user: str = typer.Option(None, "--user", help="Username to upload as (admin only)"),
):
    """Upload a document for processing."""
    
    async def _upload_document():
        if not Path(file_path).exists():
            error_message(f"File not found: {file_path}")
            return
        
        client = get_client_with_auth()
        
        try:
            # Prepare file and form data
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f, "application/octet-stream")}
                data = {
                    "title": title or Path(file_path).stem,
                    "auto_process": str(auto_process).lower()
                }
                
                response = await client.post("/api/v1/documents/upload", data=data, files=files)
                handle_api_response(response, "document upload")
        
        except Exception as e:
            error_message(f"Failed to upload document: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_upload_document())


@document_app.command()
def list(
    status: str = typer.Option(None, "--status", help="Filter by status"),
    user: str = typer.Option(None, "--user", help="Filter by username"),
    limit: int = typer.Option(20, "--limit", help="Maximum number to show"),
):
    """List documents with filtering options."""
    
    async def _list_documents():
        client = get_client_with_auth()
        
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status
            if user:
                params["user"] = user
            
            response = await client.get("/api/v1/documents/", params=params)
            data = handle_api_response(response, "listing documents")
            
            if data and "items" in data:
                from rich.table import Table
                
                documents = data["items"]
                table = Table(title=f"Documents ({len(documents)} shown)")
                table.add_column("Title", style="cyan")
                table.add_column("Status", style="white")
                table.add_column("Size", style="green")
                table.add_column("Created", style="dim")
                
                from .base import format_file_size, format_timestamp
                
                for doc in documents:
                    status_color = {
                        "completed": "green",
                        "failed": "red", 
                        "processing": "yellow",
                        "pending": "blue"
                    }.get(doc.get("status", ""), "white")
                    
                    table.add_row(
                        doc.get("title", ""),
                        f"[{status_color}]{doc.get('status', '')}[/{status_color}]",
                        format_file_size(doc.get("file_size", 0)),
                        format_timestamp(doc.get("created_at", ""))
                    )
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to list documents: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_list_documents())


@document_app.command()
def show(
    document_id: str = typer.Argument(..., help="Document ID to show"),
):
    """Show detailed information about a specific document."""
    
    async def _show_document():
        client = get_client_with_auth()
        
        try:
            response = await client.get(f"/api/v1/documents/{document_id}")
            data = handle_api_response(response, "getting document details")
            
            if data:
                from rich.table import Table
                from .base import format_file_size, format_timestamp
                
                table = Table(title="Document Details")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("ID", str(data.get("id", "")))
                table.add_row("Title", data.get("title", ""))
                table.add_row("File Name", data.get("file_name", ""))
                table.add_row("Status", data.get("status", ""))
                table.add_row("File Size", format_file_size(data.get("file_size", 0)))
                table.add_row("Created", format_timestamp(data.get("created_at", "")))
                table.add_row("Updated", format_timestamp(data.get("updated_at", "")))
                
                if data.get("error_message"):
                    table.add_row("Error", data["error_message"])
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to show document: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_document())


@document_app.command()
def delete(
    document_id: str = typer.Argument(..., help="Document ID to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Delete a document and all its chunks."""
    
    async def _delete_document():
        from .base import confirm_action
        
        if not force:
            if not confirm_action("Are you sure you want to delete this document?"):
                return
        
        client = get_client_with_auth()
        
        try:
            response = await client.delete(f"/api/v1/documents/{document_id}")
            handle_api_response(response, "document deletion")
        
        except Exception as e:
            error_message(f"Failed to delete document: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_delete_document())


@document_app.command()
def reprocess(
    document_id: str = typer.Argument(..., help="Document ID to reprocess"),
):
    """Reprocess a document (re-extract text and create new chunks)."""
    
    async def _reprocess_document():
        client = get_client_with_auth()
        
        try:
            response = await client.post(f"/api/v1/documents/{document_id}/reprocess")
            handle_api_response(response, "document reprocessing")
        
        except Exception as e:
            error_message(f"Failed to reprocess document: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_reprocess_document())


@document_app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", help="Maximum results"),
    threshold: float = typer.Option(0.7, "--threshold", help="Similarity threshold"),
):
    """Search documents using semantic similarity."""
    
    async def _search_documents():
        client = get_client_with_auth()
        
        try:
            data = {
                "query": query,
                "limit": limit,
                "similarity_threshold": threshold
            }
            
            response = await client.post("/api/v1/search/", data=data)
            result = handle_api_response(response, "document search")
            
            if result and "results" in result:
                from rich.table import Table
                
                results = result["results"]
                table = Table(title=f"Search Results ({len(results)} found)")
                table.add_column("Document", style="cyan")
                table.add_column("Chunk", style="white")
                table.add_column("Score", style="green")
                table.add_column("Preview", style="dim")
                
                for res in results:
                    chunk = res.get("chunk", {})
                    doc = res.get("document", {})
                    
                    preview = chunk.get("content", "")[:100] + "..." if len(chunk.get("content", "")) > 100 else chunk.get("content", "")
                    
                    table.add_row(
                        doc.get("title", ""),
                        str(chunk.get("chunk_index", "")),
                        f"{res.get('similarity_score', 0):.3f}",
                        preview
                    )
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to search documents: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_search_documents())


@document_app.command()
def stats():
    """Display document statistics and summary."""
    
    async def _show_stats():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/admin/documents/stats")
            data = handle_api_response(response, "getting document statistics")
            
            if data:
                from rich.panel import Panel
                from rich.columns import Columns
                from .base import format_file_size
                
                counts = data.get("counts_by_status", {})
                storage = data.get("storage", {})
                processing = data.get("processing", {})
                
                # Status counts
                status_panel = Panel(
                    f"Total: [white]{data.get('total_documents', 0)}[/white]\n"
                    f"Completed: [green]{counts.get('completed', 0)}[/green]\n"
                    f"Failed: [red]{counts.get('failed', 0)}[/red]\n"
                    f"Processing: [yellow]{counts.get('processing', 0)}[/yellow]",
                    title="📊 Status",
                    border_style="cyan"
                )
                
                # Storage info
                storage_panel = Panel(
                    f"Total Size: [green]{format_file_size(storage.get('total_size_bytes', 0))}[/green]\n"
                    f"Avg Size: [blue]{format_file_size(storage.get('avg_file_size_bytes', 0))}[/blue]",
                    title="💾 Storage",
                    border_style="green"
                )
                
                # Processing metrics
                proc_panel = Panel(
                    f"Success Rate: [green]{processing.get('success_rate', 0):.1f}%[/green]\n"
                    f"Avg Time: [blue]{processing.get('avg_processing_time_seconds', 0):.1f}s[/blue]",
                    title="⚡ Processing",
                    border_style="yellow"
                )
                
                console.print(Columns([status_panel, storage_panel, proc_panel]))
                
                # File types
                file_types = data.get("file_types", [])
                if file_types:
                    from rich.table import Table
                    
                    table = Table(title="📁 File Types")
                    table.add_column("Extension", style="cyan")
                    table.add_column("Count", style="green")
                    table.add_column("Size", style="blue")
                    
                    for ft in file_types[:5]:
                        table.add_row(
                            ft.get("extension", ""),
                            str(ft.get("count", 0)),
                            format_file_size(ft.get("total_size_bytes", 0))
                        )
                    
                    console.print(table)
        
        except Exception as e:
            error_message(f"Failed to get document statistics: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_stats())


@document_app.command()
def cleanup(
    status_filter: str = typer.Option("failed", "--status", help="Status to filter by"),
    older_than: int = typer.Option(30, "--older-than", help="Days"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Dry run mode"),
):
    """Clean up old or failed documents."""
    
    async def _cleanup_documents():
        client = get_client_with_auth()
        
        try:
            params = {
                "status_filter": status_filter,
                "older_than_days": older_than,
                "dry_run": dry_run
            }
            
            response = await client.post("/api/v1/admin/documents/cleanup", params=params)
            data = handle_api_response(response, "document cleanup")
            
            if data:
                from rich.panel import Panel
                from .base import format_file_size
                
                if dry_run:
                    preview = data.get("preview", [])
                    cleanup_panel = Panel(
                        f"Would delete: [yellow]{data.get('total_count', 0)}[/yellow] documents\n"
                        f"Total size: [blue]{format_file_size(data.get('total_size_bytes', 0))}[/blue]\n"
                        f"Criteria: [dim]{status_filter}, older than {older_than} days[/dim]",
                        title="🗑️ Cleanup Preview",
                        border_style="yellow"
                    )
                    console.print(cleanup_panel)
                    
                    if preview:
                        from rich.table import Table
                        
                        table = Table(title="Preview (first 10)")
                        table.add_column("Title", style="cyan")
                        table.add_column("Status", style="white")
                        table.add_column("Size", style="green")
                        
                        for doc in preview:
                            table.add_row(
                                doc.get("title", ""),
                                doc.get("status", ""),
                                format_file_size(doc.get("file_size", 0))
                            )
                        
                        console.print(table)
                else:
                    cleanup_panel = Panel(
                        f"Deleted: [green]{data.get('deleted_count', 0)}[/green] documents\n"
                        f"Size freed: [blue]{format_file_size(data.get('deleted_size_bytes', 0))}[/blue]",
                        title="🗑️ Cleanup Complete",
                        border_style="green"
                    )
                    console.print(cleanup_panel)
        
        except Exception as e:
            error_message(f"Failed to cleanup documents: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_cleanup_documents())