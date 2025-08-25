"""Conversation management commands for the AI Chatbot Platform CLI.

This module provides comprehensive conversation and chat management functionality
through async operations and the AI Chatbot SDK for conversation lifecycle management,
messaging support, and analytics integration.
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Argument, Option

from cli.base import APIError, error_message, format_timestamp, get_sdk, success_message

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
    """List conversations with filtering, pagination, and detailed display.

    Retrieves and displays conversations from the platform with support for
    pagination, filtering, and comprehensive conversation metadata.
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
                        "ID": str(conv.id)[:8],
                        "Title": conv.title,
                        "Active": "✓" if conv.is_active else "✗",
                        "Messages": str(conv.message_count),
                        "Created": format_timestamp(str(conv.created_at)),
                    }
                )

            from cli.base import display_rich_table

            display_rich_table(
                conv_data, f"Conversations (Page {resp.pagination.page})"
            )
        else:
            print("No conversations found.")
    except APIError as e:
        error_message(f"Failed to list conversations: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to list conversations: {str(e)}")


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

            from cli.base import display_key_value_pairs

            display_key_value_pairs(conv_details, "Conversation Details")
    except APIError as e:
        error_message(f"Failed to get conversation details: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get conversation details: {str(e)}")


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
    except APIError as e:
        error_message(f"Failed to export conversation: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to export conversation: {str(e)}")
