"""
Document management CLI commands.

Provides comprehensive document management functionality including:
- Document upload and processing
- Document search and retrieval
- Processing status monitoring
- Document statistics and analytics
- Bulk operations
"""

import mimetypes
import os
from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.progress import track
from rich.table import Table
from sqlalchemy import and_, desc, func, or_, select

from ..database import AsyncSessionLocal
from ..models.document import Document, DocumentChunk, FileStatus
from ..models.user import User
from ..services.document import DocumentService
from .base import (async_command, console, error_message, format_size, format_timestamp,
                   info_message, progress_context, success_message, warning_message)


def get_content_type(filename: str) -> str:
    """Get MIME content type for a file based on its extension."""
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


# Create the document management app
document_app = typer.Typer(help="Document management commands")


@document_app.command()
def upload(
    file_path: str = typer.Argument(..., help="Path to the file to upload"),
    title: str = typer.Option(None, "--title", "-t", help="Document title (defaults to filename)"),
    username: str = typer.Option(
        None, "--user", "-u", help="Username of document owner (defaults to system)"
    ),
    process_now: bool = typer.Option(False, "--process", "-p", help="Process document immediately"),
):
    """Upload a document for processing."""

    @async_command
    async def _upload_document():
        # Validate file exists
        if not os.path.exists(file_path):
            error_message(f"File not found: {file_path}")
            return

        file_path_obj = Path(file_path)
        if not title:
            title_to_use = file_path_obj.stem
        else:
            title_to_use = title

        async with AsyncSessionLocal() as db:
            try:
                # Get or create system user if no username provided
                user_id = None
                if username:
                    user = await db.scalar(select(User).where(User.username == username))
                    if not user:
                        error_message(f"User '{username}' not found")
                        return
                    user_id = user.id
                else:
                    # Look for system user or create one
                    system_user = await db.scalar(select(User).where(User.username == "system"))
                    if not system_user:
                        # Create a system user
                        from ..services.user import UserService

                        user_service = UserService(db)
                        system_user = await user_service.create_user(
                            username="system",
                            email="system@localhost",
                            password="system",  # Will be hashed
                            full_name="System User",
                            is_superuser=True,
                        )
                        info_message("Created system user for document ownership")
                    user_id = system_user.id

                DocumentService(db)

                # Read file content
                with open(file_path, "rb") as f:
                    file_content = f.read()

                file_size = len(file_content)

                # Create document
                document = Document(
                    title=title_to_use,
                    filename=file_path_obj.name,
                    content_type=get_content_type(file_path_obj.name),
                    file_size=file_size,
                    status=FileStatus.PENDING,
                    owner_id=user_id,
                    metainfo={"uploaded_via": "cli", "original_path": str(file_path)},
                )

                db.add(document)
                await db.commit()
                await db.refresh(document)

                success_message(f"Document '{title_to_use}' uploaded successfully")

                # Show document info
                table = Table(title="Uploaded Document")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("ID", str(document.id))
                table.add_row("Title", document.title)
                table.add_row("Filename", document.filename)
                table.add_row("Size", format_size(document.file_size))
                table.add_row("Type", document.content_type)
                table.add_row("Status", document.status.value)
                table.add_row("Owner", username or "System")
                table.add_row("Created", format_timestamp(document.created_at))

                console.print(table)

                if process_now:
                    info_message("Starting document processing...")
                    # Here you would trigger the background processor
                    # For now, just update status
                    document.status = FileStatus.PROCESSING
                    await db.commit()
                    info_message(f"Document queued for processing (ID: {document.id})")

            except Exception as e:
                error_message(f"Failed to upload document: {e}")

    _upload_document()


