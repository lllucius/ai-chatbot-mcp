"""
Enhanced Document Processor - Advanced document processing utilities using unstructured.

This module provides enhanced document processing capabilities including
language detection, text cleaning, document preprocessing, and integration
with the unstructured library for comprehensive document processing.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

import json
import logging
import re
import tempfile
from typing import Any, Dict, List, Optional
from pathlib import Path

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from unstructured.partition.auto import partition

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Enhanced document processor for text analysis and cleaning using unstructured.

    Provides functionality for language detection, text preprocessing,
    document processing, and integration with unstructured library.

    Args:
        config: Dictionary containing processor configuration options.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Define supported formats for backward compatibility with tests
        # Include json even though unstructured has constraints with it
        self.SUPPORTED_FORMATS = [
            ".txt", ".md", ".pdf", ".docx", ".doc", ".html", ".htm", 
            ".csv", ".tsv", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", 
            ".epub", ".xml", ".eml", ".msg", ".rtf", ".json"
        ]

    async def extract_text(self, file_path: str) -> str:
        """
        Extract text from document using unstructured library.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            str: Extracted text content
        """
        try:
            # Special handling for JSON files
            if file_path.endswith('.json'):
                return self._extract_json_text(file_path)
            
            # Use unstructured to partition the document
            elements = partition(file_path)
            
            # Extract text from all elements
            text_content = []
            for element in elements:
                if hasattr(element, 'text') and element.text:
                    text_content.append(element.text.strip())
            
            content = "\n\n".join(text_content)
            return content.strip()
            
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            # Fallback for simple text files
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            raise

    def _extract_json_text(self, file_path: str) -> str:
        """
        Extract text content from JSON files.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            str: Extracted text content from JSON values
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def extract_strings(obj, texts=[]):
            """Recursively extract string values from JSON object."""
            if isinstance(obj, dict):
                for value in obj.values():
                    extract_strings(value, texts)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item, texts)
            elif isinstance(obj, str):
                texts.append(obj)
            return texts
        
        text_values = extract_strings(data)
        return "\n\n".join(text_values)

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess and clean text with advanced normalization.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            str: Preprocessed and normalized text
        """
        if not text:
            return ""
        
        # Unicode normalization for smart quotes, dashes, etc.
        text = text.replace('"', '"').replace('"', '"')  # Smart quotes to regular
        text = text.replace(''', "'").replace(''', "'")  # Smart single quotes
        text = text.replace('—', '-').replace('–', '-')  # Em/en dashes to hyphen
        text = text.replace('…', '...')  # Ellipsis to three dots
        text = text.replace('\u00a0', ' ')  # Non-breaking space to regular space
        
        # Clean whitespace - multiple spaces to single
        text = re.sub(r'\s+', ' ', text)
        # Multiple newlines to double, but preserve structure
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Get comprehensive text statistics.
        
        Args:
            text: Text to analyze
            
        Returns:
            dict: Text statistics including counts and language
        """
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "line_count": 0,
                "paragraph_count": 0,
                "language": None
            }
        
        # Basic counts
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Language detection
        language = self.detect_language(text)
        
        return {
            "character_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "paragraph_count": max(1, paragraph_count),
            "language": language
        }

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of the given text.

        Args:
            text: The text to analyze for language detection.

        Returns:
            ISO 639-1 language code if detected, None if detection fails.
        """
        try:
            if not text or len(text.strip()) < 10:
                return None
            language = detect(text)
            logger.debug(f"Detected language: {language}")
            return language
        except LangDetectException as e:
            logger.debug(f"Language detection failed: {str(e)}")
            return None

    def process_document(self, document: str) -> Dict[str, Any]:
        """
        Process a document with language detection and text cleaning.

        Args:
            document: The document text to process.

        Returns:
            Dictionary containing original text, detected language, and cleaned text.
        """
        language = self.detect_language(document)
        result = {
            "original": document,
            "language": language,
            "cleaned": self.preprocess_text(document),
        }
        logger.info(f"Processed document result: {result}")
        return result

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text by removing extra whitespace.

        Args:
            text: The text to clean.

        Returns:
            Cleaned text with normalized whitespace.
        """
        cleaned = re.sub(r"\s+", " ", text).strip()
        logger.debug(f"Cleaned text: {cleaned}")
        return cleaned

    def save_processed(self, processed: Dict[str, Any], path: str) -> None:
        """
        Save processed document data to a JSON file.

        Args:
            processed: The processed document data to save.
            path: The file path where to save the data.
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(processed, f, ensure_ascii=False, indent=2)
            logger.info(f"Processed document saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save processed document: {str(e)}")
