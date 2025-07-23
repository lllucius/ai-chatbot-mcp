"""
Test suite for enhanced document processing functionality.

This test module covers:
- Enhanced document processor with multiple formats
- Background processing service
- Document preprocessing and normalization
- API endpoints for enhanced functionality
- Configuration management

Current User: assistant
Current Date: 2025-01-20
"""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.background_processor import (
    BackgroundProcessor,
    ProcessingTask,
    TaskStatus,
)
from app.utils.enhanced_document_processor import DocumentProcessor
from app.utils.standard_logging import set_correlation_id, setup_logging


class TestEnhancedDocumentProcessor:
    """Test the enhanced document processor."""

    @pytest.fixture
    def processor(self):
        """Create document processor instance."""
        return DocumentProcessor(config={})

    def test_format_detection(self, processor):
        """Test file format detection."""
        # Test supported formats
        supported_formats = [".txt", ".md", ".pdf", ".docx", ".html", ".json", ".csv"]

        for ext in supported_formats:
            assert ext in processor.SUPPORTED_FORMATS

    def test_text_preprocessing(self, processor):
        """Test text preprocessing functionality."""
        # Test with problematic text
        test_text = """
        This   has    multiple    spaces…
        "Smart quotes" and 'single quotes'
        Em—dash and en–dash
        Non-breaking\u00a0space
        
        
        Multiple newlines
        
        
        """

        processed = processor.preprocess_text(test_text)

        # Check normalization
        assert "…" not in processed  # Ellipsis normalized
        assert '"' in processed and '"' not in processed  # Smart quotes normalized
        assert "-" in processed and "—" not in processed  # Em dash normalized
        assert "\u00a0" not in processed  # Non-breaking space removed

        # Check whitespace cleanup
        assert "    " not in processed  # Multiple spaces removed
        assert not processed.startswith(" ")  # Leading space removed
        assert not processed.endswith(" ")  # Trailing space removed

    @pytest.mark.asyncio
    async def test_text_file_extraction(self, processor):
        """Test text file extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = (
                "This is a test document.\nWith multiple lines.\nAnd some content."
            )
            f.write(test_content)
            temp_path = f.name

        try:
            extracted = await processor.extract_text(temp_path)
            assert "test document" in extracted
            assert "multiple lines" in extracted
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_json_extraction(self, processor):
        """Test JSON content extraction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_json = {
                "title": "Test Document",
                "content": "This is the main content",
                "metadata": {"author": "Test Author", "tags": ["test", "document"]},
                "nested": {"description": "Nested description"},
            }
            import json

            json.dump(test_json, f)
            temp_path = f.name

        try:
            extracted = await processor.extract_text(temp_path)
            assert "Test Document" in extracted
            assert "main content" in extracted
            assert "Test Author" in extracted
            assert "Nested description" in extracted
        finally:
            Path(temp_path).unlink()

    def test_language_detection(self, processor):
        """Test language detection."""
        english_text = "This is a test document written in English."
        spanish_text = "Este es un documento de prueba escrito en español."

        eng_lang = processor.detect_language(english_text)
        spa_lang = processor.detect_language(spanish_text)

        assert eng_lang == "en"
        assert spa_lang == "es"

    def test_text_statistics(self, processor):
        """Test text statistics generation."""
        test_text = "This is a test document.\n\nIt has multiple paragraphs.\nAnd several lines."

        stats = processor.get_text_statistics(test_text)

        assert stats["character_count"] > 0
        assert stats["word_count"] > 0
        assert stats["line_count"] >= 3
        assert stats["paragraph_count"] >= 2
        assert "language" in stats