@document_app.command()
def list(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of documents to show"),
    status: str = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (pending, processing, completed, failed)",
    ),
    username: str = typer.Option(None, "--user", "-u", help="Filter by owner username"),
    search: str = typer.Option(None, "--search", help="Search in title and filename"),
    sort_by: str = typer.Option(
        "created", "--sort", help="Sort by: id, title, size, status, created"
    ),
):
    """List documents with filtering options."""

    @async_command
    async def _list_documents():
        async with AsyncSessionLocal() as db:
            try:
                query = select(Document).join(User, isouter=True)

                # Apply filters
                if status:
                    try:
                        status_enum = FileStatus(status.upper())
                        query = query.where(Document.status == status_enum)
                    except ValueError:
                        error_message(f"Invalid status: {status}")
                        return

                if username:
                    user = await db.scalar(select(User).where(User.username == username))
                    if not user:
                        error_message(f"User '{username}' not found")
                        return
                    query = query.where(Document.owner_id == user.id)

                if search:
                    search_pattern = f"%{search.lower()}%"
                    query = query.where(
                        or_(
                            func.lower(Document.title).like(search_pattern),
                            func.lower(Document.filename).like(search_pattern),
                        )
                    )

                # Apply sorting
                if sort_by == "id":
                    query = query.order_by(Document.id)
                elif sort_by == "title":
                    query = query.order_by(Document.title)
                elif sort_by == "size":
                    query = query.order_by(desc(Document.file_size))
                elif sort_by == "status":
                    query = query.order_by(Document.status)
                elif sort_by == "created":
                    query = query.order_by(desc(Document.created_at))

                query = query.limit(limit)
                result = await db.execute(query)
                documents = result.scalars().all()

                if not documents:
                    warning_message("No documents found matching criteria")
                    return

                # Create table
                table = Table(title=f"Documents ({len(documents)} found)")
                table.add_column("ID", style="cyan", width=41)  # Width for full UUID
                table.add_column("Title", style="green", width=20)
                table.add_column("Filename", style="blue", width=15)
                table.add_column("Size", width=14)
                table.add_column("Status", width=10)
                table.add_column("Owner", width=10)
                table.add_column("Created", width=12)

                # Get all user IDs for owner lookup
                user_ids = [doc.owner_id for doc in documents if doc.owner_id]
                users = {}
                if user_ids:
                    user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
                    users = {user.id: user.username for user in user_result.scalars().all()}

                for doc in documents:
                    status_icon = {
                        FileStatus.PENDING: "⏳",
                        FileStatus.PROCESSING: "⚙️",
                        FileStatus.COMPLETED: "✅",
                        FileStatus.FAILED: "❌",
                    }.get(doc.status, "❓")

                    owner_name = users.get(doc.owner_id, "System") if doc.owner_id else "System"

                    table.add_row(
                        str(doc.id),
                        doc.title[:18] + "..." if len(doc.title) > 20 else doc.title,
                        (doc.filename[:13] + "..." if len(doc.filename) > 15 else doc.filename),
                        format_size(doc.file_size),
                        f"{status_icon} {doc.status.value.title()}",
                        owner_name,
                        doc.created_at.strftime("%Y-%m-%d"),
                    )

                console.print(table)

            except Exception as e:
                error_message(f"Failed to list documents: {e}")

    _list_documents()


