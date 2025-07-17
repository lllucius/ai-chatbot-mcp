"""
Embedding service for vector operations and similarity calculations.

This service provides methods for generating embeddings, calculating similarities,
and managing vector operations for semantic search.

Generated on: 2025-07-14 03:10:09 UTC
Current User: lllucius
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for embedding generation and vector operations.

    This service handles text embedding generation, similarity calculations,
    and vector database operations for semantic search.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize embedding service.

        Args:
            db: Database session for vector operations
        """
        self.db = db
        self.openai_client = OpenAIClient()
        self.vector_dimension = settings.vector_dimension

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a text string.

        Args:
            text: Text to generate embedding for

        Returns:
            List[float]: Embedding vector or None if failed
        """
        print("=============== GENERATE EMBEDDING")
        try:
            if not text or not text.strip():
                return None

            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return None

            # Generate embedding using OpenAI
            embedding = await self.openai_client.create_embedding(
                text=cleaned_text,
                encoding_format="base64"
            )

            # Validate embedding dimensions
            if len(embedding) != self.vector_dimension:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.vector_dimension}, got {len(embedding)}"
                )
                return None

            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed for text: {e}")
            return None

    async def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List[Optional[List[float]]]: List of embedding vectors
        """
        try:
            if not texts:
                return []

            # Clean texts
            cleaned_texts = []
            text_indices = []

            for i, text in enumerate(texts):
                cleaned = self._clean_text(text)
                if cleaned:
                    cleaned_texts.append(cleaned)
                    text_indices.append(i)

            if not cleaned_texts:
                return [None] * len(texts)

            # Generate embeddings in batch
            embeddings = await self.openai_client.generate_embeddings_batch(
                cleaned_texts
            )

            # Map embeddings back to original indices
            result = [None] * len(texts)
            for i, embedding in enumerate(embeddings):
                original_index = text_indices[i]
                if len(embedding) == self.vector_dimension:
                    result[original_index] = embedding
                else:
                    logger.warning(
                        f"Embedding dimension mismatch for text {original_index}"
                    )

            return result

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [None] * len(texts)

    def compute_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            float: Cosine similarity (-1 to 1)
        """
        try:
            if not embedding1 or not embedding2:
                return 0.0

            if len(embedding1) != len(embedding2):
                logger.warning("Embedding dimension mismatch in similarity calculation")
                return 0.0

            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Clamp to valid range
            return float(np.clip(similarity, -1.0, 1.0))

        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0

    def compute_similarities_batch(
        self, query_embedding: List[float], embeddings: List[List[float]]
    ) -> List[float]:
        """
        Compute similarities between query and multiple embeddings.

        Args:
            query_embedding: Query embedding vector
            embeddings: List of embedding vectors to compare

        Returns:
            List[float]: List of similarity scores
        """
        try:
            if not query_embedding or not embeddings:
                return [0.0] * len(embeddings)

            similarities = []
            query_vec = np.array(query_embedding)
            query_norm = np.linalg.norm(query_vec)

            if query_norm == 0:
                return [0.0] * len(embeddings)

            for embedding in embeddings:
                if not embedding or len(embedding) != len(query_embedding):
                    similarities.append(0.0)
                    continue

                vec = np.array(embedding)
                vec_norm = np.linalg.norm(vec)

                if vec_norm == 0:
                    similarities.append(0.0)
                    continue

                similarity = np.dot(query_vec, vec) / (query_norm * vec_norm)
                similarities.append(float(np.clip(similarity, -1.0, 1.0)))

            return similarities

        except Exception as e:
            logger.error(f"Batch similarity computation failed: {e}")
            return [0.0] * len(embeddings)

    def _clean_text(self, text: str) -> str:
        """
        Clean and preprocess text for embedding generation.

        Args:
            text: Raw text to clean

        Returns:
            str: Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        cleaned = " ".join(text.strip().split())

        # Remove control characters
        cleaned = "".join(char for char in cleaned if ord(char) >= 32 or char in "\n\t")

        # Limit length (approximate token limit)
        max_chars = 30000  # Conservative estimate for ~8000 tokens
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
            # Try to break at sentence boundary
            last_period = cleaned.rfind(".")
            if last_period > max_chars * 0.8:
                cleaned = cleaned[: last_period + 1]

        return cleaned.strip()

    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding to unit length.

        Args:
            embedding: Embedding vector to normalize

        Returns:
            List[float]: Normalized embedding vector
        """
        try:
            vec = np.array(embedding)
            norm = np.linalg.norm(vec)

            if norm == 0:
                return embedding

            normalized = vec / norm
            return normalized.tolist()

        except Exception as e:
            logger.error(f"Embedding normalization failed: {e}")
            return embedding

    def validate_embedding(self, embedding: Optional[List[float]]) -> bool:
        """
        Validate embedding format and dimensions.

        Args:
            embedding: Embedding vector to validate

        Returns:
            bool: True if valid
        """
        if not embedding:
            return False

        if not isinstance(embedding, list):
            return False

        if len(embedding) != self.vector_dimension:
            return False

        try:
            # Check that all values are valid floats
            for val in embedding:
                if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val):
                    return False
            return True

        except Exception:
            return False

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about embeddings in the database.

        Returns:
            dict: Embedding statistics
        """
        try:
            from sqlalchemy import text

            # Count total embeddings
            result = await self.db.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
            )
            total_embeddings = result.scalar() or 0

            # Count documents with embeddings
            result = await self.db.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT document_id) 
                    FROM document_chunks 
                    WHERE embedding IS NOT NULL
                """
                )
            )
            documents_with_embeddings = result.scalar() or 0

            return {
                "total_embeddings": total_embeddings,
                "documents_with_embeddings": documents_with_embeddings,
                "vector_dimension": self.vector_dimension,
                "embedding_model": settings.openai_embedding_model,
            }

        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            return {
                "total_embeddings": 0,
                "documents_with_embeddings": 0,
                "vector_dimension": self.vector_dimension,
                "embedding_model": settings.openai_embedding_model,
            }
