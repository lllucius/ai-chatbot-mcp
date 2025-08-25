"""Document management commands for the AI Chatbot Platform CLI.

This module provides comprehensive document processing and management functionality
through async operations and the AI Chatbot SDK. It enables users to upload,
process, search, and manage documents with full support for various file formats,
text extraction, and vector embedding generation.
"""

import os
from typing import Optional

from async_typer import AsyncTyper
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Argument, Option

from cli.base import (
    APIError,
    confirm_action,
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
        response = await sdk.documents.list(
            page=page, size=size, file_type=file_type, status=status
        )
        documents = response.items
        pagination = response.pagination

        if documents:
            table = Table(title="Documents")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("File Type", style="blue")
            table.add_column("Size", style="magenta")
            table.add_column("Status", style="yellow")
            table.add_column("Owner", style="green")
            table.add_column("Chunks", style="white")
            table.add_column("Uploaded", style="bright_black")
            for doc in documents:
                table.add_row(
                    str(doc.id)[:8],
                    doc.title,
                    doc.file_type,
                    format_file_size(doc.file_size),
                    doc.status,
                    str(doc.owner_id)[:8],
                    str(doc.chunk_count),
                    format_timestamp(str(doc.created_at)),
                )
            console.print(table)
        else:
            info_message("No documents found.")
    except APIError as e:
        error_message(f"Failed to list documents: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to list documents: {str(e)}")


@document_app.async_command()
async def upload(
    file_path: str = Argument(..., help="Path to the document file"),
    title: Optional[str] = Option(None, "--title", help="Document title"),
):
    """Upload a new document for processing."""
    try:
        sdk = await get_sdk()
        if not os.path.exists(file_path):
            error_message(f"File not found: {file_path}")
            return
        with open(file_path, "rb") as f:
            resp = await sdk.documents.upload(
                f, title=title or os.path.basename(file_path)
            )
        print("RESP", resp)
        if getattr(resp, "success", False) or getattr(resp, "document", None):
            doc = getattr(resp, "document", None)
            doc_id = str(doc.id) if doc else "N/A"
            success_message(f"Document uploaded successfully (ID: {doc_id})")
        else:
            error_message(getattr(resp, "message", "Failed to upload document"))
    except APIError as e:
        error_message(f"Failed to upload document: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to upload document: {str(e)}")


@document_app.async_command()
async def show(
    document_id: str = Argument(..., help="Document ID"),
):
    """Show document details."""
    try:
        sdk = await get_sdk()
        doc = await sdk.documents.get(int(document_id))

        details = (
            f"ID: [cyan]{doc.id}[/cyan]\n"
            f"Title: [white]{doc.title}[/white]\n"
            f"File: [magenta]{doc.filename}[/magenta]\n"
            f"Type: [blue]{doc.file_type}[/blue]\n"
            f"Size: [green]{format_file_size(doc.file_size)}[/green]\n"
            f"Status: [yellow]{doc.status}[/yellow]\n"
            f"Owner: [cyan]{doc.owner_id}[/cyan]\n"
            f"Chunks: [white]{doc.chunk_count}[/white]\n"
            f"Uploaded: [bright_black]{format_timestamp(str(doc.created_at))}[/bright_black]"
        )
        panel = Panel(details, title="Document Details", border_style="magenta")
        console.print(panel)
    except APIError as e:
        error_message(f"Failed to get document: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get document: {str(e)}")


@document_app.async_command()
async def status(
    document_id: str = Argument(..., help="Document ID"),
):
    """Show processing status for a document."""
    try:
        sdk = await get_sdk()
        status = await sdk.documents.status(int(document_id))
        print("STATUS", status)
        print(type(status))
        print(dir(status))
        details = (
            f"Status: [yellow]{status.status}[/yellow]\n"
        )
        if status.status == "completed":
            details += (
                f"Progress: [green]{status.progress if status.progress else 'N/A'}[/green]\n"
                f"Chunks: [white]{status.chunk_count}[/white]\n"
                f"Started: [magenta]{format_timestamp(str(status.created_at)) if status.created_at else 'N/A'}[/magenta]\n"
    #            f"Completed: [magenta]{format_timestamp(str(status.updated_at)) if status.updated_at else 'N/A'}[/magenta]"
                f"Processing Time: [magenta]{format_timestamp(str(status.processing_time)) if status.processing_time else 'N/A'}[/magenta]\n"
                f"Message: [magenta]{status.error_message if status.error_message else 'N/A'}[/magenta]"
            )
        panel = Panel(details, title="Processing Status", border_style="blue")
        console.print(panel)
    except APIError as e:
        error_message(f"Failed to get document status: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get document status: {str(e)}")


@document_app.async_command()
async def reprocess(
    document_id: str = Argument(..., help="Document ID"),
):
    """Reprocess a document."""
    try:
        sdk = await get_sdk()
        await sdk.documents.reprocess(int(document_id))
        success_message("Document reprocessing started.")
    except APIError as e:
        error_message(f"Failed to reprocess document: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to reprocess document: {str(e)}")


@document_app.async_command()
async def delete(
    document_id: str = Argument(..., help="Document ID"),
    force: bool = Option(False, "--force", help="Skip confirmation"),
):
    """Delete a document."""

    try:
        if not force and not confirm_action(
            f"Are you sure you want to delete document '{document_id}'?"
        ):
            return
        sdk = await get_sdk()
        await sdk.documents.delete(int(document_id))
        success_message("Document deleted successfully.")
    except APIError as e:
        error_message(f"Failed to delete document: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to delete document: {str(e)}")
