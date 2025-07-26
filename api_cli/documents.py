"""
Document management commands for the API-based CLI.

This module provides all document management functionality through the SDK,
including upload, processing, search, and maintenance operations.
"""

from pathlib import Path
from typing import List, Optional
from uuid import UUID

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from client.ai_chatbot_sdk import ApiError, DocumentSearchRequest

from .base import (confirm_action, console, display_key_value_pairs,
                   error_message, format_file_size, format_timestamp,
                   get_sdk_with_auth, info_message, success_message)

document_app = typer.Typer(help="📄 Document management commands")


@document_app.command()
def upload(
    file_path: str = typer.Argument(..., help="Path to the file to upload"),
    title: Optional[str] = typer.Option(None, "--title", help="Custom title for the document"),
    user: Optional[str] = typer.Option(None, "--user", help="Username to upload as (admin only)"),
    process: bool = typer.Option(True, "--process/--no-process", help="Start processing immediately"),
):
    """Upload a document for processing with comprehensive validation."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Validate file path
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_message(f"File not found: {file_path}")
            return
        
        if not file_path_obj.is_file():
            error_message(f"Path is not a file: {file_path}")
            return
        
        # Check file size
        file_size = file_path_obj.stat().st_size
        info_message(f"Uploading file: {file_path_obj.name} ({format_file_size(file_size)})")
        
        # Open file and upload
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Uploading document...", total=None)
            
            with open(file_path, "rb") as f:
                result = sdk.documents.upload(f, title=title or file_path_obj.name)
            
            progress.update(task, description="Upload complete!")
        
        success_message("Document uploaded successfully")
        
        # Display document info
        doc = result.document
        doc_info = {
            "ID": str(doc.id),
            "Title": doc.title,
            "Filename": doc.filename,
            "File Type": doc.file_type.upper(),
            "File Size": format_file_size(doc.file_size),
            "Processing Status": doc.processing_status.title(),
            "Processing Started": "Yes" if result.processing_started else "No",
            "Created": format_timestamp(doc.created_at.isoformat() if doc.created_at else "")
        }
        
        display_key_value_pairs(doc_info, "Document Uploaded")
        
        if result.processing_started:
            info_message("Document processing has started. Use 'status' command to check progress.")
        
    except ApiError as e:
        error_message(f"Failed to upload document: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def list(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(20, "--size", "-s", help="Items per page"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by processing status"),
    file_type: Optional[str] = typer.Option(None, "--file-type", help="Filter by file type"),
    user: Optional[str] = typer.Option(None, "--user", help="Filter by user (admin only)"),
):
    """List documents with comprehensive filtering and detailed display."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Get documents using SDK
        documents_response = sdk.documents.list(
            page=page,
            size=size,
            status=status,
            file_type=file_type
        )
        
        if not documents_response.success:
            error_message("Failed to retrieve documents")
            return
            
        documents = documents_response.items
        pagination = documents_response.pagination
        
        if not documents:
            info_message("No documents found matching the criteria")
            return
        
        # Create and display table
        table = Table(title=f"Documents (Page {pagination.page} of {pagination.total} total)")
        
        table.add_column("ID", style="dim")
        table.add_column("Title", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Size", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Chunks", style="magenta")
        table.add_column("Created", style="dim")
        
        for doc in documents:
            status_style = "green" if doc.processing_status == "completed" else "yellow" if doc.processing_status == "processing" else "red"
            
            table.add_row(
                str(doc.id)[:8] + "...",
                doc.title[:40] + "..." if len(doc.title) > 40 else doc.title,
                doc.file_type.upper(),
                format_file_size(doc.file_size),
                f"[{status_style}]{doc.processing_status.title()}[/{status_style}]",
                str(doc.chunk_count),
                format_timestamp(doc.created_at.isoformat() if doc.created_at else "")
            )
        
        console.print(table)
        
        # Show pagination info
        if pagination.total > size:
            info_message(f"Showing {len(documents)} of {pagination.total} total documents")
            
    except ApiError as e:
        error_message(f"Failed to list documents: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def show(
    document_id: str = typer.Argument(..., help="Document ID to display"),
):
    """Display detailed information about a specific document."""
    
    try:
        sdk = get_sdk_with_auth()
        
        doc_uuid = UUID(document_id)
        doc = sdk.documents.get(doc_uuid)
        
        # Display document information
        doc_info = {
            "ID": str(doc.id),
            "Title": doc.title,
            "Filename": doc.filename,
            "File Type": doc.file_type.upper(),
            "MIME Type": doc.mime_type or "Unknown",
            "File Size": format_file_size(doc.file_size),
            "Processing Status": doc.processing_status.title(),
            "Chunk Count": str(doc.chunk_count),
            "Owner ID": str(doc.owner_id),
            "Created": format_timestamp(doc.created_at.isoformat() if doc.created_at else ""),
            "Updated": format_timestamp(doc.updated_at.isoformat() if doc.updated_at else "")
        }
        
        display_key_value_pairs(doc_info, "Document Details")
        
        # Show metadata if available
        if doc.metainfo:
            console.print("\n[bold]Metadata:[/bold]")
            for key, value in doc.metainfo.items():
                console.print(f"  [cyan]{key}:[/cyan] {value}")
        
        # Get processing status
        try:
            status = sdk.documents.status(doc_uuid)
            
            if status.status != "completed":
                console.print("\n[bold]Processing Status:[/bold]")
                console.print(f"  Status: {status.status.title()}")
                console.print(f"  Progress: {status.progress:.1%}")
                console.print(f"  Chunks Processed: {status.chunks_processed}/{status.total_chunks}")
                
                if status.error_message:
                    console.print(f"  [red]Error: {status.error_message}[/red]")
                    
        except ApiError:
            # Status endpoint might not be available
            pass
        
    except ValueError:
        error_message("Invalid document ID format")
        raise typer.Exit(1)
    except ApiError as e:
        error_message(f"Failed to get document: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    algorithm: str = typer.Option("hybrid", "--algorithm", "-a", help="Search algorithm (vector/text/hybrid/mmr)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results to return"),
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Similarity threshold"),
    document_ids: Optional[List[str]] = typer.Option(None, "--document-id", help="Specific document IDs to search"),
):
    """Search across documents using various algorithms."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Convert document IDs to UUIDs if provided
        doc_uuids = None
        if document_ids:
            try:
                doc_uuids = [UUID(doc_id) for doc_id in document_ids]
            except ValueError:
                error_message("Invalid document ID format")
                return
        
        # Create search request
        search_request = DocumentSearchRequest(
            query=query,
            algorithm=algorithm,
            limit=limit,
            threshold=threshold,
            document_ids=doc_uuids
        )
        
        # Perform search
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching documents...", total=None)
            
            results = sdk.search.search(search_request)
            
            progress.update(task, description="Search complete!")
        
        if not results.get("success", True):
            error_message("Search failed")
            return
        
        search_results = results.get("results", [])
        
        if not search_results:
            info_message("No documents found matching the search criteria")
            return
        
        # Display results
        console.print(f"\n[bold]Search Results for:[/bold] '{query}'")
        console.print(f"[dim]Algorithm: {algorithm}, Threshold: {threshold}[/dim]\n")
        
        table = Table(title=f"Found {len(search_results)} results")
        
        table.add_column("Score", style="green")
        table.add_column("Document", style="cyan")
        table.add_column("Content", style="white")
        table.add_column("Metadata", style="dim")
        
        for result in search_results:
            score = f"{result.get('score', 0):.3f}"
            doc_id = str(result.get('document_id', ''))[:8] + "..."
            content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
            metadata = str(result.get('metadata', {}))[:50] + "..." if len(str(result.get('metadata', {}))) > 50 else str(result.get('metadata', {}))
            
            table.add_row(score, doc_id, content, metadata)
        
        console.print(table)
        
    except ApiError as e:
        error_message(f"Search failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def status(
    document_id: str = typer.Argument(..., help="Document ID to check status"),
):
    """Check document processing status."""
    
    try:
        sdk = get_sdk_with_auth()
        
        doc_uuid = UUID(document_id)
        status = sdk.documents.status(doc_uuid)
        
        # Display status information
        status_info = {
            "Document ID": str(status.document_id),
            "Status": status.status.title(),
            "Progress": f"{status.progress:.1%}",
            "Chunks Processed": f"{status.chunks_processed}/{status.total_chunks}",
        }
        
        if status.started_at:
            status_info["Started At"] = format_timestamp(status.started_at)
            
        if status.completed_at:
            status_info["Completed At"] = format_timestamp(status.completed_at)
            
        if status.error_message:
            status_info["Error"] = status.error_message
        
        display_key_value_pairs(status_info, "Processing Status")
        
    except ValueError:
        error_message("Invalid document ID format")
        raise typer.Exit(1)
    except ApiError as e:
        error_message(f"Failed to get status: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def reprocess(
    document_id: str = typer.Argument(..., help="Document ID to reprocess"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Reprocess a document."""
    
    try:
        sdk = get_sdk_with_auth()
        
        doc_uuid = UUID(document_id)
        
        # Get document info first
        doc = sdk.documents.get(doc_uuid)
        
        # Confirm reprocessing
        if not confirm:
            if not confirm_action(f"Reprocess document '{doc.title}'? This will recreate all chunks."):
                info_message("Reprocessing cancelled")
                return
        
        # Start reprocessing
        result = sdk.documents.reprocess(doc_uuid)
        
        if result.success:
            success_message(f"Document '{doc.title}' reprocessing started")
            info_message("Use 'status' command to monitor progress")
        else:
            error_message(f"Failed to start reprocessing: {result.message}")
            
    except ValueError:
        error_message("Invalid document ID format")
        raise typer.Exit(1)
    except ApiError as e:
        error_message(f"Failed to reprocess document: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def delete(
    document_id: str = typer.Argument(..., help="Document ID to delete"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Delete a document and all its chunks."""
    
    try:
        sdk = get_sdk_with_auth()
        
        doc_uuid = UUID(document_id)
        
        # Get document info first
        doc = sdk.documents.get(doc_uuid)
        
        # Confirm deletion
        if not confirm:
            if not confirm_action(f"Delete document '{doc.title}'? This action cannot be undone."):
                info_message("Deletion cancelled")
                return
        
        # Delete document
        result = sdk.documents.delete(doc_uuid)
        
        if result.success:
            success_message(f"Document '{doc.title}' deleted successfully")
        else:
            error_message(f"Failed to delete document: {result.message}")
            
    except ValueError:
        error_message("Invalid document ID format")
        raise typer.Exit(1)
    except ApiError as e:
        error_message(f"Failed to delete document: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def cleanup(
    older_than: Optional[int] = typer.Option(None, "--older-than", help="Remove documents older than N days"),
    status: Optional[str] = typer.Option(None, "--status", help="Remove documents with specific status"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Clean up old or failed documents."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Confirm cleanup
        if not confirm:
            conditions = []
            if older_than:
                conditions.append(f"older than {older_than} days")
            if status:
                conditions.append(f"with status '{status}'")
            
            condition_str = " and ".join(conditions) if conditions else "matching the criteria"
            
            if not confirm_action(f"Clean up documents {condition_str}? This action cannot be undone."):
                info_message("Cleanup cancelled")
                return
        
        # Perform cleanup using admin endpoint
        result = sdk.admin.cleanup_documents(older_than=older_than, status=status)
        
        if result.success:
            success_message("Document cleanup completed")
            info_message(result.message)
        else:
            error_message(f"Cleanup failed: {result.message}")
            
    except ApiError as e:
        error_message(f"Failed to cleanup documents: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def download(
    document_id: str = typer.Argument(..., help="Document ID to download"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Download the original document file."""
    
    try:
        sdk = get_sdk_with_auth()
        
        doc_uuid = UUID(document_id)
        
        # Get document info first
        doc = sdk.documents.get(doc_uuid)
        
        # Download the file
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading document...", total=None)
            
            file_content = sdk.documents.download(doc_uuid)
            
            progress.update(task, description="Download complete!")
        
        # Determine output path
        if output:
            output_path = Path(output)
        else:
            output_path = Path(doc.filename)
        
        # Write file
        with open(output_path, "wb") as f:
            f.write(file_content)
        
        success_message(f"Document downloaded to: {output_path}")
        info_message(f"File size: {format_file_size(len(file_content))}")
        
    except ValueError:
        error_message("Invalid document ID format")
        raise typer.Exit(1)
    except ApiError as e:
        error_message(f"Failed to download document: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@document_app.command()
def stats():
    """Display document statistics and analytics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        # Get document statistics from admin endpoint
        stats = sdk.admin.get_document_stats()
        
        # Display statistics
        stats_info = {
            "Total Documents": stats.get("total_documents", 0),
            "Completed": stats.get("completed_documents", 0),
            "Processing": stats.get("processing_documents", 0),
            "Failed": stats.get("failed_documents", 0),
            "Total Size": format_file_size(stats.get("total_size_bytes", 0)),
            "Average Size": format_file_size(stats.get("avg_size_bytes", 0)),
            "Success Rate": f"{stats.get('success_rate', 0):.1f}%"
        }
        
        display_key_value_pairs(stats_info, "Document Statistics")
        
        # Show file type breakdown if available
        file_types = stats.get("file_types", [])
        if file_types:
            console.print("\n[bold]File Types:[/bold]")
            
            table = Table()
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="green")
            table.add_column("Total Size", style="blue")
            
            for ft in file_types:
                table.add_row(
                    ft.get("type", "").upper(),
                    str(ft.get("count", 0)),
                    format_file_size(ft.get("total_size", 0))
                )
            
            console.print(table)
        
    except ApiError as e:
        error_message(f"Failed to get document statistics: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error_message(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)