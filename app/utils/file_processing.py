"""
File processing utilities for document content extraction.

This module provides functions for extracting text content from various
file formats including PDF, DOCX, TXT, MD, and RTF files.

Generated on: 2025-07-14 03:18:45 UTC
Current User: lllucius
"""

import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict

from ..core.exceptions import DocumentError, ValidationError

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    File processor for extracting text content from various file formats.

    Supports PDF, DOCX, TXT, MD, RTF and other text-based formats.
    """

    def __init__(self):
        """Initialize file processor."""
        self.supported_types = {
            "pdf": self._extract_pdf,
            "docx": self._extract_docx,
            "txt": self._extract_text,
            "md": self._extract_text,
            "rtf": self._extract_rtf,
        }

    async def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from a file.

        Args:
            file_path: Path to the file
            file_type: File extension/type

        Returns:
            str: Extracted text content

        Raises:
            DocumentError: If extraction fails
            ValidationError: If file type not supported
        """
        if not Path(file_path).exists():
            raise DocumentError(f"File not found: {file_path}")

        file_type = file_type.lower().lstrip(".")

        if file_type not in self.supported_types:
            raise ValidationError(f"Unsupported file type: {file_type}")

        try:
            extractor = self.supported_types[file_type]
            content = await extractor(file_path)

            if not content.strip():
                raise DocumentError("No text content found in file")

            return content.strip()

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            raise DocumentError(f"Text extraction failed: {e}")

    async def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2

            text_content = []
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())

            return "\n\n".join(text_content)

        except ImportError:
            # Fallback to pypdf if PyPDF2 not available
            try:
                from pypdf import PdfReader

                text_content = []
                with open(file_path, "rb") as file:
                    pdf_reader = PdfReader(file)

                    for page in pdf_reader.pages:
                        text_content.append(page.extract_text())

                return "\n\n".join(text_content)

            except ImportError:
                raise DocumentError(
                    "PDF processing library not available. Install PyPDF2 or pypdf."
                )
        except Exception as e:
            raise DocumentError(f"PDF extraction failed: {e}")

    async def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document

            doc = Document(file_path)
            text_content = []

            # Extract paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))

            return "\n\n".join(text_content)

        except ImportError:
            raise DocumentError(
                "DOCX processing library not available. Install python-docx."
            )
        except Exception as e:
            raise DocumentError(f"DOCX extraction failed: {e}")

    async def _extract_text(self, file_path: str) -> str:
        """Extract text from plain text files (TXT, MD, etc)."""
        try:
            # Try multiple encodings
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, try binary mode and decode with errors='ignore'
            with open(file_path, "rb") as file:
                raw_content = file.read()
                return raw_content.decode("utf-8", errors="ignore")

        except Exception as e:
            raise DocumentError(f"Text file extraction failed: {e}")

    async def _extract_rtf(self, file_path: str) -> str:
        """Extract text from RTF file."""
        try:
            from striprtf.striprtf import rtf_to_text

            with open(file_path, "r", encoding="utf-8") as file:
                rtf_content = file.read()

            return rtf_to_text(rtf_content)

        except ImportError:
            raise DocumentError(
                "RTF processing library not available. Install striprtf."
            )
        except Exception as e:
            raise DocumentError(f"RTF extraction failed: {e}")

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get file information and metadata.

        Args:
            file_path: Path to the file

        Returns:
            dict: File information
        """
        try:
            file_path_obj = Path(file_path)

            # Get basic file info
            stat = file_path_obj.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path_obj))

            return {
                "filename": file_path_obj.name,
                "size": stat.st_size,
                "extension": file_path_obj.suffix.lower().lstrip("."),
                "mime_type": mime_type,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_supported": file_path_obj.suffix.lower().lstrip(".")
                in self.supported_types,
            }

        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {"filename": Path(file_path).name, "error": str(e)}

    def validate_file(self, file_path: str, max_size: int = 10485760) -> bool:
        """
        Validate file for processing.

        Args:
            file_path: Path to the file
            max_size: Maximum file size in bytes

        Returns:
            bool: True if file is valid

        Raises:
            ValidationError: If file is invalid
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise ValidationError("File does not exist")

        if not file_path_obj.is_file():
            raise ValidationError("Path is not a file")

        # Check file size
        if file_path_obj.stat().st_size > max_size:
            raise ValidationError(
                f"File size exceeds maximum allowed ({max_size} bytes)"
            )

        # Check file type
        file_type = file_path_obj.suffix.lower().lstrip(".")
        if file_type not in self.supported_types:
            raise ValidationError(f"File type '{file_type}' is not supported")

        return True
