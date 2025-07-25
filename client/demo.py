#!/usr/bin/env python3
"""
Demo script for the Enhanced AI Chatbot Terminal Client.

This script demonstrates the new features and improvements made to the chatbot client,
including configuration management, registry support, and enhanced commands.
"""
# Add the project root to the Python path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import os

from client.chatbot import AIChatbotTerminal
from client.config import ChatbotConfig


def demo_configuration():
    """Demonstrate configuration management features."""
    print("🔧 Configuration Management Demo")
    print("=" * 50)

    # Create a sample config
    config = ChatbotConfig(
        api_url="http://demo.example.com",
        username="demo_user",
        default_use_rag=True,
        default_use_tools=True,
        spinner_enabled=True,
        auto_title=True,
        max_history_display=25,
        debug_mode=True,
    )

    print(f"📍 API URL: {config.api_url}")
    print(f"👤 Username: {config.username}")
    print(f"🧠 RAG Enabled: {config.default_use_rag}")
    print(f"🔧 Tools Enabled: {config.default_use_tools}")
    print(f"⏳ Spinner Enabled: {config.spinner_enabled}")
    print(f"📝 Auto Title: {config.auto_title}")
    print(f"📖 Max History: {config.max_history_display}")
    print(f"🐛 Debug Mode: {config.debug_mode}")
    print()

    # Demonstrate environment variable override
    os.environ["CHATBOT_API_URL"] = "http://env.example.com"
    env_config = ChatbotConfig()
    print(f"🌍 Environment override - API URL: {env_config.api_url}")
    print()


def demo_help_system():
    """Demonstrate the enhanced help system."""
    print("📚 Enhanced Help System Demo")
    print("=" * 50)

    # Create a minimal config for demo
    config = ChatbotConfig(debug_mode=True)

    # Mock the SDK to avoid actual API calls
    from unittest.mock import Mock, patch

    with patch("client.chatbot.AIChatbotSDK") as mock_sdk_class:
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk

        bot = AIChatbotTerminal(config)

        print("New commands available in the enhanced chatbot:")
        print()
        bot.show_help()
        print()


def demo_registry_features():
    """Demonstrate registry management features."""
    print("🗂️ Registry Features Demo")
    print("=" * 50)

    config = ChatbotConfig(debug_mode=True)

    from unittest.mock import Mock, patch

    with patch("client.chatbot.AIChatbotSDK") as mock_sdk_class:
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk

        # Mock prompt registry
        mock_sdk.prompts.list_prompts.return_value = {
            "prompts": [
                {
                    "name": "helpful_assistant",
                    "title": "Helpful Assistant",
                    "description": "A friendly and helpful AI assistant",
                    "category": "general",
                },
                {
                    "name": "code_reviewer",
                    "title": "Code Reviewer",
                    "description": "Specialized in reviewing code and providing feedback",
                    "category": "development",
                },
                {
                    "name": "creative_writer",
                    "title": "Creative Writer",
                    "description": "Helps with creative writing and storytelling",
                    "category": "creative",
                },
            ]
        }

        # Mock profile registry
        mock_sdk.profiles.list_profiles.return_value = {
            "profiles": [
                {
                    "name": "balanced",
                    "title": "Balanced Model",
                    "description": "Good balance of creativity and precision",
                    "model_name": "gpt-4",
                    "parameters": {"temperature": 0.7, "max_tokens": 1500},
                    "is_default": True,
                },
                {
                    "name": "creative",
                    "title": "Creative Model",
                    "description": "High creativity for writing and brainstorming",
                    "model_name": "gpt-4",
                    "parameters": {"temperature": 0.9, "max_tokens": 2000},
                    "is_default": False,
                },
                {
                    "name": "precise",
                    "title": "Precise Model",
                    "description": "Low temperature for factual and analytical tasks",
                    "model_name": "gpt-4",
                    "parameters": {"temperature": 0.3, "max_tokens": 1000},
                    "is_default": False,
                },
            ]
        }

        # Mock tools registry
        mock_tool1 = Mock()
        mock_tool1.name = "calculator"
        mock_tool1.description = "Perform mathematical calculations and computations"
        mock_tool1.is_enabled = True

        mock_tool2 = Mock()
        mock_tool2.name = "weather"
        mock_tool2.description = "Get current weather information for any location"
        mock_tool2.is_enabled = True

        mock_tool3 = Mock()
        mock_tool3.name = "web_search"
        mock_tool3.description = "Search the web for current information"
        mock_tool3.is_enabled = False

        mock_tools_response = Mock()
        mock_tools_response.available_tools = [mock_tool1, mock_tool2, mock_tool3]
        mock_tools_response.enabled_count = 2
        mock_tools_response.total_count = 3
        mock_tools_response.servers = [
            {"name": "math_server", "status": "active"},
            {"name": "web_server", "status": "inactive"},
        ]

        mock_sdk.tools.list_tools.return_value = mock_tools_response

        bot = AIChatbotTerminal(config)

        print("📝 Available Prompts:")
        bot.handle_prompt_command("/prompt list")
        print()

        print("🎯 Available LLM Profiles:")
        bot.handle_profile_command("/profile list")
        print()

        print("🔧 Available Tools:")
        bot.handle_tools_command("/tools list")
        print()

        print("📊 Tools Status:")
        bot.handle_tools_command("/tools status")
        print()


