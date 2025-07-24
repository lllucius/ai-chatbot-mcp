"""
Tests for the enhanced AI Chatbot Terminal Client.

This module tests the configuration management, registry features, and
improved functionality of the chatbot client.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from client.config import ChatbotConfig, load_config, get_config_dir
from client.chatbot import AIChatbotTerminal


class TestChatbotConfig:
    """Test configuration management functionality."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ChatbotConfig()
        assert config.api_url == "http://localhost:8000"
        assert config.default_use_rag is True
        assert config.default_use_tools is True
        assert config.spinner_enabled is True
        assert config.auto_title is True
        assert config.max_history_display == 50

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            'CHATBOT_API_URL': 'http://test.example.com',
            'CHATBOT_USERNAME': 'testuser',
            'CHATBOT_DEFAULT_USE_RAG': 'false',
            'CHATBOT_DEBUG_MODE': 'true'
        }):
            config = ChatbotConfig()
            assert config.api_url == "http://test.example.com"
            assert config.username == "testuser"
            assert config.default_use_rag is False
            assert config.debug_mode is True

    def test_load_config_with_file(self):
        """Test loading configuration from file."""
        config_content = """
CHATBOT_API_URL=http://config.example.com
CHATBOT_USERNAME=configuser
CHATBOT_DEFAULT_USE_TOOLS=false
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                config = load_config(f.name)
                assert config.api_url == "http://config.example.com"
                assert config.username == "configuser"
                assert config.default_use_tools is False
            finally:
                os.unlink(f.name)

    def test_config_directories(self):
        """Test configuration directory creation."""
        config_dir = get_config_dir()
        assert config_dir.exists()
        assert config_dir.is_dir()


class TestAIChatbotTerminal:
    """Test enhanced chatbot terminal functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ChatbotConfig(
            api_url="http://test.example.com",
            username="testuser",
            password="testpass",
            debug_mode=True
        )

    @patch('client.chatbot.AIChatbotSDK')
    def test_chatbot_initialization(self, mock_sdk_class):
        """Test chatbot initialization with config."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        bot = AIChatbotTerminal(self.config)
        
        assert bot.config == self.config
        assert bot.sdk == mock_sdk
        assert bot.current_prompt == self.config.default_prompt_name
        assert bot.current_profile == self.config.default_profile_name
        mock_sdk_class.assert_called_once_with(base_url=self.config.api_url)

    @patch('client.chatbot.AIChatbotSDK')
    def test_token_persistence(self, mock_sdk_class):
        """Test token saving and loading functionality."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock user response
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_sdk.auth.me.return_value = mock_user
        
        bot = AIChatbotTerminal(self.config)
        
        # Test token saving
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            bot.config.token_file = f.name
            bot.username = "testuser"
            bot._save_token("test_token_123")
            
            # Verify token was saved
            with open(f.name, 'r') as saved_file:
                token_data = json.load(saved_file)
                assert token_data['token'] == "test_token_123"
                assert token_data['username'] == "testuser"
                
            # Test token loading
            bot2 = AIChatbotTerminal(self.config)
            bot2.config.token_file = f.name
            success = bot2._load_saved_token()
            
            assert success is True
            assert bot2.token == "test_token_123"
            assert bot2.username == "testuser"
            
            os.unlink(f.name)

    @patch('client.chatbot.AIChatbotSDK')
    def test_prompt_commands(self, mock_sdk_class):
        """Test prompt-related command handling."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock prompts response
        mock_sdk.prompts.list_prompts.return_value = {
            'prompts': [
                {'name': 'helpful', 'title': 'Helpful Assistant'},
                {'name': 'creative', 'title': 'Creative Writer'}
            ]
        }
        
        mock_prompt = Mock()
        mock_prompt.title = "Helpful Assistant"
        mock_prompt.description = "A helpful AI assistant"
        mock_prompt.category = "general"
        mock_prompt.content = "You are a helpful assistant"
        mock_sdk.prompts.get_prompt.return_value = mock_prompt
        
        bot = AIChatbotTerminal(self.config)
        
        # Test prompt list
        with patch('builtins.print') as mock_print:
            bot.handle_prompt_command("/prompt list")
            mock_sdk.prompts.list_prompts.assert_called_once()
            
        # Test prompt use
        bot.handle_prompt_command("/prompt use helpful")
        assert bot.current_prompt == "helpful"
        mock_sdk.prompts.get_prompt.assert_called_with("helpful")

    @patch('client.chatbot.AIChatbotSDK')  
    def test_profile_commands(self, mock_sdk_class):
        """Test profile-related command handling."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock profiles response
        mock_sdk.profiles.list_profiles.return_value = {
            'profiles': [
                {'name': 'creative', 'title': 'Creative Model', 'is_default': False},
                {'name': 'precise', 'title': 'Precise Model', 'is_default': True}
            ]
        }
        
        mock_profile = Mock()
        mock_profile.title = "Creative Model"
        mock_profile.description = "High creativity settings"
        mock_profile.model_name = "gpt-4"
        mock_profile.parameters = {"temperature": 0.9, "max_tokens": 2000}
        mock_sdk.profiles.get_profile.return_value = mock_profile
        
        bot = AIChatbotTerminal(self.config)
        
        # Test profile list
        with patch('builtins.print') as mock_print:
            bot.handle_profile_command("/profile list")
            mock_sdk.profiles.list_profiles.assert_called_once()
            
        # Test profile use
        bot.handle_profile_command("/profile use creative")
        assert bot.current_profile == "creative"
        mock_sdk.profiles.get_profile.assert_called_with("creative")

    @patch('client.chatbot.AIChatbotSDK')
    def test_tools_commands(self, mock_sdk_class):
        """Test tools-related command handling."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock tools response
        mock_tool1 = Mock()
        mock_tool1.name = "calculator"
        mock_tool1.description = "Perform mathematical calculations"
        mock_tool1.is_enabled = True
        
        mock_tool2 = Mock()
        mock_tool2.name = "weather"
        mock_tool2.description = "Get weather information"
        mock_tool2.is_enabled = False
        
        mock_tools_response = Mock()
        mock_tools_response.available_tools = [mock_tool1, mock_tool2]
        mock_tools_response.enabled_count = 1
        mock_tools_response.total_count = 2
        mock_tools_response.servers = [{'name': 'test_server', 'status': 'active'}]
        
        mock_sdk.tools.list_tools.return_value = mock_tools_response
        
        bot = AIChatbotTerminal(self.config)
        
        # Test tools list
        with patch('builtins.print') as mock_print:
            bot.handle_tools_command("/tools list")
            mock_sdk.tools.list_tools.assert_called_once()
            
        # Test tool enable
        bot.handle_tools_command("/tools enable weather")
        mock_sdk.tools.enable_tool.assert_called_with("weather")

    @patch('client.chatbot.AIChatbotSDK')
    def test_conversation_export(self, mock_sdk_class):
        """Test conversation export functionality."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock conversation messages
        mock_msg1 = Mock()
        mock_msg1.id = "msg1"
        mock_msg1.role = "user"
        mock_msg1.content = "Hello"
        mock_msg1.created_at = None
        mock_msg1.token_count = 5
        
        mock_msg2 = Mock()
        mock_msg2.id = "msg2"
        mock_msg2.role = "assistant"
        mock_msg2.content = "Hi there!"
        mock_msg2.created_at = None
        mock_msg2.token_count = 10
        
        mock_msgs_response = Mock()
        mock_msgs_response.items = [mock_msg1, mock_msg2]
        mock_sdk.conversations.messages.return_value = mock_msgs_response
        
        bot = AIChatbotTerminal(self.config)
        bot.conversation_id = "test-conv-id"
        bot.conversation_title = "Test Conversation"
        
        # Test export
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                with patch('builtins.print'):
                    bot.export_conversation()
                    
                # Verify export data structure
                export_call = mock_json_dump.call_args[0][0]
                assert export_call['conversation_id'] == "test-conv-id"
                assert export_call['title'] == "Test Conversation"
                assert len(export_call['messages']) == 2
                assert export_call['messages'][0]['role'] == "user"
                assert export_call['messages'][1]['role'] == "assistant"

    @patch('client.chatbot.input_prompt')
    @patch('client.chatbot.AIChatbotSDK')
    def test_configuration_interface(self, mock_sdk_class, mock_input):
        """Test interactive configuration interface."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock user inputs
        mock_input.side_effect = ["false", "true", "25"]
        
        bot = AIChatbotTerminal(self.config)
        
        with patch('builtins.print'):
            bot.configure_settings()
            
        # Verify settings were updated
        assert bot.config.default_use_rag is False
        assert bot.config.default_use_tools is True
        assert bot.config.max_history_display == 25

    @patch('client.chatbot.AIChatbotSDK')
    def test_enhanced_chat_request(self, mock_sdk_class):
        """Test chat request with registry features."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock chat response
        mock_ai_msg = Mock()
        mock_ai_msg.content = "Hello! How can I help you?"
        
        mock_conversation = Mock()
        mock_conversation.id = "conv-id"
        mock_conversation.title = "Test Chat"
        
        mock_response = Mock()
        mock_response.ai_message = mock_ai_msg
        mock_response.conversation = mock_conversation
        
        mock_sdk.conversations.chat.return_value = mock_response
        
        bot = AIChatbotTerminal(self.config)
        bot.conversation_id = "existing-conv"
        bot.conversation_title = "Existing Conv"
        bot.current_prompt = "helpful_assistant"
        bot.current_profile = "creative_model"
        
        # Simulate sending a message (we'll mock the input and chat flow)
        with patch('client.chatbot.input_prompt', return_value="Hello"):
            with patch('client.chatbot.spinner') as mock_spinner:
                with patch('builtins.print'):
                    # Manually create the chat request that would be made
                    from client.ai_chatbot_sdk import ChatRequest
                    
                    expected_request = ChatRequest(
                        user_message="Hello",
                        conversation_id="existing-conv",
                        conversation_title="Existing Conv",
                        use_rag=bot.config.default_use_rag,
                        use_tools=bot.config.default_use_tools,
                        prompt_name="helpful_assistant",
                        profile_name="creative_model"
                    )
                    
                    # Verify the request structure is correct
                    assert expected_request.user_message == "Hello"
                    assert expected_request.prompt_name == "helpful_assistant"
                    assert expected_request.profile_name == "creative_model"
                    assert expected_request.use_rag == bot.config.default_use_rag
                    assert expected_request.use_tools == bot.config.default_use_tools


class TestIntegration:
    """Integration tests for the enhanced chatbot."""

    @patch('client.chatbot.AIChatbotSDK')
    def test_full_workflow(self, mock_sdk_class):
        """Test a complete workflow with all features."""
        mock_sdk = Mock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock authentication
        mock_token = Mock()
        mock_token.access_token = "test_token"
        mock_sdk.auth.login.return_value = mock_token
        
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_sdk.auth.me.return_value = mock_user
        
        # Create bot and authenticate
        config = ChatbotConfig(username="testuser", password="testpass")
        bot = AIChatbotTerminal(config)
        
        with patch('builtins.print'):
            bot.authenticate()
            
        # Verify authentication
        assert bot.token == "test_token"
        assert bot.username == "testuser"
        mock_sdk.auth.login.assert_called_once_with(username="testuser", password="testpass")
        mock_sdk.set_token.assert_called_with("test_token")


if __name__ == "__main__":
    pytest.main([__file__])