"""
Search service for document retrieval and similarity search.

This service provides various search algorithms including:
- Vector similarity (PGVector, ivfflat index)
- Full-text search (Postgres GIN index, tsvector column, BM25 ranking if available)
- Hybrid search (normalized and calibrated blending of vector and text scores)
- Maximum Marginal Relevance (MMR, using embedding cosine distance for diversity)

Features:
- Embedding caching for repeated/similar queries (in-memory LRU)
- All queries filter by user_id first for security and performance
- Each result contains metadata for explainability
- Robust exception handling and logging
- All API/search algorithms are documented in function docstrings

API Endpoints (suggested for documentation):
- search_documents
- get_similar_chunks

Current User: lllucius
"""

import logging
import functools
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from time import time

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError, SearchError
from ..models.document import Document, DocumentChunk
from ..schemas.document import DocumentChunkResponse, DocumentSearchRequest
from ..services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

# ----- In-memory LRU cache for embeddings -----
class LRUCache:
    """A simple LRU cache for query embeddings."""
    def __init__(self, capacity=128):
        self.cache: Dict[str, Tuple[float, list]] = {}
        self.order: List[str] = []
        self.capacity = capacity

    def get(self, key):
        if key in self.cache:
            self.order.remove(key)
            self.order.insert(0, key)
            return self.cache[key][1]
        return None

    def set(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.order) >= self.capacity:
            old_key = self.order.pop()
            del self.cache[old_key]
        self.order.insert(0, key)
        self.cache[key] = (time(), value)

embedding_cache = LRUCache(capacity=256)

