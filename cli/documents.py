"""
Document management commands for the AI Chatbot Platform CLI.

This module provides comprehensive document processing and management functionality
through async operations and the AI Chatbot SDK. It enables users to upload,
process, search, and manage documents with full support for various file formats,
text extraction, and vector embedding generation.

Key Features:
    - Document upload and processing with format validation
    - Text extraction and content analysis
    - Vector embedding generation for similarity search
    - Document search and retrieval with advanced filtering
    - Bulk document operations and batch processing
    - Document metadata management and tagging

Document Processing:
    - Support for multiple file formats (PDF, DOCX, TXT, HTML)
    - Automatic text extraction and content normalization
    - Vector embedding generation for semantic search
    - Document chunking and segmentation for large files
    - Content quality validation and error handling

Search and Retrieval:
    - Vector similarity search with relevance scoring
    - Full-text search with keyword matching
    - Advanced filtering by metadata, date, and file type
    - Semantic search with natural language queries
    - Search result ranking and pagination

Performance Features:
    - Async document processing for responsiveness
    - Efficient batch operations for bulk uploads
    - Optimized vector search with PGVector integration
    - Progress tracking for long-running operations
    - Memory-efficient streaming for large files

Use Cases:
    - Knowledge base creation and management
    - Document search and discovery systems
    - Content analysis and information extraction
    - Bulk document migration and processing
    - Research and academic document management

Example Usage:
    ```bash
    # Upload and process documents
    ai-chatbot documents upload file.pdf --extract-text --generate-embeddings
    ai-chatbot documents batch-upload docs/ --recursive --filter "*.pdf"

    # Search and retrieve documents
    ai-chatbot documents search --query "machine learning" --limit 10
    ai-chatbot documents list --file-type pdf --page 1 --size 20

    # Document management
    ai-chatbot documents show doc_id --include-content
    ai-chatbot documents delete doc_id --confirm
    ai-chatbot documents update doc_id --title "New Title"
    ```
"""

from typing import Optional


from async_typer import AsyncTyper
from rich.console import Console
from typer import Argument, Option

from .base import (
    error_message,
    format_file_size,
    format_timestamp,
    get_sdk,
    info_message,
    success_message,
)

console = Console()

document_app = AsyncTyper(help="Document management commands", rich_markup_mode=None)


@document_app.async_command()
async def list(
    page: int = Option(1, "--page", "-p", help="Page number"),
    size: int = Option(20, "--size", "-s", help="Items per page"),
    file_type: Optional[str] = Option(None, "--file-type", help="Filter by file type"),
    status: Optional[str] = Option(
        None, "--status", help="Filter by processing status"
    ),
):
    """List all documents with filtering."""
    try:
        sdk = await get_sdk()
        resp = await sdk.documents.list(
            page=page, size=size, file_type=file_type, status=status
        )
        print("REAP", resp)
        if resp:
            from rich.table import Table

            table = Table(title=f"Documents")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("File Type", style="blue")
            table.add_column("Size", style="magenta")
            table.add_column("Status", style="yellow")
            table.add_column("Owner", style="green")
            table.add_column("Chunks", style="white")
            table.add_column("Uploaded", style="bright_black")
            for doc in resp:
                table.add_row(
                    str(doc.id)[:8] + "...",
                    doc.title,
                    doc.file_type,
                    format_file_size(doc.file_size),
                    doc.processing_status,
                    str(doc.owner_id)[:8] + "...",
                    str(doc.chunk_count),
                    format_timestamp(str(doc.created_at)),
                )
            console.print(table)
        else:
            info_message("No documents found.")
    except Exception as e:
        error_message(f"Failed to list documents: {str(e)}")
        raise SystemExit(1)


