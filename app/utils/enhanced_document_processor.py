"""
Enhanced Document Processor - Advanced document processing utilities.

This module provides enhanced document processing capabilities including
language detection, text cleaning, and document preprocessing.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

import re
import json
import logging
from typing import Dict, Any, Optional

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Enhanced document processor for text analysis and cleaning.
    
    Provides functionality for language detection, text preprocessing,
    and document processing with configurable options.
    
    Args:
        config: Dictionary containing processor configuration options.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of the given text.
        
        Args:
            text: The text to analyze for language detection.
            
        Returns:
            ISO 639-1 language code if detected, None if detection fails.
        """
        try:
            language = detect(text)
            logger.debug(f"Detected language: {language}")
            return language
        except LangDetectException as e:
            logger.error(f"Language detection failed: {str(e)}")
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
            "cleaned": self.clean_text(document)
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
        cleaned = re.sub(r'\s+', ' ', text).strip()
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
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(processed, f, ensure_ascii=False, indent=2)
            logger.info(f"Processed document saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save processed document: {str(e)}")
