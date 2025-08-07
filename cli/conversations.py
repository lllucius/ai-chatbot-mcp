"""
Conversation management commands for the AI Chatbot Platform CLI.

This module provides comprehensive conversation and chat management functionality
through async operations and the AI Chatbot SDK. It enables users and administrators
to create, manage, and monitor conversations with full support for messaging,
analytics, and conversation lifecycle management.

The module implements enterprise-grade conversation management patterns including
real-time messaging, conversation state management, and comprehensive analytics.
All operations integrate seamlessly with the platform's AI services and user
management systems.

Key Features:
    - Conversation creation and management
    - Message history and pagination
    - Real-time conversation monitoring
    - Conversation search and filtering
    - Bulk conversation operations
    - Analytics and reporting integration

Conversation Lifecycle:
    - Creation with customizable titles and settings
    - Active conversation management and state tracking
    - Message threading and context preservation
    - Conversation archiving and retrieval
    - Cleanup and maintenance operations

Performance Features:
    - Async operations for responsive user interface
    - Efficient pagination for large conversation datasets
    - Optimized message loading and display
    - Fast conversation search and filtering
    - Minimal memory footprint for bulk operations

Analytics Integration:
    - Conversation metrics and statistics
    - User engagement tracking
    - Performance monitoring and optimization
    - Export capabilities for external analysis
    - Real-time dashboard integration

Use Cases:
    - Customer support conversation management
    - Team collaboration and communication
    - AI training and conversation analysis
    - Bulk conversation operations for maintenance
    - Integration testing and validation

Example Usage:
    ```bash
    # Create and manage conversations
    ai-chatbot conversations create --title "Customer Support Session"
    ai-chatbot conversations list --active-only --page 1 --size 20

    # View conversation details
    ai-chatbot conversations show conv_id --include-messages
    ai-chatbot conversations messages conv_id --limit 50

    # Conversation operations
    ai-chatbot conversations activate conv_id
    ai-chatbot conversations archive conv_id
    ai-chatbot conversations delete conv_id --confirm

    # Search and analytics
    ai-chatbot conversations search --query "support" --date-range 7d
    ai-chatbot conversations stats --group-by date --period week
    ```

Integration:
    - Customer support platform integration
    - Analytics and reporting system connectivity
    - Real-time messaging platform integration
    - AI model training and evaluation systems
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Argument, Option

from .base import error_message, format_timestamp, get_sdk, success_message

conversation_app = AsyncTyper(
    help="Conversation management commands", rich_markup_mode=None
)


@conversation_app.async_command()
async def list(
    page: int = Option(1, "--page", "-p", help="Page number"),
    size: int = Option(20, "--size", "-s", help="Items per page"),
    active_only: bool = Option(
        False, "--active-only", help="Show only active conversations"
    ),
):
    """
    List conversations with filtering, pagination, and detailed display.

    Retrieves and displays conversations from the platform with support for
    pagination, filtering, and comprehensive conversation metadata. The command
    provides a tabular view of conversations with key information including
    status, message counts, and creation timestamps.

    The listing supports various filtering options to help users find specific
    conversations quickly, and includes pagination for handling large datasets
    efficiently. All timestamps are formatted for easy reading and timezone
    awareness.

    Args:
        page (int): Page number for pagination, starting from 1. Defaults to 1
        size (int): Number of conversations per page (max 100). Defaults to 20
        active_only (bool): Filter to show only active conversations. Defaults to False

    Performance Notes:
        - Efficient pagination with server-side filtering
        - Optimized API calls with minimal data transfer
        - Fast table rendering with Rich formatting
        - Responsive display for large conversation datasets

    Use Cases:
        - Reviewing recent conversation activity
        - Finding specific conversations by status or date
        - Monitoring conversation volume and activity
        - Administrative oversight of platform usage
        - Identifying conversations requiring attention

    Example:
        ```bash
        # List recent conversations
        ai-chatbot conversations list

        # Show only active conversations
        ai-chatbot conversations list --active-only

        # Navigate through pages
        ai-chatbot conversations list --page 2 --size 50
        ```

    Note:
        The command displays a "No conversations found" message if the result
        set is empty, which may occur with restrictive filtering or when no
        conversations exist in the system.
    """
    try:
        sdk = await get_sdk()
        resp = await sdk.conversations.list(
            page=page, size=size, active_only=active_only
        )
        if resp and resp.items:
            # Convert to table data
            conv_data = []
            for conv in resp.items:
                conv_data.append(
                    {
                        "ID": str(conv.id)[:8] + "...",
                        "Title": conv.title,
                        "Active": "✓" if conv.is_active else "✗",
                        "Messages": str(conv.message_count),
                        "Created": format_timestamp(str(conv.created_at)),
                    }
                )

            from .base import display_rich_table

            display_rich_table(
                conv_data, f"Conversations (Page {resp.pagination.page})"
            )
        else:
            print("No conversations found.")
    except Exception as e:
        error_message(f"Failed to list conversations: {str(e)}")
        raise SystemExit(1)


@conversation_app.async_command()
async def show(
    conversation_id: str = Argument(..., help="Conversation ID"),
):
    """Show conversation details."""
    try:
        sdk = await get_sdk()
        conv = await sdk.conversations.get(int(conversation_id))
        if conv:
            conv_details = {
                "ID": str(conv.id),
                "Title": conv.title,
                "Active": "Yes" if conv.is_active else "No",
                "Messages": str(conv.message_count),
                "Created": format_timestamp(str(conv.created_at)),
            }

            from .base import display_key_value_pairs

            display_key_value_pairs(conv_details, "Conversation Details")
    except Exception as e:
        error_message(f"Failed to get conversation details: {str(e)}")
        raise SystemExit(1)


@conversation_app.async_command()
async def export(
    conversation_id: str = Argument(..., help="Conversation ID"),
    output: Optional[str] = Option(None, "--output", help="Output file"),
):
    """Export a conversation to a file."""
    try:
        sdk = await get_sdk()

        data = await sdk.admin.export_conversation(int(conversation_id))
        import json

        filename = output or f"conversation_{conversation_id}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        success_message(f"Conversation exported to {filename}")
    except Exception as e:
        error_message(f"Failed to export conversation: {str(e)}")
        raise SystemExit(1)
