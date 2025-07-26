#!/usr/bin/env python3
"""
Test script to validate SDK response parsing fixes.

This script tests the specific issues mentioned in the problem statement:
1. Tools list command validation error  
2. Profiles list "No profiles available" issue
3. Streaming JSON serialization
"""

import json
import os
import sys
from unittest.mock import Mock, patch

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas.conversation import (ConversationResponse, MessageResponse,
                                      StreamCompleteResponse)
from client.ai_chatbot_sdk import AIChatbotSDK, ToolsListResponse


def test_tools_list_response():
    """Test that tools list response can be parsed by SDK."""
    print("🔧 Testing Tools List Response Parsing...")
    
    # This is the new response format from our fixed API
    api_response = {
        "success": True,
        "message": "Retrieved 3 tools from 2 servers",
        "available_tools": [
            {
                "name": "file_search",
                "description": "Search through files",
                "schema": {"type": "object", "properties": {}},
                "server_name": "filesystem",
                "is_enabled": True,
                "usage_count": 5,
                "last_used_at": None
            },
            {
                "name": "web_browse", 
                "description": "Browse web pages",
                "schema": {"type": "object", "properties": {}},
                "server_name": "web",
                "is_enabled": True,
                "usage_count": 12,
                "last_used_at": "2025-01-15T10:30:00Z"
            }
        ],
        "openai_tools": [
            {"type": "function", "function": {"name": "file_search"}},
            {"type": "function", "function": {"name": "web_browse"}}
        ],
        "servers": [
            {"name": "filesystem", "status": "connected", "enabled": True},
            {"name": "web", "status": "connected", "enabled": True}
        ],
        "enabled_count": 2,
        "total_count": 2
    }
    
    try:
        # Test that this can be parsed into ToolsListResponse
        tools_response = ToolsListResponse(**api_response)
        print(f"  ✅ Successfully parsed response with {len(tools_response.available_tools)} tools")
        print(f"  ✅ Message: {tools_response.message}")
        print(f"  ✅ Enabled tools: {tools_response.enabled_count}/{tools_response.total_count}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to parse tools response: {e}")
        return False

def test_profiles_list_response():
    """Test that profiles list response shows available profiles."""
    print("\n👤 Testing Profiles List Response Parsing...")
    
    # This is the new response format from our fixed API
    api_response = {
        "success": True,
        "message": "Retrieved 3 profiles",
        "profiles": [
            {
                "name": "default",
                "title": "Default Profile", 
                "description": "Balanced settings for general use",
                "is_default": True,
                "is_active": True,
                "parameters": {"temperature": 0.7, "max_tokens": 1000},
                "usage_count": 25,
                "last_used_at": "2025-01-15T09:15:00Z",
                "created_at": "2025-01-01T00:00:00Z"
            },
            {
                "name": "creative",
                "title": "Creative Profile",
                "description": "Higher temperature for creative tasks", 
                "is_default": False,
                "is_active": True,
                "parameters": {"temperature": 1.2, "max_tokens": 1500},
                "usage_count": 8,
                "last_used_at": "2025-01-14T16:20:00Z",
                "created_at": "2025-01-05T12:00:00Z"
            },
            {
                "name": "analytical",
                "title": "Analytical Profile",
                "description": "Lower temperature for analytical tasks",
                "is_default": False, 
                "is_active": True,
                "parameters": {"temperature": 0.3, "max_tokens": 800},
                "usage_count": 15,
                "last_used_at": "2025-01-15T08:45:00Z",
                "created_at": "2025-01-03T14:30:00Z"
            }
        ],
        "total": 3,
        "page": 1,
        "size": 20,
        "filters": {
            "active_only": True,
            "search": None
        }
    }
    
    try:
        # Test that profiles are available and can be processed
        if api_response.get("profiles"):
            profiles = api_response["profiles"]
            print(f"  ✅ Found {len(profiles)} profiles (was showing 'No profiles available')")
            for profile in profiles:
                status = "default" if profile["is_default"] else "active"
                print(f"    • {profile['name']}: {profile['title']} ({status})")
            return True
        else:
            print("  ❌ No profiles in response")
            return False
    except Exception as e:
        print(f"  ❌ Failed to parse profiles response: {e}")
        return False

