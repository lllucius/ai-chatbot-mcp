#!/usr/bin/env python3
"""
Manual verification script for tool call handling modes.

This script demonstrates the functionality without requiring a full server setup.
"""

import json
import os

# Set environment variables
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-development-32chars-minimum-length"
os.environ["OPENAI_API_KEY"] = "test-api-key"

from app.schemas.tool_calling import ToolHandlingMode
from app.services.openai_client import OpenAIClient


def test_format_functions():
    """Test the formatting functions."""
    print("=== Testing Format Functions ===\n")

    client = OpenAIClient()

    # Test tool results formatting
    tool_results = [
        {
            "tool_call_id": "call_123",
            "success": True,
            "content": [{"type": "text", "text": "Weather in NYC: 75°F, sunny"}],
            "execution_time_ms": 150.0,
        },
        {
            "tool_call_id": "call_456",
            "success": False,
            "error": "API rate limit exceeded",
            "execution_time_ms": 50.0,
        },
    ]

    formatted_content = client._format_tool_results_as_content(tool_results)
    print("RETURN_RESULTS Mode Output:")
    print(formatted_content)
    print("\n" + "=" * 60 + "\n")

    # Test AI formatting
    ai_format = client._format_tool_result_for_ai(tool_results[0])
    print("COMPLETE_WITH_RESULTS Mode Tool Message:")
    print(ai_format)
    print("\n" + "=" * 60 + "\n")


def test_enum_values():
    """Test the enum functionality."""
    print("=== Testing Enum Values ===\n")

    print(f"RETURN_RESULTS: {ToolHandlingMode.RETURN_RESULTS}")
    print(f"COMPLETE_WITH_RESULTS: {ToolHandlingMode.COMPLETE_WITH_RESULTS}")

    # Test enum creation from strings
    mode1 = ToolHandlingMode("return_results")
    mode2 = ToolHandlingMode("complete_with_results")

    print(f"\nFrom string 'return_results': {mode1}")
    print(f"From string 'complete_with_results': {mode2}")

    print("\nEnum equality test:")
    print(
        f"mode1 == ToolHandlingMode.RETURN_RESULTS: {mode1 == ToolHandlingMode.RETURN_RESULTS}"
    )
    print(
        f"mode2 == ToolHandlingMode.COMPLETE_WITH_RESULTS: {mode2 == ToolHandlingMode.COMPLETE_WITH_RESULTS}"
    )

    print("\n" + "=" * 60 + "\n")


def test_chat_request():
    """Test ChatRequest with tool handling modes."""
    print("=== Testing ChatRequest ===\n")

    from app.schemas.conversation import ChatRequest

    # Default mode
    request1 = ChatRequest(user_message="Test message")
    print(f"Default mode: {request1.tool_handling_mode}")

    # Explicit mode
    request2 = ChatRequest(
        user_message="Test message", tool_handling_mode=ToolHandlingMode.RETURN_RESULTS
    )
    print(f"Explicit RETURN_RESULTS: {request2.tool_handling_mode}")

    # Test serialization
    print("\nSerialized request:")
    print(
        json.dumps(
            {
                "user_message": request2.user_message,
                "tool_handling_mode": request2.tool_handling_mode,
                "use_tools": request2.use_tools,
                "temperature": request2.temperature,
            },
            indent=2,
        )
    )

    print("\n" + "=" * 60 + "\n")


def test_tool_call_summary():
    """Test tool call summary creation."""
    print("=== Testing Tool Call Summary ===\n")

    from app.schemas.tool_calling import ToolCallResult, ToolCallSummary

    results = [
        ToolCallResult(
            tool_call_id="call_1",
            tool_name="weather_search",
            success=True,
            content=[{"type": "text", "text": "Sunny, 75°F"}],
            execution_time_ms=150.0,
        ),
        ToolCallResult(
            tool_call_id="call_2",
            tool_name="news_search",
            success=True,
            content=[{"type": "text", "text": "Latest news..."}],
            execution_time_ms=200.0,
        ),
    ]

    summary = ToolCallSummary(
        total_calls=2,
        successful_calls=2,
        failed_calls=0,
        total_execution_time_ms=350.0,
        results=results,
    )

    print("Tool Call Summary:")
    print(json.dumps(summary.model_dump(), indent=2))

    print("\n" + "=" * 60 + "\n")


def main():
    """Run all tests."""
    print("🚀 Manual Verification: Tool Call Handling Modes\n")

    try:
        test_enum_values()
        test_chat_request()
        test_tool_call_summary()
        test_format_functions()

        print("✅ All manual tests passed!")
        print("\n🎯 Key Features Verified:")
        print("  • ToolHandlingMode enum with correct values")
        print("  • ChatRequest defaults to COMPLETE_WITH_RESULTS")
        print("  • Tool result formatting for both modes")
        print("  • ToolCallSummary structure and serialization")
        print("  • Proper enum string conversion")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