@document_app.command()
def show(
    document_id: str = typer.Argument(..., help="Document ID (UUID) to show details for"),
):
    """Show detailed information about a specific document."""

    @async_command
    async def _show_document():
        async with AsyncSessionLocal() as db:
            try:
                # Validate UUID format
                try:
                    import uuid

                    uuid.UUID(document_id)
                except ValueError:
                    error_message(f"Invalid UUID format: {document_id}")
                    return

                # Get document with owner info
                result = await db.execute(
                    select(Document, User)
                    .join(User, isouter=True)
                    .where(Document.id == document_id)
                )
                row = result.first()

                if not row:
                    error_message(f"Document with ID {document_id} not found")
                    return

                document, owner = row

                # Get chunk statistics
                chunk_count = await db.scalar(
                    select(func.count(DocumentChunk.id)).where(
                        DocumentChunk.document_id == document_id
                    )
                )

                # Document details table
                table = Table(title=f"Document Details: {document.title}")
                table.add_column("Field", style="cyan", width=20)
                table.add_column("Value", style="green")

                table.add_row("ID", str(document.id))
                table.add_row("Title", document.title)
                table.add_row("Filename", document.filename)
                table.add_row("Content Type", document.content_type)
                table.add_row("Size", format_size(document.file_size))
                table.add_row("Status", f"{document.status.value.title()}")
                table.add_row("Owner", owner.username if owner else "System")
                table.add_row("Chunks", str(chunk_count or 0))
                table.add_row("Created", format_timestamp(document.created_at))
                table.add_row("Updated", format_timestamp(document.updated_at))

                if document.metainfo:
                    table.add_row("Metadata", str(document.metainfo))

                console.print(table)

                # Show recent chunks if any
                if chunk_count and chunk_count > 0:
                    chunks_result = await db.execute(
                        select(DocumentChunk)
                        .where(DocumentChunk.document_id == document_id)
                        .order_by(DocumentChunk.chunk_index)
                        .limit(5)
                    )
                    chunks = chunks_result.scalars().all()

                    chunk_table = Table(title="Document Chunks (first 5)")
                    chunk_table.add_column("Index", width=8)
                    chunk_table.add_column("Content Preview", width=60)
                    chunk_table.add_column("Tokens", width=10)

                    for chunk in chunks:
                        preview = (
                            chunk.content[:57] + "..." if len(chunk.content) > 60 else chunk.content
                        )
                        chunk_table.add_row(
                            str(chunk.chunk_index), preview, str(chunk.token_count or 0)
                        )

                    console.print(chunk_table)

            except Exception as e:
                error_message(f"Failed to show document details: {e}")

    _show_document()