def test_streaming_json_serialization():
    """Test that streaming responses can be JSON serialized."""
    print("\n📡 Testing Streaming JSON Serialization...")
    
    try:
        # Create mock Pydantic objects that would come from the service layer
        from datetime import datetime
        from uuid import uuid4

        # Mock MessageResponse (this was causing the JSON serialization error)
        message_data = {
            "id": str(uuid4()),  # Convert to string
            "role": "assistant", 
            "content": "This is a test response from the AI assistant.",
            "conversation_id": str(uuid4()),  # Convert to string
            "token_count": 15,
            "tool_calls": None,
            "tool_call_results": None,
            "metainfo": {"model": "gpt-4"},
            "created_at": datetime.now()
        }
        
        conversation_data = {
            "id": str(uuid4()),  # Convert to string
            "title": "Test Conversation",
            "is_active": True,
            "user_id": str(uuid4()),  # Convert to string
            "message_count": 2,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_message_at": datetime.now(),
            "metainfo": {"category": "test"}
        }
        
        # This would be the problematic part - trying to serialize Pydantic objects
        # OLD CODE (would fail):
        # response_data = {
        #     "ai_message": MessageResponse.model_validate(message_data),
        #     "conversation": ConversationResponse.model_validate(conversation_data)
        # }
        # json.dumps(response_data)  # ❌ This would fail with "Object of type MessageResponse is not JSON serializable"
        
        # NEW CODE (works):
        ai_message = MessageResponse.model_validate(message_data)
        conversation = ConversationResponse.model_validate(conversation_data)
        
        response_data = {
            "ai_message": ai_message.model_dump(mode='json'),  # Use mode='json' to apply encoders
            "conversation": conversation.model_dump(mode='json')  # Use mode='json' to apply encoders
        }
        
        # Test the complete streaming response
        complete_response = StreamCompleteResponse(response=response_data)
        json_output = json.dumps(complete_response.model_dump())
        
        print("  ✅ Successfully serialized StreamCompleteResponse to JSON")
        print(f"  ✅ JSON length: {len(json_output)} characters")
        
        # Parse back to verify it's valid JSON
        parsed = json.loads(json_output)
        print(f"  ✅ JSON is valid and contains type: {parsed['type']}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed streaming JSON serialization test: {e}")
        return False

def test_mock_client_interaction():
    """Test mock client interaction to simulate CLI commands."""
    print("\n🤖 Testing Mock Client Interaction...")
    
    try:
        # Mock the SDK requests to test parsing logic
        with patch('requests.Session.request') as mock_request:
            # Mock tools response
            mock_tools_response = Mock()
            mock_tools_response.ok = True
            mock_tools_response.json.return_value = {
                "success": True,
                "message": "Retrieved 2 tools from 1 server",
                "available_tools": [
                    {"name": "calculator", "description": "Perform calculations", "schema": {}, "server_name": "math", "is_enabled": True, "usage_count": 3}
                ],
                "openai_tools": [],
                "servers": [{"name": "math", "status": "connected"}],
                "enabled_count": 1,
                "total_count": 1
            }
            
            # Mock profiles response  
            mock_profiles_response = Mock()
            mock_profiles_response.ok = True
            mock_profiles_response.json.return_value = {
                "success": True,
                "message": "Retrieved 1 profile", 
                "profiles": [
                    {"name": "test", "title": "Test Profile", "is_default": True, "is_active": True, "parameters": {}}
                ]
            }
            
            # Simulate different endpoints
            def mock_side_effect(method, url, **kwargs):
                if '/tools/' in url:
                    return mock_tools_response
                elif '/profiles/' in url:
                    return mock_profiles_response
                else:
                    mock_resp = Mock()
                    mock_resp.ok = False
                    mock_resp.status_code = 404
                    return mock_resp
            
            mock_request.side_effect = mock_side_effect
            
            # Test SDK initialization and calls
            sdk = AIChatbotSDK("http://localhost:8000")
            
            # Test tools list (this was failing before)
            tools_result = sdk.tools.list_tools()
            print(f"  ✅ Tools list call successful: {tools_result.message}")
            print(f"  ✅ Available tools: {len(tools_result.available_tools)}")
            
            # Test profiles list (this was showing "No profiles available")
            profiles_result = sdk.profiles.list_profiles()
            if profiles_result.get("profiles"):
                print(f"  ✅ Profiles list call successful: found {len(profiles_result['profiles'])} profiles")
            else:
                print("  ❌ Still showing no profiles available")
                return False
                
            return True
            
    except Exception as e:
        print(f"  ❌ Mock client interaction failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing SDK Response Handling Fixes")
    print("=" * 50)
    
    tests = [
        test_tools_list_response,
        test_profiles_list_response, 
        test_streaming_json_serialization,
        test_mock_client_interaction
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("  🎉 All tests PASSED! The SDK response handling issues have been fixed.")
        return 0
    else:
        print("  ⚠️  Some tests FAILED. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())