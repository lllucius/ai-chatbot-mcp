"""
Text processing utilities for document chunking and analysis.

This module provides functions for text cleaning, chunking,
token counting, and other text processing operations with
streaming and memory optimization support.

Generated on: 2025-07-14 03:50:38 UTC
Current User: lllucius
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Data class for text chunks."""

    content: str
    start_char: int
    end_char: int
    chunk_index: int
    metainfo: Optional[Dict[str, Any]] = None


class TextProcessor:
    """
    Optimized text processing utilities for document analysis and chunking.

    This class provides methods for cleaning text, creating chunks with
    streaming support and memory optimization for large documents.
    """

    def __init__(
        self, chunk_size: int = 1000, chunk_overlap: int = 200, max_memory_mb: int = 500
    ):
        """
        Initialize text processor.

        Args:
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between consecutive chunks
            max_memory_mb: Maximum memory usage in MB before optimization
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_memory_mb = max_memory_mb

    def _check_memory_usage(self) -> None:
        """Check if memory usage is too high."""
        try:
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)

            if memory.percent > 80:
                logger.warning(f"High memory usage: {memory.percent}%")

            if memory_mb > self.max_memory_mb * 1024:  # Convert to bytes
                raise MemoryError("Memory usage too high for text processing")

        except Exception as e:
            logger.debug(f"Memory check failed: {e}")

    async def create_chunks_streaming(
        self, text: str, metainfo: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[TextChunk]:
        """
        Create text chunks with streaming support for memory optimization.

        Args:
            text: Input text to chunk
            metainfo: Optional metadata to include with chunks

        Yields:
            TextChunk: Individual text chunks

        Raises:
            MemoryError: If memory usage becomes too high
        """
        if not text or not text.strip():
            return

        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return

        start_pos = 0
        chunk_index = 0

        while start_pos < len(cleaned_text):
            # Check memory usage periodically
            if chunk_index % 100 == 0:
                self._check_memory_usage()
                await asyncio.sleep(0)  # Allow other tasks

            # Calculate end position
            end_pos = start_pos + self.chunk_size

            # If this is not the last chunk, try to break at a sentence boundary
            if end_pos < len(cleaned_text):
                end_pos = self._find_break_point(cleaned_text, start_pos, end_pos)
            else:
                end_pos = len(cleaned_text)

            # Extract chunk content
            chunk_content = cleaned_text[start_pos:end_pos].strip()

            if chunk_content:
                chunk = TextChunk(
                    content=chunk_content,
                    start_char=start_pos,
                    end_char=end_pos,
                    chunk_index=chunk_index,
                    metainfo=metainfo,
                )
                yield chunk
                chunk_index += 1

            # Calculate next start position with overlap
            if end_pos >= len(cleaned_text):
                break

            start_pos = max(start_pos + 1, end_pos - self.chunk_overlap)

            # Allow other coroutines to run
            await asyncio.sleep(0)

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text to clean

        Returns:
            str: Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove control characters except newlines and tabs
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive blank lines
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        return text.strip()

    def create_chunks(
        self, text: str, metainfo: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            metainfo: Optional metainfo to include with chunks

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text or not text.strip():
            return []

        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []

        chunks = []
        start_pos = 0
        chunk_index = 0

        while start_pos < len(cleaned_text):
            # Calculate end position
            end_pos = start_pos + self.chunk_size

            # If this is not the last chunk, try to break at a sentence boundary
            if end_pos < len(cleaned_text):
                end_pos = self._find_break_point(cleaned_text, start_pos, end_pos)
            else:
                end_pos = len(cleaned_text)

            # Extract chunk content
            chunk_content = cleaned_text[start_pos:end_pos].strip()

            if chunk_content:
                chunk = TextChunk(
                    content=chunk_content,
                    start_char=start_pos,
                    end_char=end_pos,
                    chunk_index=chunk_index,
                    metainfo=metainfo,
                )
                chunks.append(chunk)
                chunk_index += 1

            # Calculate next start position with overlap
            if end_pos >= len(cleaned_text):
                break

            start_pos = max(start_pos + 1, end_pos - self.chunk_overlap)

        return chunks

    def _find_break_point(self, text: str, start_pos: int, end_pos: int) -> int:
        """
        Find optimal break point for text chunking.

        Args:
            text: Full text
            start_pos: Start position of chunk
            end_pos: Proposed end position

        Returns:
            int: Optimal break point
        """
        # Look for sentence boundaries first
        search_start = max(start_pos, end_pos - 200)
        search_text = text[search_start:end_pos]

        # Look for sentence endings
        sentence_endings = []
        for match in re.finditer(r"[.!?]+\s+", search_text):
            pos = search_start + match.end()
            if pos < end_pos:
                sentence_endings.append(pos)

        if sentence_endings:
            return sentence_endings[-1]

        # Look for paragraph breaks
        paragraph_breaks = []
        for match in re.finditer(r"\n\s*\n", search_text):
            pos = search_start + match.start()
            if pos < end_pos:
                paragraph_breaks.append(pos)

        if paragraph_breaks:
            return paragraph_breaks[-1]

        # Look for line breaks
        line_breaks = []
        for match in re.finditer(r"\n", search_text):
            pos = search_start + match.start()
            if pos < end_pos:
                line_breaks.append(pos)

        if line_breaks:
            return line_breaks[-1]

        # Look for word boundaries
        word_boundaries = []
        for match in re.finditer(r"\s+", search_text):
            pos = search_start + match.start()
            if pos < end_pos:
                word_boundaries.append(pos)

        if word_boundaries:
            return word_boundaries[-1]

        # Fall back to original end position
        return end_pos

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text using simple frequency analysis.

        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to return

        Returns:
            List[str]: List of keywords
        """
        if not text:
            return []

        # Clean and normalize text
        cleaned = self.clean_text(text.lower())

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
        }

        # Extract words
        words = re.findall(r"\b[a-zA-Z]{3,}\b", cleaned)
        words = [word for word in words if word not in stop_words]

        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]

    def estimate_reading_time(self, text: str, words_per_minute: int = 200) -> int:
        """
        Estimate reading time for text.

        Args:
            text: Text to analyze
            words_per_minute: Average reading speed

        Returns:
            int: Estimated reading time in minutes
        """
        if not text:
            return 0

        word_count = len(text.split())
        reading_time = max(1, round(word_count / words_per_minute))
        return reading_time

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Get comprehensive text statistics.

        Args:
            text: Text to analyze

        Returns:
            dict: Text statistics
        """
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "reading_time_minutes": 0,
                "keywords": [],
            }

        cleaned = self.clean_text(text)

        # Basic counts
        char_count = len(cleaned)
        word_count = len(cleaned.split())

        # Sentence count (approximate)
        sentence_count = len(re.findall(r"[.!?]+", cleaned))

        # Paragraph count
        paragraph_count = len([p for p in cleaned.split("\n\n") if p.strip()])

        # Reading time
        reading_time = self.estimate_reading_time(cleaned)

        # Keywords
        keywords = self.extract_keywords(cleaned)

        return {
            "character_count": char_count,
            "word_count": word_count,
            "sentence_count": max(1, sentence_count),
            "paragraph_count": max(1, paragraph_count),
            "reading_time_minutes": reading_time,
            "keywords": keywords,
        }

    def truncate_text(
        self, text: str, max_length: int, preserve_words: bool = True
    ) -> str:
        """
        Truncate text to specified length.

        Args:
            text: Text to truncate
            max_length: Maximum length
            preserve_words: Whether to preserve word boundaries

        Returns:
            str: Truncated text
        """
        if not text or len(text) <= max_length:
            return text

        if not preserve_words:
            return text[:max_length].rstrip()

        # Find the last complete word within the limit
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")

        if last_space > max_length * 0.8:  # If we're not losing too much
            return truncated[:last_space].rstrip()
        else:
            return truncated.rstrip()