@document_app.command()
def delete(
    document_id: str = typer.Argument(..., help="Document ID (UUID) to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a document and all its chunks."""

    @async_command
    async def _delete_document():
        async with AsyncSessionLocal() as db:
            try:
                # Validate UUID format
                try:
                    import uuid

                    uuid.UUID(document_id)
                except ValueError:
                    error_message(f"Invalid UUID format: {document_id}")
                    return

                document = await db.scalar(select(Document).where(Document.id == document_id))

                if not document:
                    error_message(f"Document with ID {document_id} not found")
                    return

                # Get chunk count
                chunk_count = await db.scalar(
                    select(func.count(DocumentChunk.id)).where(
                        DocumentChunk.document_id == document_id
                    )
                )

                console.print("\n[bold red]This will permanently delete:[/bold red]")
                console.print(f"  • Document: {document.title}")
                console.print(f"  • File: {document.filename}")
                console.print(f"  • Chunks: {chunk_count or 0}")
                console.print()

                if not force:
                    from rich.prompt import Confirm

                    if not Confirm.ask("Are you sure you want to delete this document?"):
                        warning_message("Deletion cancelled")
                        return

                # Delete chunks first
                if chunk_count:
                    await db.execute(
                        DocumentChunk.__table__.delete().where(
                            DocumentChunk.document_id == document_id
                        )
                    )

                # Delete document
                await db.delete(document)
                await db.commit()

                success_message(
                    f"Document '{document.title}' and {chunk_count or 0} chunks deleted successfully"
                )

            except Exception as e:
                error_message(f"Failed to delete document: {e}")

    _delete_document()


@document_app.command()
def reprocess(
    document_id: str = typer.Argument(..., help="Document ID (UUID) to reprocess"),
):
    """Reprocess a document (re-extract text and create new chunks)."""

    @async_command
    async def _reprocess_document():
        async with AsyncSessionLocal() as db:
            try:
                # Validate UUID format
                try:
                    import uuid

                    uuid.UUID(document_id)
                except ValueError:
                    error_message(f"Invalid UUID format: {document_id}")
                    return

                document = await db.scalar(select(Document).where(Document.id == document_id))

                if not document:
                    error_message(f"Document with ID {document_id} not found")
                    return

                info_message(f"Reprocessing document: {document.title}")

                # Reset status and clear existing chunks
                document.status = FileStatus.PENDING
                await db.execute(
                    DocumentChunk.__table__.delete().where(DocumentChunk.document_id == document_id)
                )
                await db.commit()

                # Queue for processing
                document.status = FileStatus.PROCESSING
                await db.commit()

                success_message(f"Document '{document.title}' queued for reprocessing")
                info_message(f"Monitor status with: manage documents show {document_id}")

            except Exception as e:
                error_message(f"Failed to reprocess document: {e}")

    _reprocess_document()


@document_app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    threshold: float = typer.Option(
        0.7, "--threshold", "-t", help="Similarity threshold (0.0-1.0)"
    ),
):
    """Search documents using semantic similarity."""

    @async_command
    async def _search_documents():
        async with AsyncSessionLocal() as db:
            try:
                from ..schemas.document import DocumentSearchRequest
                from ..services.search import SearchService

                search_service = SearchService(db)

                # Create search request - try vector first, fallback to text search
                search_request = DocumentSearchRequest(
                    query=query, algorithm="vector", limit=limit, threshold=threshold
                )

                # Use system user ID for search (since CLI doesn't have user context)
                system_user = await db.scalar(select(User).where(User.username == "system"))
                if not system_user:
                    # Create system user if not exists
                    from ..services.user import UserService

                    user_service = UserService(db)
                    system_user = await user_service.create_user(
                        username="system",
                        email="system@localhost",
                        password="system",
                        full_name="System User",
                        is_superuser=True,
                    )

                async with progress_context("Searching documents..."):
                    try:
                        # Perform search with vector first
                        results = await search_service.search_documents(
                            request=search_request, user_id=system_user.id
                        )
                    except Exception as e:
                        # If vector search fails, try text search as fallback
                        warning_message(f"Vector search failed: {e}")
                        info_message("Falling back to text search...")
                        
                        search_request = DocumentSearchRequest(
                            query=query, algorithm="text", limit=limit, threshold=0.0
                        )
                        results = await search_service.search_documents(
                            request=search_request, user_id=system_user.id
                        )

                if not results:
                    warning_message(
                        f"No documents found matching '{query}' with threshold {threshold}"
                    )
                    return

                # Create results table
                table = Table(title=f"Search Results for: '{query}'")
                table.add_column("Score", style="cyan", width=8)
                table.add_column("Document", style="green", width=30)
                table.add_column("Chunk Preview", style="blue", width=60)
                table.add_column("Doc ID", width=36)

                for result in results:
                    # Truncate content for display
                    content_preview = (
                        result.content[:57] + "..." if len(result.content) > 60 else result.content
                    )
                    content_preview = content_preview.replace("\n", " ")

                    score = f"{result.similarity_score:.3f}" if result.similarity_score else "N/A"
                    doc_title = result.document_title or "Unknown"

                    table.add_row(
                        score,
                        doc_title[:27] + "..." if len(doc_title) > 30 else doc_title,
                        content_preview,
                        str(result.document_id),
                    )

                console.print(table)

            except Exception as e:
                error_message(f"Search failed: {e}")

    _search_documents()


@document_app.command()
def stats():
    """Display document statistics and summary."""

    @async_command
    async def _document_stats():
        async with AsyncSessionLocal() as db:
            try:
                # Basic document counts
                total_docs = await db.scalar(select(func.count(Document.id)))

                # Status breakdown
                status_counts = {}
                for status in FileStatus:
                    count = await db.scalar(
                        select(func.count(Document.id)).where(Document.status == status)
                    )
                    status_counts[status] = count or 0

                # Size statistics
                total_size = await db.scalar(select(func.sum(Document.file_size)))
                avg_size = await db.scalar(select(func.avg(Document.file_size)))

                # Recent uploads
                last_7_days = datetime.now() - timedelta(days=7)
                recent_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.created_at >= last_7_days)
                )

                # Chunk statistics
                total_chunks = await db.scalar(select(func.count(DocumentChunk.id)))
                avg_chunks_per_doc = float(total_chunks or 0) / max(total_docs or 1, 1) if total_docs else 0

                # Create statistics table
                table = Table(title="Document Statistics")
                table.add_column("Metric", style="cyan", width=25)
                table.add_column("Count/Value", style="green", width=15)
                table.add_column("Details", style="yellow")

                table.add_row("Total Documents", str(total_docs or 0), "")
                table.add_row(
                    "Total Size",
                    format_size(total_size or 0),
                    f"Avg: {format_size(avg_size or 0)}",
                )
                table.add_row(
                    "Total Chunks",
                    str(total_chunks or 0),
                    f"Avg per doc: {avg_chunks_per_doc:.1f}",
                )
                table.add_row(
                    "Recent (7 days)",
                    str(recent_docs or 0),
                    f"{float(recent_docs or 0) / max(total_docs or 1, 1) * 100:.1f}% of total",
                )

                # Status breakdown
                table.add_row("", "", "")  # Separator
                for status, count in status_counts.items():
                    status_icon = {
                        FileStatus.PENDING: "⏳",
                        FileStatus.PROCESSING: "⚙️",
                        FileStatus.COMPLETED: "✅",
                        FileStatus.FAILED: "❌",
                    }.get(status, "❓")

                    percentage = (
                        f"{float(count) / max(total_docs or 1, 1) * 100:.1f}%" if total_docs else "0%"
                    )
                    table.add_row(f"{status_icon} {status.value.title()}", str(count), percentage)

                console.print(table)

            except Exception as e:
                error_message(f"Failed to get document statistics: {e}")

    _document_stats()


