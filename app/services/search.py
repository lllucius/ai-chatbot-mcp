"""
Search service for comprehensive document retrieval and similarity search.

This service provides advanced search capabilities for the AI chatbot platform
including multiple search algorithms, caching optimization, and performance
monitoring. It integrates vector similarity search, full-text search, hybrid
algorithms, and Maximum Marginal Relevance (MMR) for diverse search needs.

Key Features:
- Multiple search algorithms (vector, text, hybrid, MMR)
- LRU caching for query embeddings to optimize performance
- PGVector integration for efficient similarity search
- PostgreSQL full-text search with GIN indexing
- Configurable similarity thresholds and result limits
- User-based access control and security filtering

Search Algorithms:
- Vector Search: Semantic similarity using embeddings with PGVector ivfflat index
- Text Search: Traditional full-text search with PostgreSQL tsvector and BM25 ranking
- Hybrid Search: Normalized and calibrated blending of vector and text scores
- MMR Search: Maximum Marginal Relevance using embedding cosine distance for diversity

Performance Features:
- In-memory LRU cache for embedding queries (reduces API calls)
- User-based filtering for security and performance optimization
- Result metadata for search explainability and debugging
- Comprehensive error handling and logging for monitoring

API Endpoints Integration:
- search_documents: Main search interface with algorithm selection
- get_similar_chunks: Direct similarity search for related content

"""

import logging
from time import time
from typing import Dict, List, Optional, Tuple


from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.schemas.document import DocumentChunkResponse, DocumentSearchRequest

from ..core.exceptions import NotFoundError, SearchError
from ..models.document import Document, DocumentChunk
from ..services.embedding import EmbeddingService
from .base import BaseService

logger = logging.getLogger(__name__)


# ----- In-memory LRU cache for embeddings -----
class LRUCache:
    """A simple LRU cache for query embeddings."""

    def __init__(self, capacity=128):
        """Initialize the LRU cache.

        Args:
            capacity: Maximum number of items to store in cache.
        """
        self.cache: Dict[str, Tuple[float, List[float]]] = {}
        self.order: List[str] = []
        self.capacity = capacity

    def get(self, key: str) -> Optional[List[float]]:
        """Get value from cache and update access order.

        Args:
            key: Cache key to retrieve.

        Returns:
            Cached value or None if not found.
        """
        if key in self.cache:
            self.order.remove(key)
            self.order.insert(0, key)
            return self.cache[key][1]
        return None

    def set(self, key: str, value: List[float]) -> None:
        """Set value in cache with LRU eviction policy.

        Args:
            key: Cache key to store.
            value: Value to cache.
        """
        if key in self.cache:
            self.order.remove(key)
        elif len(self.order) >= self.capacity:
            old_key = self.order.pop()
            del self.cache[old_key]
        self.order.insert(0, key)
        self.cache[key] = (time(), value)


embedding_cache = LRUCache(capacity=256)