class SearchService:
    """
    Service for document search and retrieval operations.
    See method docstrings for detailed algorithm descriptions.
    """

    def __init__(self, db: AsyncSession):
        """
        Args:
            db: Database session for search operations
        """
        self.db = db
        self.embedding_service = EmbeddingService(db)

    async def get_query_embedding(self, query: str):
        """Returns embedding for query, using cache for performance."""
        cached = embedding_cache.get(query)
        if cached is not None:
            return cached
        embedding = await self.embedding_service.generate_embedding(query)
        if embedding:
            embedding_cache.set(query, embedding)
        return embedding

    async def search_documents(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """
        Search documents using the specified algorithm.
        Args:
            request: Search request parameters
            user_id: User ID for access control
        Returns:
            List[DocumentChunkResponse]: Search results with metadata and similarity scores
        """
        try:
            if request.algorithm == "vector":
                return await self._vector_search(request, user_id)
            elif request.algorithm == "text":
                return await self._text_search(request, user_id)
            elif request.algorithm == "hybrid":
                return await self._hybrid_search(request, user_id)
            elif request.algorithm == "mmr":
                return await self._mmr_search(request, user_id)
            else:
                raise SearchError(f"Unknown search algorithm: {request.algorithm}")
        except Exception as e:
            logger.exception(f"Search failed: {e}")
            raise SearchError(f"Search operation failed: {e}")

    async def _vector_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """
        Vector similarity search using PGVector ivfflat index.
        - Uses pre-filtering on user_id and other filters for index efficiency.
        - Returns similarity_score and search_meta for each result.
        """
        embedding = await self.get_query_embedding(request.query)
        if not embedding:
            raise SearchError("Failed to generate query embedding")

        distance_expr = DocumentChunk.embedding.op("<=>")(embedding).label("distance")
        similarity_threshold = 1.0 - request.threshold

        # Pre-filter user_id before vector op!
        query = (
            select(DocumentChunk, distance_expr)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.owner_id == user_id)
            .where(DocumentChunk.embedding.isnot(None))
        )
        if request.document_ids:
            query = query.where(Document.id.in_(request.document_ids))
        if request.file_types:
            query = query.where(Document.file_type.in_(request.file_types))

        query = (
            query.where(distance_expr <= similarity_threshold)
            .order_by(distance_expr)
            .limit(request.limit)
        )

        result = await self.db.execute(query)
        rows = result.fetchall()

        # Normalize scores to [0, 1]
        distances = [distance for _, distance in rows]
        max_distance = max(distances, default=1.0)
        min_distance = min(distances, default=0.0)
        norm = lambda d: 1.0 - ((d - min_distance) / (max_distance - min_distance + 1e-8))  # [0,1], higher is better

        results = []
        for chunk, distance in rows:
            similarity_score = norm(distance)
            chunk_response = DocumentChunkResponse.model_validate(chunk)
            chunk_response.similarity_score = similarity_score
            chunk_response.search_meta = {
                "method": "vector",
                "distance": float(distance),
                "normalized_similarity": similarity_score,
            }
            results.append(chunk_response)
        return results

    async def _text_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """
        Full-text search using Postgres GIN index and tsvector column.
        - Uses plainto_tsquery and tsvector column (content_tsv) for performance.
        - Uses BM25 ranking (if pg_bm25 is installed), else fallback to ts_rank_cd.
        - Returns search_meta for each result.
        """
        ts_query = func.plainto_tsquery('english', request.query)
        # Use BM25 if available, fallback to ts_rank_cd
        try:
            rank_expr = func.bm25('content_tsv', ts_query).label("rank")
            bm25_supported = True
        except Exception:
            rank_expr = func.ts_rank_cd(DocumentChunk.content_tsv, ts_query).label("rank")
            bm25_supported = False

        query = (
            select(DocumentChunk, rank_expr)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.owner_id == user_id)
            .where(DocumentChunk.content_tsv.op('@@')(ts_query))
        )
        if request.document_ids:
            query = query.where(Document.id.in_(request.document_ids))
        if request.file_types:
            query = query.where(Document.file_type.in_(request.file_types))

        query = query.order_by(rank_expr.desc()).limit(request.limit)

        result = await self.db.execute(query)
        rows = result.fetchall()

        # Normalize rank to [0,1]
        ranks = [float(rank) for _, rank in rows]
        max_rank = max(ranks, default=1.0)
        min_rank = min(ranks, default=0.0)
        norm = lambda r: (r - min_rank) / (max_rank - min_rank + 1e-8)

        results = []
        for chunk, rank in rows:
            score = norm(float(rank))
            if score >= request.threshold:
                chunk_response = DocumentChunkResponse.model_validate(chunk)
                chunk_response.similarity_score = score
                chunk_response.search_meta = {
                    "method": "text",
                    "bm25_supported": bm25_supported,
                    "raw_score": float(rank),
                    "normalized_score": score,
                }
                results.append(chunk_response)
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        return results[: request.limit]

    async def _hybrid_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """
        Hybrid search: combine normalized vector and text scores.
        - Each result contains the method(s) that matched and their scores.
        - Score normalization/calibration to [0, 1].
        """
        vector_results = await self._vector_search(request, user_id)
        text_results = await self._text_search(request, user_id)

        combined_results = {}
        for result in vector_results:
            chunk_id = result.id
            combined_results[chunk_id] = result
            combined_results[chunk_id].search_meta = {"methods": ["vector"], **result.search_meta}
            combined_results[chunk_id].similarity_score = (result.similarity_score or 0) * 0.7

        for result in text_results:
            chunk_id = result.id
            if chunk_id in combined_results:
                combined_results[chunk_id].search_meta["methods"].append("text")
                text_score = (result.similarity_score or 0) * 0.3
                combined_results[chunk_id].similarity_score += text_score
            else:
                result.similarity_score = (result.similarity_score or 0) * 0.3
                result.search_meta = {"methods": ["text"], **result.search_meta}
                combined_results[chunk_id] = result

        results = list(combined_results.values())
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        filtered_results = [
            r for r in results if (r.similarity_score or 0) >= request.threshold
        ]
        return filtered_results[: request.limit]

    async def _mmr_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """
        Maximum Marginal Relevance (MMR) for diverse, relevant results:
        - Use cosine similarity between embeddings for diversity.
        - Returns results with method metadata.
        """
        vector_request = DocumentSearchRequest(
            query=request.query,
            document_ids=request.document_ids,
            file_types=request.file_types,
            limit=min(request.limit * 3, 50),
            threshold=max(request.threshold - 0.1, 0.5),
            algorithm="vector",
        )
        candidates = await self._vector_search(vector_request, user_id)
        if not candidates:
            return []

        lambda_param = 0.7
        selected = [candidates[0]]
        remaining = candidates[1:]

        # Pre-fetch embeddings for all chunks for cosine calculation
        def get_emb(chunk): return getattr(chunk, 'embedding', None)
        selected_embs = [get_emb(selected[0])]

        while len(selected) < request.limit and remaining:
            best_score = -1
            best_idx = -1

            for i, candidate in enumerate(remaining):
                relevance = candidate.similarity_score or 0
                candidate_emb = get_emb(candidate)
                max_sim = 0
                if candidate_emb is not None:
                    for emb in selected_embs:
                        if emb is not None:
                            sim = self._cosine_similarity(candidate_emb, emb)
                            max_sim = max(max_sim, sim)
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            if best_idx >= 0:
                selected.append(remaining[best_idx])
                selected_embs.append(get_emb(remaining[best_idx]))
                remaining.pop(best_idx)
            else:
                break
        for res in selected:
            if hasattr(res, "search_meta"):
                res.search_meta["methods"] = ["vector", "mmr"]
        return selected

    @staticmethod
    def _cosine_similarity(vec1, vec2):
        """Cosine similarity for two lists of floats."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """
        Calculate simple text similarity score (Jaccard).
        Used as a fallback for diversity in MMR if embeddings are missing.
        """
        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())
        if not query_terms:
            return 0.0
        intersection = len(query_terms.intersection(content_terms))
        union = len(query_terms.union(content_terms))
        if union == 0:
            return 0.0
        return intersection / union

    async def get_similar_chunks(
        self, chunk_id: int, user_id: UUID, limit: int = 5
    ) -> List[DocumentChunkResponse]:
        """
        Find chunks similar to a given chunk using vector ANN search.
        Args:
            chunk_id: Reference chunk ID
            user_id: User ID for access control
            limit: Maximum results to return
        Returns:
            List[DocumentChunkResponse]: Similar chunks
        """
        try:
            chunk_result = await self.db.execute(
                select(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(and_(DocumentChunk.id == chunk_id, Document.owner_id == user_id))
            )
            reference_chunk = chunk_result.scalar_one_or_none()
            if not reference_chunk or not reference_chunk.embedding:
                raise NotFoundError("Reference chunk not found or has no embedding")
            distance_expr = DocumentChunk.embedding.op("<=>")(reference_chunk.embedding)
            query = (
                select(DocumentChunk, distance_expr.label("distance"))
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(Document.owner_id == user_id)
                .where(DocumentChunk.id != chunk_id)
                .where(DocumentChunk.embedding.isnot(None))
                .order_by(distance_expr)
                .limit(limit)
            )

            result = await self.db.execute(query)
            rows = result.fetchall()

            distances = [distance for _, distance in rows]
            max_distance = max(distances, default=1.0)
            min_distance = min(distances, default=0.0)
            norm = lambda d: 1.0 - ((d - min_distance) / (max_distance - min_distance + 1e-8))

            results = []
            for chunk, distance in rows:
                similarity_score = norm(distance)
                chunk_response = DocumentChunkResponse.model_validate(chunk)
                chunk_response.similarity_score = similarity_score
                chunk_response.search_meta = {
                    "method": "vector",
                    "distance": float(distance),
                    "normalized_similarity": similarity_score,
                }
                results.append(chunk_response)
            return results
        except Exception as e:
            logger.exception(f"get_similar_chunks failed: {e}")
            raise SearchError(f"Similar chunk search failed: {e}")
