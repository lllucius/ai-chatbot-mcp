"""
File processing utilities for document content extraction using unstructured.

This module provides functions for extracting text content from various
file formats using the unstructured library for unified document processing
with streaming support and memory optimization.

Generated on: 2025-07-14 03:18:45 UTC
Current User: lllucius
"""

import asyncio
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

import psutil
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title

from ..core.exceptions import DocumentError, ValidationError

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Unified file processor using unstructured library for extracting text content 
    from various file formats.

    Supports PDF, DOCX, TXT, MD, RTF, HTML and more through unstructured's 
    auto-partitioning with optimized chunking and memory management.
    """

    def __init__(self, max_file_size: int = 50 * 1024 * 1024, chunk_size: int = 8192):
        """
        Initialize file processor with unstructured backend.

        Args:
            max_file_size: Maximum file size to process (50MB default)
            chunk_size: Chunk size for streaming operations (8KB default)
        """
        self.max_file_size = max_file_size
        self.chunk_size = chunk_size
        # Unstructured supports many formats, but some have constraints
        # Focus on the most commonly used and well-supported formats
        self.supported_types = {
            "pdf", "docx", "doc", "txt", "md", "rtf", "html", "htm", 
            "csv", "tsv", "xlsx", "xls", "pptx", "ppt", "odt", "epub",
            "xml", "eml", "msg"
        }
        
        # Formats that may need special handling
        self.text_formats = {"txt", "md", "csv", "tsv"}

    def _check_memory_usage(self) -> None:
        """Check if memory usage is too high and warn."""
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                logger.warning(f"High memory usage: {memory.percent}%")
                if memory.percent > 90:
                    raise MemoryError("System memory usage too high")
        except Exception as e:
            logger.debug(f"Memory check failed: {e}")

    def _validate_file(self, file_path: str) -> None:
        """Validate file before processing."""
        path = Path(file_path)

        if not path.exists():
            raise DocumentError(f"File not found: {file_path}")

        if not path.is_file():
            raise DocumentError(f"Path is not a file: {file_path}")

        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            raise DocumentError(
                f"File too large: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB"
            )

        if file_size == 0:
            raise DocumentError("File is empty")

    async def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from a file using unstructured library.

        Args:
            file_path: Path to the file
            file_type: File extension/type

        Returns:
            str: Extracted text content

        Raises:
            DocumentError: If extraction fails
            ValidationError: If file type not supported
        """
        # Validate file
        self._validate_file(file_path)

        file_type = file_type.lower().lstrip(".")

        if file_type not in self.supported_types:
            raise ValidationError(f"Unsupported file type: {file_type}")

        # Check memory before processing
        self._check_memory_usage()

        try:
            # Use unstructured to partition the document
            logger.info(f"Processing {file_type} file: {file_path}")
            
            # Run the potentially CPU-intensive operation in a thread pool
            elements = await asyncio.get_event_loop().run_in_executor(
                None, partition, file_path
            )

            if not elements:
                raise DocumentError("No content found in file")

            # Extract text from all elements
            text_content = []
            for element in elements:
                if hasattr(element, 'text') and element.text:
                    text_content.append(element.text.strip())

            content = "\n\n".join(text_content)

            if not content.strip():
                raise DocumentError("No text content found in file")

            logger.info(f"Successfully extracted {len(content)} characters from {file_path}")
            return content.strip()

        except Exception as partition_error:
            # Fallback for simple text files when unstructured fails
            if file_type in self.text_formats:
                logger.warning(f"Unstructured partitioning failed for {file_path}, trying simple text extraction: {partition_error}")
                try:
                    return await self._extract_simple_text(file_path)
                except Exception as text_error:
                    logger.error(f"Simple text extraction also failed for {file_path}: {text_error}")
                    raise DocumentError(f"Both unstructured and simple text extraction failed: {text_error}")
            else:
                raise DocumentError(f"Text extraction failed: {partition_error}")

        except MemoryError:
            logger.error(f"Out of memory processing {file_path}")
            raise DocumentError("File too large to process - insufficient memory")
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            raise DocumentError(f"Text extraction failed: {e}")

    async def extract_text_streaming(
        self, file_path: str, file_type: str
    ) -> AsyncIterator[str]:
        """
        Extract text content from a file using streaming for large files.

        Args:
            file_path: Path to the file
            file_type: File extension/type

        Yields:
            str: Text chunks as they are processed

        Raises:
            DocumentError: If extraction fails
            ValidationError: If file type not supported
        """
        # Validate file
        self._validate_file(file_path)

        file_type = file_type.lower().lstrip(".")

        if file_type not in self.supported_types:
            raise ValidationError(f"Unsupported file type: {file_type}")

        try:
            # For streaming, we'll partition and yield chunks incrementally
            elements = await asyncio.get_event_loop().run_in_executor(
                None, partition, file_path
            )

            chunk_size = 4096  # 4KB chunks
            current_chunk = ""

            for element in elements:
                if hasattr(element, 'text') and element.text:
                    element_text = element.text.strip()
                    if element_text:
                        current_chunk += element_text + "\n\n"
                        
                        # Yield chunks when they reach the target size
                        while len(current_chunk) >= chunk_size:
                            yield current_chunk[:chunk_size]
                            current_chunk = current_chunk[chunk_size:]
                            await asyncio.sleep(0)  # Allow other tasks

            # Yield any remaining content
            if current_chunk.strip():
                yield current_chunk.strip()

        except Exception as e:
            raise DocumentError(f"Streaming text extraction failed: {e}")

    async def _extract_simple_text(self, file_path: str) -> str:
        """
        Simple text extraction fallback for basic text files.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            str: Extracted text content
        """
        try:
            # Check file size before loading
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB limit for text files
                raise DocumentError("Text file too large (>100MB)")

            # Try multiple encodings
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

            for encoding in encodings:
                try:
                    # For large files, read in chunks to avoid memory issues
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        content_chunks = []
                        with open(file_path, "r", encoding=encoding) as file:
                            while True:
                                chunk = file.read(self.chunk_size)
                                if not chunk:
                                    break
                                content_chunks.append(chunk)
                                # Yield control periodically
                                if len(content_chunks) % 100 == 0:
                                    await asyncio.sleep(0)
                                    self._check_memory_usage()
                        return "".join(content_chunks)
                    else:
                        # Small files can be read normally
                        with open(file_path, "r", encoding=encoding) as file:
                            return file.read()
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, try binary mode and decode with errors='ignore'
            with open(file_path, "rb") as file:
                raw_content = file.read()
                return raw_content.decode("utf-8", errors="ignore")

        except Exception as e:
            raise DocumentError(f"Simple text extraction failed: {e}")

    async def extract_chunks(
        self, file_path: str, file_type: str, max_characters: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Extract structured chunks from a document using unstructured's chunking.

        Args:
            file_path: Path to the file
            file_type: File extension/type
            max_characters: Maximum characters per chunk

        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries with metadata

        Raises:
            DocumentError: If extraction fails
            ValidationError: If file type not supported
        """
        # Validate file
        self._validate_file(file_path)

        file_type = file_type.lower().lstrip(".")

        if file_type not in self.supported_types:
            raise ValidationError(f"Unsupported file type: {file_type}")

        try:
            # Use unstructured to partition the document
            logger.info(f"Extracting chunks from {file_type} file: {file_path}")
            
            # Run partitioning in thread pool
            elements = await asyncio.get_event_loop().run_in_executor(
                None, partition, file_path
            )

            if not elements:
                raise DocumentError("No content found in file")

            # Use unstructured's chunking functionality
            def chunk_elements():
                return chunk_by_title(elements, max_characters=max_characters)
            
            chunked_elements = await asyncio.get_event_loop().run_in_executor(
                None, chunk_elements
            )

            # Convert to structured format
            chunks = []
            for i, element in enumerate(chunked_elements):
                if hasattr(element, 'text') and element.text:
                    # Get metadata from element
                    metadata = {}
                    if hasattr(element, 'metadata') and element.metadata:
                        element_metadata = element.metadata
                        if hasattr(element_metadata, 'to_dict'):
                            metadata.update(element_metadata.to_dict())
                        elif isinstance(element_metadata, dict):
                            metadata.update(element_metadata)

                    chunks.append({
                        'text': element.text,
                        'chunk_index': i,
                        'character_count': len(element.text),
                        'metadata': metadata
                    })

            logger.info(f"Successfully extracted {len(chunks)} chunks from {file_path}")
            return chunks

        except Exception as e:
            logger.error(f"Chunk extraction failed for {file_path}: {e}")
            raise DocumentError(f"Chunk extraction failed: {e}")

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

            file_extension = file_path_obj.suffix.lower().lstrip(".")

            return {
                "filename": file_path_obj.name,
                "size": stat.st_size,
                "extension": file_extension,
                "mime_type": mime_type,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_supported": file_extension in self.supported_types,
                "supported_formats": list(self.supported_types)
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