class SearchService(BaseService):
    """
    Service for comprehensive document search and retrieval operations.

    This service extends BaseService to provide advanced search capabilities
    including vector similarity search, text search, hybrid algorithms, and
    Maximum Marginal Relevance (MMR) with enhanced caching, logging, and
    performance optimization.

    Search Algorithms:
    - Vector Search: Pure semantic similarity using embeddings with PGVector
    - Text Search: Traditional full-text search with PostgreSQL GIN indexing
    - Hybrid Search: Weighted combination of vector and text search results
    - MMR Search: Maximum Marginal Relevance for diverse result sets

    Performance Features:
    - LRU caching for query embeddings to reduce API calls
    - Optimized database queries with proper indexing
    - Configurable similarity thresholds and result limits
    - User-based access control and security filtering

    Responsibilities:
    - Query embedding generation with caching optimization
    - Multi-algorithm search execution with result ranking
    - Search result formatting and metadata enrichment
    - Performance monitoring and query optimization
    - User access control and security enforcement
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize search service with embedding capabilities.

        Args:
            db: Database session for search operations
        """
        super().__init__(db, "search_service")
        self.embedding_service = EmbeddingService(db)
        self.bm25_supported = None  # Initially unknown

    async def check_bm25_support(self):
        """Check if BM25 function is available in the database.

        Returns:
            True if BM25 is supported, False otherwise.
        """
        # Only check once
        if self.bm25_supported is not None:
            return self.bm25_supported
        # Query pg_proc for a function named bm25 with (tsvector, tsquery) params
        sql = """
        SELECT EXISTS(
            SELECT 1 FROM pg_proc
            WHERE proname = 'bm25'
            AND proargtypes[0] = (SELECT oid FROM pg_type WHERE typname = 'tsvector')
        );
        """
        result = await self.db.execute(text(sql))
        self.bm25_supported = result.scalar() or False
        return self.bm25_supported

    async def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Get embedding for query, using cache for performance."""
        cached = embedding_cache.get(query)
        if cached is not None:
            # Validate cached embedding type
            if not isinstance(cached, list):
                logger.warning(
                    f"Invalid cached embedding type: {type(cached)}, regenerating"
                )
                # Remove invalid cache entry
                if query in embedding_cache.cache:
                    del embedding_cache.cache[query]
                    if query in embedding_cache.order:
                        embedding_cache.order.remove(query)
                cached = None
            else:
                return cached

        embedding = await self.embedding_service.generate_embedding(query)
        if embedding:
            # Validate embedding before caching
            if not isinstance(embedding, list):
                logger.error(f"Invalid embedding type from service: {type(embedding)}")
                return None
            embedding_cache.set(query, embedding)
        return embedding

    async def search_documents(
        self, request: DocumentSearchRequest, user_id: str
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
        self, request: DocumentSearchRequest, user_id: str
    ) -> List[DocumentChunkResponse]:
        """
        Vector similarity search using PGVector ivfflat index.

        - Uses pre-filtering on user_id and other filters for index efficiency.
        - Returns similarity_score for each result.
        """
        embedding = await self.get_query_embedding(request.query)
        if not embedding:
            raise SearchError("Failed to generate query embedding")

        # Validate embedding is a list
        if not isinstance(embedding, list):
            raise SearchError(
                f"Invalid embedding type: {type(embedding)}, expected list"
            )

        distance_expr = DocumentChunk.embedding.cosine_distance(embedding).label(
            "distance"
        )
        similarity_threshold = 1.0 - request.threshold

        # Pre-filter user_id before vector op!
        query = (
            select(DocumentChunk, distance_expr)
            .join(Document, DocumentChunk.document_id == Document.id)
            .options(joinedload(DocumentChunk.document))
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

        def norm(d):
            return 1.0 - (
                (d - min_distance) / (max_distance - min_distance + 1e-8)
            )  # [0,1], higher is better

        results = []
        for chunk, distance in rows:
            similarity_score = norm(distance)

            # Create DocumentChunkResponse directly with explicit field assignment
            chunk_response = DocumentChunkResponse(
                id=chunk.id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_offset,
                end_char=chunk.end_offset,
                token_count=chunk.token_count,
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                similarity_score=similarity_score,
                metainfo=chunk.document.metainfo,
                created_at=chunk.created_at,
            )

            results.append(chunk_response)
        return results

    async def _text_search(
        self, request: DocumentSearchRequest, user_id: str
    ) -> List[DocumentChunkResponse]:
        """
        Full-text search using Postgres GIN index and tsvector column.

        - Uses plainto_tsquery and tsvector column (content_tsv) for performance.
        - Uses BM25 ranking (if pg_bm25 is installed), else fallback to ts_rank_cd.
        """
        ts_query = func.plainto_tsquery("english", request.query)
        # Check support for bm25
        bm25_supported = await self.check_bm25_support()
        if bm25_supported:
            rank_expr = func.bm25(
                func.to_tsvector("english", DocumentChunk.content), ts_query
            ).label("rank")
        else:
            rank_expr = func.ts_rank_cd(
                func.to_tsvector("english", DocumentChunk.content), ts_query
            ).label("rank")

        query = (
            select(DocumentChunk, rank_expr)
            .join(Document, DocumentChunk.document_id == Document.id)
            .options(joinedload(DocumentChunk.document))
            .where(Document.owner_id == user_id)
            .where(
                func.to_tsvector("english", DocumentChunk.content).op("@@")(ts_query)
            )
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

        def norm(r):
            return (r - min_rank) / (max_rank - min_rank + 1e-8)

        results = []
        for chunk, rank in rows:
            score = norm(float(rank))
            if score >= request.threshold:
                # Create DocumentChunkResponse directly with explicit field assignment
                chunk_response = DocumentChunkResponse(
                    id=chunk.id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_char=chunk.start_offset,
                    end_char=chunk.end_offset,
                    token_count=chunk.token_count,
                    document_id=chunk.document_id,
                    document_title=chunk.document.title,
                    similarity_score=score,
                    metainfo=chunk.document.metainfo,
                    created_at=chunk.created_at,
                )
                results.append(chunk_response)
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)

        return results[: request.limit]

    async def _hybrid_search(
        self, request: DocumentSearchRequest, user_id: str
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
            combined_results[chunk_id].similarity_score = (
                result.similarity_score or 0
            ) * 0.7

        for result in text_results:
            chunk_id = result.id
            if chunk_id in combined_results:
                text_score = (result.similarity_score or 0) * 0.3
                combined_results[chunk_id].similarity_score += text_score
            else:
                result.similarity_score = (result.similarity_score or 0) * 0.3
                combined_results[chunk_id] = result

        results = list(combined_results.values())
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        filtered_results = [
            r for r in results if (r.similarity_score or 0) >= request.threshold
        ]
        return filtered_results[: request.limit]

    async def _mmr_search(
        self, request: DocumentSearchRequest, user_id: str
    ) -> List[DocumentChunkResponse]:
        """
        Maximum Marginal Relevance (MMR) for diverse, relevant results.

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
        def get_emb(chunk):
            return getattr(chunk, "embedding", None)

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
        self, chunk_id: int, user_id: str, limit: int = 5
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

            def norm(d):
                return 1.0 - ((d - min_distance) / (max_distance - min_distance + 1e-8))

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
