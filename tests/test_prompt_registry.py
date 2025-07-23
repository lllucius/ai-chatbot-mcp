"""
Unit tests for prompt registry functionality.

These tests cover prompt management including creation, activation,
and usage tracking.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from app.services.prompt_service import PromptService


class TestPromptService:
    """Test prompt service functionality."""

    @pytest.mark.asyncio
    async def test_create_prompt(self):
        """Test creating a prompt."""
        with patch('app.services.prompt_service.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            prompt = await PromptService.create_prompt(
                name="test_prompt",
                title="Test Prompt",
                content="You are a test assistant.",
                description="Test prompt description",
                category="test",
                tags=["test", "example"]
            )
            
            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_default_prompt(self):
        """Test creating a default prompt unsets other defaults."""
        with patch('app.services.prompt_service.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            await PromptService.create_prompt(
                name="default_prompt",
                title="Default Prompt",
                content="You are a helpful assistant.",
                is_default=True
            )
            
            # Should unset existing defaults first
            assert mock_db.execute.call_count >= 1  # At least one execute call to unset defaults
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_default_prompt(self):
        """Test setting a prompt as default."""
        with patch('app.services.prompt_service.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.rowcount = 1
            
            result = await PromptService.set_default_prompt("test_prompt")
            
            assert result is True
            # Should execute two queries: unset all defaults, then set new default
            assert mock_db.execute.call_count == 2
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_prompt_usage(self):
        """Test recording prompt usage."""
        with patch('app.services.prompt_service.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock prompt exists
            mock_prompt = AsyncMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prompt
            
            result = await PromptService.record_prompt_usage("test_prompt")
            
            assert result is True
            mock_prompt.record_usage.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_prompts_with_search(self):
        """Test listing prompts with search functionality."""
        with patch('app.services.prompt_service.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock query result
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            
            await PromptService.list_prompts(
                active_only=True,
                category="test",
                search="assistant"
            )
            
            # Verify query was executed
            mock_db.execute.assert_called_once()


class TestPromptModel:
    """Test prompt model functionality."""

    def test_prompt_tag_list_property(self):
        """Test prompt tag list property."""
        from app.models.prompt import Prompt
        
        prompt = Prompt(
            name="test",
            title="Test",
            content="Content",
            tags="tag1, tag2 ,  tag3"
        )
        
        assert prompt.tag_list == ["tag1", "tag2", "tag3"]

    def test_prompt_tag_list_setter(self):
        """Test prompt tag list setter."""
        from app.models.prompt import Prompt
        
        prompt = Prompt(
            name="test",
            title="Test",
            content="Content"
        )
        
        prompt.tag_list = ["new", "tags", "here"]
        assert prompt.tags == "new,tags,here"

    def test_prompt_record_usage(self):
        """Test prompt usage recording."""
        from app.models.prompt import Prompt
        from datetime import datetime
        
        prompt = Prompt(
            name="test",
            title="Test",
            content="Content",
            usage_count=5
        )
        
        prompt.record_usage()
        
        assert prompt.usage_count == 6
        assert isinstance(prompt.last_used_at, datetime)


class TestPromptStatistics:
    """Test prompt statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_prompt_stats(self):
        """Test getting prompt statistics."""
        with patch('app.services.prompt_service.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock database queries
            mock_db.scalar.side_effect = [10, 8]  # total, active
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            
            # Mock get_default_prompt
            with patch.object(PromptService, 'get_default_prompt') as mock_default:
                mock_default.return_value = None
                
                # Mock get_categories and get_all_tags
                with patch.object(PromptService, 'get_categories') as mock_categories:
                    with patch.object(PromptService, 'get_all_tags') as mock_tags:
                        mock_categories.return_value = ["test", "example"]
                        mock_tags.return_value = ["tag1", "tag2"]
                        
                        stats = await PromptService.get_prompt_stats()
                        
                        assert stats["total_prompts"] == 10
                        assert stats["active_prompts"] == 8
                        assert stats["inactive_prompts"] == 2
                        assert stats["default_prompt"] is None
                        assert len(stats["categories"]) == 2
                        assert stats["total_tags"] == 2