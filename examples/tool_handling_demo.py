#!/usr/bin/env python3
"""
Example script demonstrating the new tool call handling modes.

This script shows how to use both RETURN_RESULTS and COMPLETE_WITH_RESULTS modes
for handling tool call results in the AI chatbot.

Generated on: 2025-01-20 21:00:00 UTC
Current User: assistant
"""

import asyncio
import json
import os
from typing import Dict, Any

# Set environment variables for development
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-development-32chars-minimum-length"
os.environ["OPENAI_API_KEY"] = "test-api-key"

from app.schemas.conversation import ChatRequest
from app.schemas.tool_calling import ToolHandlingMode


def print_separator(title: str):
    """Print a visual separator with title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


async def demonstrate_tool_handling_modes():
    """Demonstrate the different tool handling modes."""
    
    print_separator("Tool Call Handling Modes Demo")
    
    # Example 1: RETURN_RESULTS mode
    print_separator("Mode 1: RETURN_RESULTS")
    print("This mode returns the raw tool call results as the chat completion content.")
    print("Use this when you want to see exactly what tools were called and their results.")
    
    request_return_results = ChatRequest(
        user_message="Search for information about machine learning and summarize it",
        tool_handling_mode=ToolHandlingMode.RETURN_RESULTS,
        use_tools=True,
        use_rag=False
    )
    
    print("\nChatRequest configuration:")
    print(json.dumps({
        "user_message": request_return_results.user_message,
        "tool_handling_mode": request_return_results.tool_handling_mode,
        "use_tools": request_return_results.use_tools,
        "use_rag": request_return_results.use_rag
    }, indent=2))
    
    print("\nExpected behavior:")
    print("- OpenAI determines which tools to call")
    print("- Tools are executed by the unified tool executor")
    print("- Results are formatted as markdown content and returned")
    print("- No further OpenAI completion is made")
    print("- User sees detailed tool execution results")
    
    # Example 2: COMPLETE_WITH_RESULTS mode
    print_separator("Mode 2: COMPLETE_WITH_RESULTS (Default)")
    print("This mode feeds tool results back to OpenAI for a final completion.")
    print("Use this for normal conversational AI where tools enhance the response.")
    
    request_complete_with_results = ChatRequest(
        user_message="Search for information about machine learning and summarize it",
        tool_handling_mode=ToolHandlingMode.COMPLETE_WITH_RESULTS,
        use_tools=True,
        use_rag=False
    )
    
    print("\nChatRequest configuration:")
    print(json.dumps({
        "user_message": request_complete_with_results.user_message,
        "tool_handling_mode": request_complete_with_results.tool_handling_mode,
        "use_tools": request_complete_with_results.use_tools,
        "use_rag": request_complete_with_results.use_rag
    }, indent=2))
    
    print("\nExpected behavior:")
    print("- OpenAI determines which tools to call")
    print("- Tools are executed by the unified tool executor")
    print("- Tool results are sent back to OpenAI as 'tool' messages")
    print("- OpenAI generates a final response incorporating the tool results")
    print("- User sees a natural language response informed by tool results")
    
    # Example 3: API Usage
    print_separator("API Usage Examples")
    
    print("POST /api/v1/conversations/chat")
    print("\nExample 1 - Return tool results directly:")
    example1 = {
        "user_message": "What's the weather in New York?",
        "tool_handling_mode": "return_results",
        "use_tools": True
    }
    print(json.dumps(example1, indent=2))
    
    print("\nExample 2 - Complete with tool results (default):")
    example2 = {
        "user_message": "What's the weather in New York?",
        "tool_handling_mode": "complete_with_results",
        "use_tools": True
    }
    print(json.dumps(example2, indent=2))
    
    print("\nExample 3 - Using default mode (backwards compatible):")
    example3 = {
        "user_message": "What's the weather in New York?",
        "use_tools": True
    }
    print(json.dumps(example3, indent=2))
    print("(Defaults to 'complete_with_results' mode)")
    
    # Example response structures
    print_separator("Response Structure Comparison")
    
    print("RETURN_RESULTS mode response:")
    return_results_response = {
        "success": True,
        "message": "Chat response generated successfully",
        "ai_message": {
            "id": "msg-123",
            "role": "assistant",
            "content": "# Tool Execution Results\\n\\n## Tool Call 1: weather_search\\n✅ **Status**: Success\\n**Result**:\\n```\\nCurrent weather in New York: 72°F, Partly cloudy\\n```\\n**Execution Time**: 245.67ms\\n",
            "created_at": "2025-01-20T21:00:00Z"
        },
        "tool_call_summary": {
            "total_calls": 1,
            "successful_calls": 1,
            "failed_calls": 0,
            "total_execution_time_ms": 245.67,
            "results": [
                {
                    "tool_call_id": "call_123",
                    "tool_name": "weather_search",
                    "success": True,
                    "content": [{"type": "text", "text": "Current weather in New York: 72°F, Partly cloudy"}],
                    "execution_time_ms": 245.67
                }
            ]
        },
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 25,
            "total_tokens": 175
        }
    }
    print(json.dumps(return_results_response, indent=2))
    
    print("\n" + "-"*60 + "\n")
    
    print("COMPLETE_WITH_RESULTS mode response:")
    complete_with_results_response = {
        "success": True,
        "message": "Chat response generated successfully",
        "ai_message": {
            "id": "msg-124",
            "role": "assistant",
            "content": "The current weather in New York is 72°F with partly cloudy skies. It's a pleasant day with comfortable temperatures!",
            "created_at": "2025-01-20T21:00:00Z"
        },
        "tool_call_summary": {
            "total_calls": 1,
            "successful_calls": 1,
            "failed_calls": 0,
            "total_execution_time_ms": 245.67,
            "results": [
                {
                    "tool_call_id": "call_123",
                    "tool_name": "weather_search",
                    "success": True,
                    "content": [{"type": "text", "text": "Current weather in New York: 72°F, Partly cloudy"}],
                    "execution_time_ms": 245.67
                }
            ]
        },
        "usage": {
            "prompt_tokens": 220,
            "completion_tokens": 65,
            "total_tokens": 285
        }
    }
    print(json.dumps(complete_with_results_response, indent=2))
    
    print_separator("Use Case Recommendations")
    
    print("📋 RETURN_RESULTS mode is ideal for:")
    print("  • Debugging tool execution")
    print("  • Building tool testing interfaces")
    print("  • Creating tool execution dashboards")
    print("  • Systems where raw tool data is needed")
    print("  • Integration scenarios where tools provide structured data")
    
    print("\n🤖 COMPLETE_WITH_RESULTS mode is ideal for:")
    print("  • Normal conversational AI experiences")
    print("  • When you want natural language responses")
    print("  • User-facing chatbot interfaces")
    print("  • When tools should enhance but not replace AI responses")
    print("  • Most production chat scenarios")
    
    print_separator("Implementation Summary")
    
    print("✅ New Features Added:")
    print("  • ToolHandlingMode enum with RETURN_RESULTS and COMPLETE_WITH_RESULTS")
    print("  • Extended ChatRequest schema with tool_handling_mode field")
    print("  • Updated OpenAI client with flexible tool result handling")
    print("  • Enhanced ChatResponse with tool_call_summary")
    print("  • Backward compatibility maintained (defaults to COMPLETE_WITH_RESULTS)")
    print("  • Comprehensive test coverage")
    
    print("\n🔧 Technical Details:")
    print("  • Minimal changes to existing codebase")
    print("  • Uses existing unified tool executor")
    print("  • Proper error handling for both modes")
    print("  • Token usage tracking for both completion calls")
    print("  • Rich tool execution summaries with timing")


if __name__ == "__main__":
    asyncio.run(demonstrate_tool_handling_modes())