@document_app.async_command()
async def upload(
    file_path: str = Argument(..., help="Path to the document file"),
    title: Optional[str] = Option(None, "--title", help="Document title"),
):
    """Upload a new document for processing."""
    try:
        sdk = await get_sdk()
        import os

        if not os.path.exists(file_path):
            error_message(f"File not found: {file_path}")
            return
        with open(file_path, "rb") as f:
            resp = await sdk.documents.upload(
                f, title=title or os.path.basename(file_path)
            )
        if getattr(resp, "success", False) or getattr(resp, "document", None):
            doc = getattr(resp, "document", None)
            doc_id = str(doc.id) if doc else "N/A"
            success_message(f"Document uploaded successfully (ID: {doc_id})")
        else:
            error_message(getattr(resp, "message", "Failed to upload document"))
    except Exception as e:
        error_message(f"Failed to upload document: {str(e)}")
        raise SystemExit(1)


@document_app.async_command()
async def show(
    document_id: str = Argument(..., help="Document ID"),
):
    """Show document details."""
    try:
        sdk = await get_sdk()
        doc = await sdk.documents.get(str(document_id))
        if doc:
            from rich.panel import Panel

            details = (
                f"ID: [cyan]{doc.id}[/cyan]\n"
                f"Title: [white]{doc.title}[/white]\n"
                f"File: [magenta]{doc.filename}[/magenta]\n"
                f"Type: [blue]{doc.file_type}[/blue]\n"
                f"Size: [green]{format_file_size(doc.file_size)}[/green]\n"
                f"Status: [yellow]{doc.processing_status}[/yellow]\n"
                f"Owner: [cyan]{doc.owner_id}[/cyan]\n"
                f"Chunks: [white]{doc.chunk_count}[/white]\n"
                f"Uploaded: [bright_black]{format_timestamp(str(doc.created_at))}[/bright_black]"
            )
            panel = Panel(details, title="Document Details", border_style="magenta")
            console.print(panel)
    except Exception as e:
        error_message(f"Failed to get document details: {str(e)}")
        raise SystemExit(1)


@document_app.async_command()
async def status(
    document_id: str = Argument(..., help="Document ID"),
):
    """Show processing status for a document."""
    try:
        sdk = await get_sdk()
        status = await sdk.documents.status(str(document_id))
        if status:
            from rich.panel import Panel

            details = (
                f"Status: [yellow]{status.status}[/yellow]\n"
            )
            if not status.status == "pending":
                details += (
                    f"Progress: [green]{status.progress:.1%}[/green]\n"
                    f"Chunks: [white]{status.chunks_processed}/{status.total_chunks}[/white]\n"
                    f"Started: [magenta]{format_timestamp(str(status.started_at)) if status.started_at else 'N/A'}[/magenta]\n"
                    f"Completed: [magenta]{format_timestamp(str(status.completed_at)) if status.completed_at else 'N/A'}[/magenta]"
                )
            panel = Panel(details, title="Processing Status", border_style="blue")
            console.print(panel)
    except Exception as e:
        error_message(f"Failed to get document status: {str(e)}")
        raise SystemExit(1)


@document_app.async_command()
async def reprocess(
    document_id: str = Argument(..., help="Document ID"),
):
    """Reprocess a document."""
    try:
        sdk = await get_sdk()
        resp = await sdk.documents.reprocess(str(document_id))
        if getattr(resp, "success", False):
            success_message("Document reprocessing started.")
        else:
            error_message(getattr(resp, "message", "Failed to reprocess document"))
    except Exception as e:
        error_message(f"Failed to reprocess document: {str(e)}")
        raise SystemExit(1)


@document_app.async_command()
async def delete(
    document_id: str = Argument(..., help="Document ID"),
    force: bool = Option(False, "--force", help="Skip confirmation"),
):
    """Delete a document."""
    from .base import confirm_action

    try:
        if not force and not confirm_action(
            f"Are you sure you want to delete document '{document_id}'?"
        ):
            return
        sdk = await get_sdk()
        resp = await sdk.documents.delete(str(document_id))
        if getattr(resp, "success", False):
            success_message("Document deleted successfully.")
        else:
            error_message(getattr(resp, "message", "Failed to delete document"))
    except Exception as e:
        error_message(f"Failed to delete document: {str(e)}")
        raise SystemExit(1)