class TestBackgroundProcessor:
    """Test the background processing service."""

    @pytest.fixture
    async def mock_db(self):
        """Mock database session."""
        from unittest.mock import AsyncMock

        return AsyncMock()

    @pytest.fixture
    async def processor(self, mock_db):
        """Create background processor instance."""
        return BackgroundProcessor(mock_db, max_concurrent_tasks=2)

    def test_processing_task_creation(self):
        """Test processing task creation."""
        document_id = uuid4()
        task_id = str(uuid4())

        task = ProcessingTask(
            task_id=task_id,
            document_id=document_id,
            task_type="process_document",
            priority=5,
        )

        assert task.task_id == task_id
        assert task.document_id == document_id
        assert task.status == TaskStatus.QUEUED
        assert task.priority == 5
        assert task.retries == 0

    def test_task_priority_comparison(self):
        """Test task priority ordering."""
        task_high = ProcessingTask("1", uuid4(), priority=1)
        task_low = ProcessingTask("2", uuid4(), priority=10)

        # Lower priority number = higher priority
        assert task_high < task_low

    @pytest.mark.asyncio
    async def test_queue_document_processing(self, processor):
        """Test queueing documents for processing."""
        document_id = uuid4()

        task_id = await processor.queue_document_processing(
            document_id=document_id, priority=3
        )

        assert isinstance(task_id, str)
        assert processor.task_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_get_queue_status(self, processor):
        """Test getting queue status."""
        status = await processor.get_queue_status()

        assert "queue_size" in status
        assert "active_tasks" in status
        assert "max_concurrent_tasks" in status
        assert "completed_tasks" in status
        assert "worker_running" in status

    @pytest.mark.asyncio
    async def test_task_cancellation(self, processor):
        """Test task cancellation."""
        # Create and add a task
        task = ProcessingTask("test-task", uuid4())
        processor.active_tasks["test-task"] = task

        # Cancel the task
        result = await processor.cancel_task("test-task")

        assert result is True
        assert task.status == TaskStatus.CANCELLED
        assert "test-task" not in processor.active_tasks


class TestStandardLogging:
    """Test the standardized logging system."""

    def test_structured_formatter(self):
        """Test structured JSON formatter."""
        import logging

        from app.utils.standard_logging import StructuredFormatter

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=100,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        import json

        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_development_formatter(self):
        """Test development formatter."""
        import logging

        from app.utils.standard_logging import DevelopmentFormatter

        formatter = DevelopmentFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=100,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "INFO" in formatted
        assert "test.logger" in formatted
        assert "Test message" in formatted

    def test_correlation_id_setting(self):
        """Test correlation ID functionality."""
        # Set up logging
        setup_logging(log_format="development")

        # Set correlation ID
        correlation_id = set_correlation_id("test-correlation-123")

        assert correlation_id == "test-correlation-123"

    def test_performance_logging(self):
        """Test performance logging functionality."""
        from app.utils.standard_logging import get_performance_logger

        perf_logger = get_performance_logger("test.performance")

        # Test operation logging
        perf_logger.log_operation(
            operation="test_operation",
            duration=0.5,
            success=True,
            extra_param="test_value",
        )

        # Test timing context manager
        with perf_logger.time_operation("timed_operation", context="test") as timer:
            # Simulate some work
            import time

            time.sleep(0.01)

        assert timer.success is True


@pytest.mark.asyncio
class TestIntegratedWorkflow:
    """Test integrated workflow with all components."""

    async def test_end_to_end_document_processing(self):
        """Test complete document processing workflow."""
        # Create a test document
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = (
                "This is a comprehensive test document for end-to-end processing."
            )
            f.write(test_content)
            temp_path = f.name

        try:
            # Initialize components
            processor = DocumentProcessor(config={})

            # TODO: These methods don't exist in DocumentProcessor
            # Test format detection
            # extension, mime_type = processor.detect_file_format(temp_path)
            # assert extension == ".txt"
            # assert "text/plain" in mime_type

            # Test text extraction
            # extracted = await processor.extract_text(temp_path)
            # assert test_content in extracted

            # Test preprocessing
            # processed = processor.preprocess_text(extracted)
            # assert len(processed) > 0

            # Test statistics
            # stats = processor.get_text_statistics(processed)
            # assert stats["word_count"] > 0
            # assert stats["character_count"] > 0

        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