@document_app.command()
def cleanup(
    status: str = typer.Option("failed", "--status", "-s", help="Status of documents to clean up"),
    older_than: int = typer.Option(30, "--older-than", help="Days old to consider for cleanup"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clean up old or failed documents."""

    @async_command
    async def _cleanup_documents():
        async with AsyncSessionLocal() as db:
            try:
                # Validate status
                try:
                    status_enum = FileStatus(status.lower())
                except ValueError:
                    valid_statuses = [s.value for s in FileStatus]
                    error_message(
                        f"Invalid status: {status}. Valid options: {', '.join(valid_statuses)}"
                    )
                    return

                # Find documents to clean up
                cutoff_date = datetime.now() - timedelta(days=older_than)
                query = select(Document).where(
                    and_(
                        Document.status == status_enum,
                        Document.created_at < cutoff_date,
                    )
                )

                result = await db.execute(query)
                documents = result.scalars().all()

                if not documents:
                    info_message(f"No {status} documents older than {older_than} days found")
                    return

                console.print(
                    f"\n[bold yellow]Found {len(documents)} {status} documents to clean up:[/bold yellow]"
                )
                for doc in documents[:10]:  # Show first 10
                    console.print(f"  • {doc.title} (ID: {doc.id}, Size: {format_size(doc.file_size)})")

                if len(documents) > 10:
                    console.print(f"  ... and {len(documents) - 10} more")

                if not force:
                    from rich.prompt import Confirm

                    if not Confirm.ask(f"Delete these {len(documents)} documents?"):
                        warning_message("Cleanup cancelled")
                        return

                # Delete documents and their chunks
                deleted_count = 0
                for doc in track(documents, description="Cleaning up..."):
                    try:
                        # Delete chunks
                        await db.execute(
                            DocumentChunk.__table__.delete().where(
                                DocumentChunk.document_id == doc.id
                            )
                        )
                        # Delete document
                        await db.delete(doc)
                        deleted_count += 1
                    except Exception as e:
                        error_message(f"Failed to delete document {doc.id}: {e}")

                await db.commit()
                success_message(f"Cleaned up {deleted_count} documents")

            except Exception as e:
                error_message(f"Cleanup failed: {e}")

    _cleanup_documents()
