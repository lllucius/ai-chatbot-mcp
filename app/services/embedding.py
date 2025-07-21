"""
Embedding service for vector operations and similarity calculations.

This service provides methods for generating embeddings, calculating similarities,
and managing vector operations for semantic search, leveraging PGVector and PostgreSQL.

Embeddings are expected to be 1D dense float vectors of length `vector_dimension`
(as defined by DocumentChunk.embedding in the data model).
All values should be floats (typically in the range [-1, 1]), and no NaN or Inf values are allowed.

Generated on: 2025-07-20 05:16:05 UTC
Current User: lllucius
"""

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from ..config import settings
from ..services.openai_client import OpenAIClient
from ..models.document import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for embedding generation and vector operations,
    with direct integration to PGVector-powered Postgres similarity search.

    Args:
        db (AsyncSession): SQLAlchemy async session for database access.
        openai_client (Optional[OpenAIClient]): Client for generating embeddings. If not provided, a new instance is created.
        vector_dimension (Optional[int]): Expected dimension of embeddings. If not provided, inferred from DocumentChunk.
        batch_size (Optional[int]): Maximum API batch size for embedding generation.
        embedding_encoding (Optional[str]): Encoding format for embedding API.
    """

    def __init__(
        self,
        db: AsyncSession,
        openai_client: Optional[OpenAIClient] = None,
        vector_dimension: Optional[int] = None,
        batch_size: Optional[int] = None,
        embedding_encoding: Optional[str] = None,
    ):
        self.db: AsyncSession = db
        self.openai_client: OpenAIClient = openai_client or OpenAIClient()

        # Centralize dimension: model > settings > fallback
        self.vector_dimension: int = (
            vector_dimension
            or getattr(DocumentChunk.__table__.c.embedding.type, "dim", None)
            or getattr(settings, "vector_dimension", 3072)
        )
        self.batch_size: int = batch_size or getattr(settings, "embedding_batch_size", 100)
        self.embedding_encoding: str = embedding_encoding or getattr(settings, "embedding_encoding", "base64")
        self._embedding_cache: Dict[str, List[float]] = {}

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a text string.

        Args:
            text (str): Text to generate embedding for.

        Returns:
            Optional[List[float]]: Embedding vector (float32, shape [vector_dimension]) or None if failed.

        Notes:
            - Uses in-memory cache to avoid duplicate OpenAI API calls.
            - Validates embedding shape and type before returning.
        """
        if not text or not text.strip():
            return None

        cleaned_text: str = self._clean_text(text)
        if not cleaned_text:
            return None

        cache_key = cleaned_text
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            embedding = await self.openai_client.create_embedding(
                text=cleaned_text, encoding_format=self.embedding_encoding
            )
            embedding = self._ensure_float32_and_shape(embedding)
            if not self.validate_embedding(embedding):
                logger.warning(
                    f"Invalid embedding for text (len={len(embedding) if embedding else 'None'}): {cleaned_text[:50]}..."
                )
                return None

            self._embedding_cache[cache_key] = embedding
            return embedding

        except Exception as e:
            logger.error(
                f"Embedding generation failed for text: {e}", exc_info=True
            )
            return None

    async def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts (List[str]): List of texts to generate embeddings for.

        Returns:
            List[Optional[List[float]]]: List of embedding vectors (None if failed for corresponding input).

        Notes:
            - Uses in-memory cache per text.
            - Calls are chunked to avoid API overload (batch size configurable).
            - Validates and ensures shape/type for every output.
        """
        if not texts:
            return []

        cleaned_texts: List[str] = []
        text_indices: List[int] = []
        result: List[Optional[List[float]]] = [None] * len(texts)

        for i, text in enumerate(texts):
            cleaned = self._clean_text(text)
            if not cleaned:
                continue
            cache_key = cleaned
            if cache_key in self._embedding_cache:
                result[i] = self._embedding_cache[cache_key]
            else:
                cleaned_texts.append(cleaned)
                text_indices.append(i)

        if not cleaned_texts:
            return result

        try:
            for chunk_start in range(0, len(cleaned_texts), self.batch_size):
                chunk = cleaned_texts[chunk_start : chunk_start + self.batch_size]
                indices_chunk = text_indices[chunk_start : chunk_start + self.batch_size]
                embeddings = await self.openai_client.generate_embeddings_batch(chunk)
                for j, embedding in enumerate(embeddings):
                    idx = indices_chunk[j]
                    cleaned = chunk[j]
                    embedding = self._ensure_float32_and_shape(embedding)
                    if self.validate_embedding(embedding):
                        self._embedding_cache[cleaned] = embedding
                        result[idx] = embedding
                    else:
                        logger.warning(
                            f"Invalid embedding in batch for text idx {idx} (len={len(embedding) if embedding else 'None'})"
                        )
            return result

        except Exception as e:
            logger.error(
                f"Batch embedding generation failed: {e}", exc_info=True
            )
            return [None] * len(texts)

    def compute_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1 (List[float]): First embedding vector.
            embedding2 (List[float]): Second embedding vector.

        Returns:
            float: Cosine similarity in the range [-1, 1]. Returns 0.0 for invalid input.
        """
        if not embedding1 or not embedding2:
            return 0.0
        if len(embedding1) != len(embedding2):
            logger.warning("Embedding dimension mismatch in similarity calculation")
            return 0.0

        try:
            vec1 = np.array(embedding1, dtype=np.float32)
            vec2 = np.array(embedding2, dtype=np.float32)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(np.clip(similarity, -1.0, 1.0))
        except Exception as e:
            logger.error(
                f"Similarity computation failed: {e}", exc_info=True
            )
            return 0.0

    def compute_similarities_batch(
        self, query_embedding: List[float], embeddings: List[List[float]]
    ) -> List[float]:
        """
        Compute cosine similarities between a query embedding and multiple candidate embeddings.

        Args:
            query_embedding (List[float]): Query embedding vector.
            embeddings (List[List[float]]): List of embedding vectors to compare.

        Returns:
            List[float]: List of cosine similarity scores in the range [-1, 1].
                         Returns empty list if embeddings is empty.

        Notes:
            - Uses matrix vectorization for batch similarity calculation.
            - If a candidate embedding is invalid, result is 0.0 for that entry.
        """
        if not query_embedding or not embeddings:
            return []

        try:
            valid_mask = [
                emb and len(emb) == len(query_embedding) for emb in embeddings
            ]
            if not any(valid_mask):
                return [0.0] * len(embeddings)

            emb_matrix = np.array(
                [emb if emb and len(emb) == len(query_embedding) else np.zeros_like(query_embedding)
                 for emb in embeddings],
                dtype=np.float32
            )
            query_vec = np.array(query_embedding, dtype=np.float32)
            query_norm = np.linalg.norm(query_vec)
            emb_norms = np.linalg.norm(emb_matrix, axis=1)
            dot_products = np.dot(emb_matrix, query_vec)
            similarities = np.zeros(len(embeddings), dtype=np.float32)
            nonzero_mask = (emb_norms != 0) & (query_norm != 0)
            similarities[nonzero_mask] = dot_products[nonzero_mask] / (emb_norms[nonzero_mask] * query_norm)
            similarities = np.clip(similarities, -1.0, 1.0)
            similarities[~np.array(valid_mask)] = 0.0
            return similarities.tolist()
        except Exception as e:
            logger.error(
                f"Batch similarity computation failed: {e}", exc_info=True
            )
            return [0.0] * len(embeddings)

    def _clean_text(self, text: str) -> str:
        """
        Clean and preprocess text for embedding generation.

        Args:
            text (str): Raw text to clean.

        Returns:
            str: Cleaned text.

        Notes:
            - Removes excessive whitespace and control characters.
            - Truncates to a conservative max length (approx. 8000 tokens).
        """
        if not text:
            return ""
        cleaned = " ".join(text.strip().split())
        cleaned = "".join(
            char for char in cleaned if ord(char) >= 32 or char in "\n\t"
        )
        max_chars = 30000  # Conservative estimate for ~8000 tokens
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
            last_period = cleaned.rfind(".")
            if last_period > max_chars * 0.8:
                cleaned = cleaned[: last_period + 1]
        return cleaned.strip()

    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding to unit length.

        Args:
            embedding (List[float]): Embedding vector to normalize.

        Returns:
            List[float]: Normalized embedding vector. If norm is zero, returns original embedding.
        """
        try:
            vec = np.array(embedding, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm == 0:
                return embedding
            normalized = vec / norm
            return normalized.tolist()
        except Exception as e:
            logger.error(
                f"Embedding normalization failed: {e}", exc_info=True
            )
            return embedding

    def validate_embedding(self, embedding: Optional[List[float]]) -> bool:
        """
        Validate embedding format, type, and dimensions.

        Args:
            embedding (Optional[List[float]]): Embedding vector to validate.

        Returns:
            bool: True if valid, False otherwise.

        Notes:
            - Embedding must be a list of length self.vector_dimension and contain only floats/ints.
            - No NaN or Inf values allowed.
        """
        if not embedding or not isinstance(embedding, list):
            return False
        if len(embedding) != self.vector_dimension:
            return False
        try:
            for val in embedding:
                if not isinstance(val, (int, float)):
                    return False
                if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    return False
            return True
        except Exception:
            return False

    def _ensure_float32_and_shape(self, embedding: Optional[List[float]]) -> Optional[List[float]]:
        """
        Ensure the embedding is a float32 list of the correct shape.

        Args:
            embedding (Optional[List[float]]): Input embedding.

        Returns:
            Optional[List[float]]: Output embedding as float32 list with correct length, or None if invalid.
        """
        if embedding is None or not isinstance(embedding, list):
            return None
        arr = np.asarray(embedding, dtype=np.float32)
        if arr.shape != (self.vector_dimension,):
            return None
        return arr.tolist()

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about embeddings in the database.

        Returns:
            dict: Embedding statistics with fields:
                - total_embeddings (int): Total number of embeddings in DB.
                - documents_with_embeddings (int): Unique documents with embeddings.
                - vector_dimension (int): Dimension of embedding vectors.
                - embedding_model (str): Embedding model name.
        """
        try:
            total_embeddings = await self.db.scalar(
                select(func.count()).where(DocumentChunk.embedding != None)
            )
            documents_with_embeddings = await self.db.scalar(
                select(func.count(func.distinct(DocumentChunk.document_id))).where(
                    DocumentChunk.embedding != None
                )
            )
            return {
                "total_embeddings": total_embeddings or 0,
                "documents_with_embeddings": documents_with_embeddings or 0,
                "vector_dimension": self.vector_dimension,
                "embedding_model": getattr(settings, "openai_embedding_model", None),
            }
        except Exception as e:
            logger.error(
                f"Failed to get embedding stats: {e}", exc_info=True
            )
            return {
                "total_embeddings": 0,
                "documents_with_embeddings": 0,
                "vector_dimension": self.vector_dimension,
                "embedding_model": getattr(settings, "openai_embedding_model", None),
            }

    async def search_similar_chunks(
        self, query_embedding: List[float], top_k: int = 10
    ) -> List[DocumentChunk]:
        """
        Search for top_k most similar document chunks using PGVector in Postgres.

        Args:
            query_embedding (List[float]): Query embedding (must be length self.vector_dimension).
            top_k (int): Number of results to retrieve.

        Returns:
            List[DocumentChunk]: Ranked by cosine similarity (most similar first).

        Notes:
            - Uses PGVector's <-> operator for efficient cosine similarity in SQL.
            - Requires a suitable index (e.g., ivfflat/vector_cosine_ops) on document_chunks.embedding.
        """
        if not self.validate_embedding(query_embedding):
            logger.warning("Query embedding is invalid or wrong dimension for search_similar_chunks")
            return []
        try:
            # PGVector expects a python list of floats, matching the column type.
            sql = text("""
                SELECT * FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> :embedding
                LIMIT :top_k
            """)
            result = await self.db.execute(sql, {"embedding": query_embedding, "top_k": top_k})
            # If using SQLAlchemy 2.x, use scalars().all(); adjust as per version
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"Similarity search in Postgres failed: {e}", exc_info=True
            )
            return []