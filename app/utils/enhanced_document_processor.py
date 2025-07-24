"Utility functions for enhanced_document_processor operations."

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
    "DocumentProcessor class for specialized functionality."

    def __init__(self, config: Dict[(str, Any)]):
        "Initialize class instance."
        self.config = config
        self.SUPPORTED_FORMATS = [
            ".txt",
            ".md",
            ".pdf",
            ".docx",
            ".doc",
            ".html",
            ".htm",
            ".csv",
            ".tsv",
            ".xlsx",
            ".xls",
            ".pptx",
            ".ppt",
            ".odt",
            ".epub",
            ".xml",
            ".eml",
            ".msg",
            ".rtf",
            ".json",
        ]

    async def extract_text(self, file_path: str) -> str:
        "Extract Text operation."
        try:
            if file_path.endswith(".json"):
                return self._extract_json_text(file_path)
            elements = partition(file_path)
            text_content = []
            for element in elements:
                if hasattr(element, "text") and element.text:
                    text_content.append(element.text.strip())
            content = "\n\n".join(text_content)
            return content.strip()
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            if file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            raise

    def _extract_json_text(self, file_path: str) -> str:
        "Extract Json Text operation."
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def extract_strings(obj, texts=[]):
            "Extract Strings operation."
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
        "Preprocess Text operation."
        if not text:
            return ""
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(', "\'").replace(', "'")
        text = text.replace("—", "-").replace("–", "-")
        text = text.replace("…", "...")
        text = text.replace("\xa0", " ")
        text = re.sub("\\s+", " ", text)
        text = re.sub("\\n\\s*\\n\\s*\\n+", "\n\n", text)
        return text.strip()

    def get_text_statistics(self, text: str) -> Dict[(str, Any)]:
        "Get text statistics data."
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "line_count": 0,
                "paragraph_count": 0,
                "language": None,
            }
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split("\n"))
        paragraph_count = len([p for p in text.split("\n\n") if p.strip()])
        language = self.detect_language(text)
        return {
            "character_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "paragraph_count": max(1, paragraph_count),
            "language": language,
        }

    def detect_language(self, text: str) -> Optional[str]:
        "Detect Language operation."
        try:
            if (not text) or (len(text.strip()) < 10):
                return None
            language = detect(text)
            logger.debug(f"Detected language: {language}")
            return language
        except LangDetectException as e:
            logger.debug(f"Language detection failed: {str(e)}")
            return None

    def process_document(self, document: str) -> Dict[(str, Any)]:
        "Process document operations."
        language = self.detect_language(document)
        result = {
            "original": document,
            "language": language,
            "cleaned": self.preprocess_text(document),
        }
        logger.info(f"Processed document result: {result}")
        return result

    def clean_text(self, text: str) -> str:
        "Clean Text operation."
        cleaned = re.sub("\\s+", " ", text).strip()
        logger.debug(f"Cleaned text: {cleaned}")
        return cleaned

    def save_processed(self, processed: Dict[(str, Any)], path: str) -> None:
        "Save Processed operation."
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(processed, f, ensure_ascii=False, indent=2)
            logger.info(f"Processed document saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save processed document: {str(e)}")
