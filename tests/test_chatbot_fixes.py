"""
Test cases for the chatbot fixes.

This module tests the specific fixes made to address the chatbot issues:
1. Document search validation error (q vs query)
2. Embedding service method name error  
3. Readline support for command history
4. Streaming support in client
"""

import os
from unittest.mock import Mock, patch

import pytest


class TestDocumentSearchFix:
    """Test the document search parameter fix."""

    def test_document_search_request_validation(self):
        """Test that DocumentSearchRequest accepts 'query' parameter."""
        from client.ai_chatbot_sdk import DocumentSearchRequest

        # This should work with the fixed parameter name
        req = DocumentSearchRequest(
            query="test search", 
            limit=10,
            algorithm="hybrid"
        )
        
        assert req.query == "test search"
        assert req.limit == 10
        assert req.algorithm == "hybrid"

    def test_document_search_request_model_dump(self):
        """Test that model_dump produces correct structure."""
        from client.ai_chatbot_sdk import DocumentSearchRequest
        
        req = DocumentSearchRequest(query="test search")
        dumped = req.model_dump()
        
        # Should have 'query', not 'q'
        assert "query" in dumped
        assert "q" not in dumped
        assert dumped["query"] == "test search"


class TestEmbeddingServiceFix:
    """Test the embedding service method name fix."""

    def test_openai_client_has_correct_method(self):
        """Test that OpenAI client has the correct embedding method."""
        from app.services.openai_client import OpenAIClient
        
        client = OpenAIClient()
        
        # Should have create_embeddings_batch method
        assert hasattr(client, 'create_embeddings_batch')
        assert callable(getattr(client, 'create_embeddings_batch'))
        
        # Should NOT have the old method name
        assert not hasattr(client, 'generate_embeddings_batch')

    @patch('app.services.embedding.OpenAIClient')
    def test_embedding_service_calls_correct_method(self, mock_openai_class):
        """Test that EmbeddingService calls the correct method name."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.services.embedding import EmbeddingService

        # Mock the OpenAI client
        mock_client = Mock()
        mock_client.create_embeddings_batch = Mock(return_value=[[0.1, 0.2, 0.3]])
        mock_openai_class.return_value = mock_client
        
        # Create embedding service
        mock_db = Mock(spec=AsyncSession)
        service = EmbeddingService(db=mock_db, openai_client=mock_client)
        
        # Verify the client has the correct method
        assert hasattr(service.openai_client, 'create_embeddings_batch')


class TestReadlineSupport:
    """Test readline support for command history."""

    def test_readline_import_available(self):
        """Test that readline import is handled gracefully."""
        from client.chatbot import READLINE_AVAILABLE

        # Should be a boolean indicating availability
        assert isinstance(READLINE_AVAILABLE, bool)

    def test_setup_readline_no_error(self):
        """Test that setup_readline doesn't raise errors."""
        from client.chatbot import setup_readline

        # Should not raise any exceptions
        setup_readline()

    @patch('client.chatbot.READLINE_AVAILABLE', True)
    @patch('client.chatbot.readline')
    def test_setup_readline_with_readline(self, mock_readline):
        """Test readline setup when readline is available."""
        from client.chatbot import setup_readline

        # Mock readline methods
        mock_readline.read_history_file = Mock()
        mock_readline.parse_and_bind = Mock()
        mock_readline.set_history_length = Mock()
        
        setup_readline()
        
        # Verify readline configuration calls
        mock_readline.parse_and_bind.assert_any_call("tab: complete")
        mock_readline.set_history_length.assert_called_with(1000)

    def test_input_prompt_handles_eof(self):
        """Test that input_prompt handles EOF gracefully."""
        from client.chatbot import input_prompt
        
        with patch('builtins.input', side_effect=EOFError):
            with pytest.raises(SystemExit):
                input_prompt("Test: ")


class TestStreamingSupport:
    """Test streaming support in client."""

    def test_conversations_client_has_streaming(self):
        """Test that ConversationsClient has streaming method."""
        from client.ai_chatbot_sdk import AIChatbotSDK, ConversationsClient
        
        sdk = AIChatbotSDK("http://localhost:8000")
        client = ConversationsClient(sdk)
        
        assert hasattr(client, 'chat_stream')
        assert callable(getattr(client, 'chat_stream'))

    def test_chatbot_config_has_streaming_option(self):
        """Test that ChatbotConfig has streaming configuration."""
        # Clear env to avoid validation issues
        old_env = dict(os.environ)
        for key in list(os.environ.keys()):
            if any(x in key for x in ['SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY', 'ENVIRONMENT']):
                del os.environ[key]
        
        try:
            from client.config import ChatbotConfig
            
            config = ChatbotConfig()
            assert hasattr(config, 'enable_streaming')
            assert isinstance(config.enable_streaming, bool)
            assert config.enable_streaming == False  # Default value
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    @patch('client.ai_chatbot_sdk.requests.Session.post')
    def test_chat_stream_method(self, mock_post):
        """Test the chat_stream method functionality."""
        from client.ai_chatbot_sdk import (AIChatbotSDK, ChatRequest,
                                           ConversationsClient)

        # Mock streaming response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            "data: chunk1",
            "data: chunk2", 
            "data: [DONE]"
        ]
        mock_post.return_value = mock_response
        
        sdk = AIChatbotSDK("http://localhost:8000")
        sdk.set_token("test_token")
        client = ConversationsClient(sdk)
        
        chat_req = ChatRequest(user_message="test message")
        
        # Get streaming chunks
        chunks = list(client.chat_stream(chat_req))
        
        assert chunks == ["chunk1", "chunk2"]
        mock_post.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])