def demo_document_management():
    """Demonstrate document management features."""
    print("📄 Document Management Demo")
    print("=" * 50)

    config = ChatbotConfig(debug_mode=True)

    from unittest.mock import Mock, patch

    with patch("client.chatbot.AIChatbotSDK") as mock_sdk_class:
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk

        # Mock document list
        mock_doc1 = Mock()
        mock_doc1.title = "AI Research Paper"
        mock_doc1.file_type = "pdf"
        mock_doc1.file_size = 1024 * 1024 * 2  # 2MB
        mock_doc1.processing_status = "completed"
        mock_doc1.id = "doc-123"
        mock_doc1.chunk_count = 45

        mock_doc2 = Mock()
        mock_doc2.title = "Project Documentation"
        mock_doc2.file_type = "docx"
        mock_doc2.file_size = 1024 * 512  # 512KB
        mock_doc2.processing_status = "processing"
        mock_doc2.id = "doc-456"
        mock_doc2.chunk_count = 12

        mock_docs_response = Mock()
        mock_docs_response.items = [mock_doc1, mock_doc2]
        mock_sdk.documents.list.return_value = mock_docs_response

        # Mock document search
        mock_sdk.search.search.return_value = {
            "results": [
                {
                    "title": "AI Research Paper",
                    "content": "Artificial intelligence has made significant advances...",
                    "score": 0.95,
                },
                {
                    "title": "Project Documentation",
                    "content": "This project implements a chatbot system...",
                    "score": 0.87,
                },
            ]
        }

        bot = AIChatbotTerminal(config)

        print("📁 Document List:")
        bot.handle_docs_command("/docs list")
        print()

        print("🔍 Document Search Results (query: 'artificial intelligence'):")
        bot.handle_docs_command("/docs search artificial intelligence")
        print()


def demo_conversation_features():
    """Demonstrate enhanced conversation features."""
    print("💬 Enhanced Conversation Features Demo")
    print("=" * 50)

    config = ChatbotConfig(auto_title=True, max_history_display=5, debug_mode=True)

    from unittest.mock import Mock, patch

    with patch("client.chatbot.AIChatbotSDK") as mock_sdk_class:
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk

        # Mock conversation list
        from datetime import datetime, timedelta

        mock_conv1 = Mock()
        mock_conv1.id = "conv-123"
        mock_conv1.title = "Machine Learning Discussion"
        mock_conv1.message_count = 15
        mock_conv1.is_active = True
        mock_conv1.last_message_at = datetime.now() - timedelta(hours=2)

        mock_conv2 = Mock()
        mock_conv2.id = "conv-456"
        mock_conv2.title = "Python Development Help"
        mock_conv2.message_count = 8
        mock_conv2.is_active = True
        mock_conv2.last_message_at = datetime.now() - timedelta(days=1)

        mock_conv3 = Mock()
        mock_conv3.id = "conv-789"
        mock_conv3.title = "Creative Writing Session"
        mock_conv3.message_count = 23
        mock_conv3.is_active = False
        mock_conv3.last_message_at = datetime.now() - timedelta(days=3)

        mock_convs_response = Mock()
        mock_convs_response.items = [mock_conv1, mock_conv2, mock_conv3]
        mock_sdk.conversations.list.return_value = mock_convs_response

        # Initialize bot for demo purposes
        AIChatbotTerminal(config)

        print("📋 Enhanced conversation list with metadata:")
        print("Your recent conversations:")
        for i, conv in enumerate(mock_convs_response.items, 1):
            status = "Active" if conv.is_active else "Archived"
            last_msg = conv.last_message_at.strftime("%Y-%m-%d %H:%M")
            print(
                f"  [{i}] {conv.title[:50]} (ID: {str(conv.id)[:8]}..., {conv.message_count} msgs, {status}, {last_msg})"
            )
        print()

        print("🔍 Search functionality:")
        print("- Search conversations by title")
        print("- Filter by status (active/archived)")
        print("- Export conversations to JSON")
        print()


def demo_settings_management():
    """Demonstrate settings and configuration management."""
    print("⚙️ Settings Management Demo")
    print("=" * 50)

    config = ChatbotConfig(debug_mode=True)

    from unittest.mock import Mock, patch

    with patch("client.chatbot.AIChatbotSDK") as mock_sdk_class:
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk

        bot = AIChatbotTerminal(config)
        bot.username = "demo_user"
        bot.current_prompt = "helpful_assistant"
        bot.current_profile = "balanced"

        print("📊 Current Settings Display:")
        bot.show_settings()
        print()

        print("🔧 Interactive Configuration:")
        print("- Toggle RAG on/off")
        print("- Toggle tools on/off")
        print("- Adjust max history display")
        print("- Change default prompt/profile")
        print("- Enable/disable spinner")
        print()


def main():
    """Run all demonstrations."""
    print("🚀 AI Chatbot Terminal Client - Enhanced Features Demo")
    print("=" * 60)
    print()

    demos = [
        demo_configuration,
        demo_help_system,
        demo_registry_features,
        demo_document_management,
        demo_conversation_features,
        demo_settings_management,
    ]

    for i, demo_func in enumerate(demos, 1):
        print(f"Demo {i}/{len(demos)}")
        demo_func()

        if i < len(demos):
            input("Press Enter to continue to the next demo...")
            print()

    print("✅ Demo completed! The enhanced chatbot includes:")
    print("   • Configuration management with environment variables")
    print("   • Registry support for prompts, profiles, and tools")
    print("   • Document upload and search capabilities")
    print("   • Enhanced conversation management with search/export")
    print("   • Persistent authentication tokens")
    print("   • Interactive settings configuration")
    print("   • Comprehensive help system")
    print("   • Error handling and debugging features")
    print()
    print("🎯 The chatbot now supports advanced AI platform features")
    print("   while maintaining a simple, intuitive command-line interface.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Thanks for checking out the enhanced features!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("This is expected in a demo environment without a running API server.")
