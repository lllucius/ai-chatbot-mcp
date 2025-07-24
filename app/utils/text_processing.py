"Utility functions for text_processing operations."

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional
import psutil

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    "TextChunk class for specialized functionality."

    content: str
    start_char: int
    end_char: int
    chunk_index: int
    metainfo: Optional[Dict[(str, Any)]] = None


class TextProcessor:
    "TextProcessor class for specialized functionality."

    def __init__(
        self, chunk_size: int = 1000, chunk_overlap: int = 200, max_memory_mb: int = 500
    ):
        "Initialize class instance."
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_memory_mb = max_memory_mb

    def _check_memory_usage(self) -> None:
        "Check Memory Usage operation."
        try:
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            if memory.percent > 80:
                logger.warning(f"High memory usage: {memory.percent}%")
            if memory_mb > (self.max_memory_mb * 1024):
                raise MemoryError("Memory usage too high for text processing")
        except Exception as e:
            logger.debug(f"Memory check failed: {e}")

    async def create_chunks_streaming(
        self, text: str, metainfo: Optional[Dict[(str, Any)]] = None
    ) -> AsyncIterator[TextChunk]:
        "Create new chunks streaming."
        if (not text) or (not text.strip()):
            return
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return
        start_pos = 0
        chunk_index = 0
        while start_pos < len(cleaned_text):
            if (chunk_index % 100) == 0:
                self._check_memory_usage()
                (await asyncio.sleep(0))
            end_pos = start_pos + self.chunk_size
            if end_pos < len(cleaned_text):
                end_pos = self._find_break_point(cleaned_text, start_pos, end_pos)
            else:
                end_pos = len(cleaned_text)
            chunk_content = cleaned_text[start_pos:end_pos].strip()
            if chunk_content:
                chunk = TextChunk(
                    content=chunk_content,
                    start_char=start_pos,
                    end_char=end_pos,
                    chunk_index=chunk_index,
                    metainfo=metainfo,
                )
                (yield chunk)
                chunk_index += 1
            if end_pos >= len(cleaned_text):
                break
            start_pos = max((start_pos + 1), (end_pos - self.chunk_overlap))
            (await asyncio.sleep(0))

    def clean_text(self, text: str) -> str:
        "Clean Text operation."
        if not text:
            return ""
        text = re.sub("\\s+", " ", text)
        text = "".join(
            (char for char in text if ((ord(char) >= 32) or (char in "\n\t")))
        )
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub("\\n\\s*\\n\\s*\\n", "\n\n", text)
        return text.strip()

    def create_chunks(
        self, text: str, metainfo: Optional[Dict[(str, Any)]] = None
    ) -> List[TextChunk]:
        "Create new chunks."
        if (not text) or (not text.strip()):
            return []
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []
        chunks = []
        start_pos = 0
        chunk_index = 0
        while start_pos < len(cleaned_text):
            end_pos = start_pos + self.chunk_size
            if end_pos < len(cleaned_text):
                end_pos = self._find_break_point(cleaned_text, start_pos, end_pos)
            else:
                end_pos = len(cleaned_text)
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
            if end_pos >= len(cleaned_text):
                break
            start_pos = max((start_pos + 1), (end_pos - self.chunk_overlap))
        return chunks

    def _find_break_point(self, text: str, start_pos: int, end_pos: int) -> int:
        "Find Break Point operation."
        search_start = max(start_pos, (end_pos - 200))
        search_text = text[search_start:end_pos]
        sentence_endings = []
        for match in re.finditer("[.!?]+\\s+", search_text):
            pos = search_start + match.end()
            if pos < end_pos:
                sentence_endings.append(pos)
        if sentence_endings:
            return sentence_endings[(-1)]
        paragraph_breaks = []
        for match in re.finditer("\\n\\s*\\n", search_text):
            pos = search_start + match.start()
            if pos < end_pos:
                paragraph_breaks.append(pos)
        if paragraph_breaks:
            return paragraph_breaks[(-1)]
        line_breaks = []
        for match in re.finditer("\\n", search_text):
            pos = search_start + match.start()
            if pos < end_pos:
                line_breaks.append(pos)
        if line_breaks:
            return line_breaks[(-1)]
        word_boundaries = []
        for match in re.finditer("\\s+", search_text):
            pos = search_start + match.start()
            if pos < end_pos:
                word_boundaries.append(pos)
        if word_boundaries:
            return word_boundaries[(-1)]
        return end_pos

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        "Extract Keywords operation."
        if not text:
            return []
        cleaned = self.clean_text(text.lower())
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
        words = re.findall("\\b[a-zA-Z]{3,}\\b", cleaned)
        words = [word for word in words if (word not in stop_words)]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=(lambda x: x[1]), reverse=True)
        return [word for (word, freq) in sorted_words[:max_keywords]]

    def estimate_reading_time(self, text: str, words_per_minute: int = 200) -> int:
        "Estimate Reading Time operation."
        if not text:
            return 0
        word_count = len(text.split())
        reading_time = max(1, round((word_count / words_per_minute)))
        return reading_time

    def get_text_statistics(self, text: str) -> Dict[(str, Any)]:
        "Get text statistics data."
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
        char_count = len(cleaned)
        word_count = len(cleaned.split())
        sentence_count = len(re.findall("[.!?]+", cleaned))
        paragraph_count = len([p for p in cleaned.split("\n\n") if p.strip()])
        reading_time = self.estimate_reading_time(cleaned)
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
        "Truncate Text operation."
        if (not text) or (len(text) <= max_length):
            return text
        if not preserve_words:
            return text[:max_length].rstrip()
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > (max_length * 0.8):
            return truncated[:last_space].rstrip()
        else:
            return truncated.rstrip()
