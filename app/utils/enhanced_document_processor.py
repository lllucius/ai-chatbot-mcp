import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def detect_language(self, text: str) -> Optional[str]:
        try:
            language = detect(text)
            logger.debug(f"Detected language: {language}")
            return language
        except LangDetectException as e:
            logger.error(f"Language detection failed: {str(e)}")
            return None

    def process_document(self, document: str) -> Dict[str, Any]:
        language = self.detect_language(document)
        result = {
            "original": document,
            "language": language,
            "cleaned": self.clean_text(document)
        }
        logger.info(f"Processed document result: {result}")
        return result

    def clean_text(self, text: str) -> str:
        cleaned = re.sub(r'\s+', ' ', text).strip()
        logger.debug(f"Cleaned text: {cleaned}")
        return cleaned

    def save_processed(self, processed: Dict[str, Any], path: str) -> None:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(processed, f, ensure_ascii=False, indent=2)
            logger.info(f"Processed document saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save processed document: {str(e)}")
