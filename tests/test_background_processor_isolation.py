"""
Test background processor database isolation and session management.

This test verifies that the refactored background processor properly:
1. Creates isolated database sessions per task
2. Avoids session leakage between tasks
3. Works well with SQLAlchemy's async architecture
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.background_processor import BackgroundProcessor, ProcessingTask, TaskStatus


class TestBackgroundProcessorIsolation:
    """Test database isolation in background processor."""

    @pytest.fixture
    def processor(self):
        """Create a background processor for testing."""
        return BackgroundProcessor(max_concurrent_tasks=2)

    @pytest.fixture
    def mock_async_session_local(self):
        """Mock AsyncSessionLocal to track session creation."""
        with patch('app.database.AsyncSessionLocal') as mock:
            mock_session = AsyncMock()
            mock.return_value = mock_session
            yield mock, mock_session

    def test_processor_initialization_no_db_dependency(self, processor):
        """Test that processor can be initialized without a database session."""
        assert processor is not None
        assert processor.max_concurrent_tasks == 2
        assert processor.active_tasks == {}
        assert processor.task_results == {}

    @pytest.mark.asyncio
    async def test_get_background_processor_no_db_parameter(self):
        """Test that get_background_processor no longer requires db parameter."""
        from app.services.background_processor import get_background_processor
        
        # Should not raise an error when called without parameters
        with patch('app.services.background_processor._background_processor', None):
            with patch.object(BackgroundProcessor, 'start', new_callable=AsyncMock):
                processor = await get_background_processor()
                assert processor is not None

    @pytest.mark.asyncio
    async def test_process_task_creates_own_session(self, processor, mock_async_session_local):
        """Test that each task creates its own database session."""
        mock_session_factory, mock_session = mock_async_session_local
        
        # Mock database operations
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        # Mock the document processing
        with patch.object(processor, '_process_document_task', new_callable=AsyncMock) as mock_process:
            task = ProcessingTask(
                task_id="task_123",
                document_id=123,
                task_type="process_document"
            )
            
            await processor._process_task(task)
            
            # Verify that AsyncSessionLocal was called to create a new session
            mock_session_factory.assert_called_once()
            
            # Verify that the session was properly closed
            mock_session.close.assert_called_once()
            
            # Verify the document processing was called with the session
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_tasks_use_separate_sessions(self, processor, mock_async_session_local):
        """Test that concurrent tasks each get their own database session."""
        mock_session_factory, mock_session = mock_async_session_local
        
        # Make the factory return different mock sessions for each call
        session1 = AsyncMock()
        session2 = AsyncMock()
        mock_session_factory.side_effect = [session1, session2]
        
        # Mock database operations for both sessions
        for session in [session1, session2]:
            session.execute = AsyncMock()
            session.commit = AsyncMock()
            session.close = AsyncMock()
        
        # Mock the document processing to be quick
        with patch.object(processor, '_process_document_task', new_callable=AsyncMock):
            task1 = ProcessingTask(
                task_id="task_123",
                document_id=123,
                task_type="process_document"
            )
            task2 = ProcessingTask(
                task_id="task_123",
                document_id=123,
                task_type="process_document"
            )
            
            # Process tasks concurrently
            await asyncio.gather(
                processor._process_task(task1),
                processor._process_task(task2)
            )
            
            # Verify that two separate sessions were created
            assert mock_session_factory.call_count == 2
            
            # Verify both sessions were closed
            session1.close.assert_called_once()
            session2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_closed_on_error(self, processor, mock_async_session_local):
        """Test that database session is properly closed even when task fails."""
        mock_session_factory, mock_session = mock_async_session_local
        
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        # Mock the document processing to raise an error
        with patch.object(processor, '_process_document_task', new_callable=AsyncMock) as mock_process:
            mock_process.side_effect = Exception("Test error")
            
            task = ProcessingTask(
                task_id="task_123",
                document_id=123,
                task_type="process_document"
            )
            
            # Process the task (should handle the error)
            await processor._process_task(task)
            
            # Verify that the session was still closed despite the error
            mock_session.close.assert_called_once()
            
            # Verify the task status was updated to reflect the error handling
            assert task.task_id not in processor.active_tasks

    @pytest.mark.asyncio
    async def test_error_handling_uses_provided_session(self, processor, mock_async_session_local):
        """Test that error handling uses the same session as the task."""
        mock_session_factory, mock_session = mock_async_session_local
        
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        
        # Mock the document processing to raise an error
        with patch.object(processor, '_process_document_task', new_callable=AsyncMock) as mock_process:
            mock_process.side_effect = Exception("Test error")
            
            # Mock the error handler
            with patch.object(processor, '_handle_task_error', new_callable=AsyncMock) as mock_error_handler:
                task = ProcessingTask(
                    task_id="task_123",
                    document_id=123,
                    task_type="process_document"
                )
                
                await processor._process_task(task)
                
                # Verify error handler was called with the session
                mock_error_handler.assert_called_once()
                args = mock_error_handler.call_args[0]
                assert args[0] == task  # First arg is task
                assert isinstance(args[1], Exception)  # Second arg is error
                assert args[2] == mock_session  # Third arg is db session

    @pytest.mark.asyncio
    async def test_task_status_tracking_isolated(self, processor):
        """Test that task status tracking doesn't interfere between tasks."""
        task1_id = "task_123"
        task2_id = "task_456"
        
        task1 = ProcessingTask(task1_id, 123, "process_document")
        task2 = ProcessingTask(task2_id, 456, "process_document")
        
        # Add tasks to active tasks
        processor.active_tasks[task1_id] = task1
        processor.active_tasks[task2_id] = task2
        
        # Update status of one task
        task1.status = TaskStatus.PROCESSING
        task1.progress = 0.5
        
        # Verify the other task is unaffected
        assert task2.status == TaskStatus.QUEUED
        assert task2.progress == 0.0
        
        # Verify we can get independent status for each task
        status1 = await processor.get_task_status(task1_id)
        status2 = await processor.get_task_status(task2_id)
        
        # Both should be valid but different
        assert status1 is not None
        assert status2 is not None
        assert status1 != status2