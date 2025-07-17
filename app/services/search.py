"""
Search service for document retrieval and similarity search.

This service provides various search algorithms including vector similarity,
text search, hybrid search, and Maximum Marginal Relevance (MMR) search.

Generated on: 2025-07-14 03:15:29 UTC
Current User: lllucius
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError, SearchError
from ..models.document import Document, DocumentChunk
from ..schemas.document import DocumentChunkResponse, DocumentSearchRequest
from ..services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for document search and retrieval operations.

    This service provides multiple search algorithms and handles
    document chunk retrieval with similarity scoring.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize search service.

        Args:
            db: Database session for search operations
        """
        self.db = db
        self.embedding_service = EmbeddingService(db)

    async def search_documents(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """
        Search documents using the specified algorithm.

        Args:
            request: Search request parameters
            user_id: User ID for access control

        Returns:
            List[DocumentChunkResponse]: Search results with similarity scores
        """
        #try:
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

        #except Exception as e:
        #    logger.error(f"Search failed: {e}")
        #    raise SearchError(f"Search operation failed: {e}")

    async def _vector_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """Perform vector similarity search."""
        print("VECTOR_SEARCH")

        # Generate query embedding
        embedding = await self.embedding_service.generate_embedding(request.query)
        if not embedding:
            raise SearchError("Failed to generate query embedding")
        print("EMBEDDING", embedding)
        print("TYPE", type(embedding))
        print("LELN", len(embedding))

        distance_expr = DocumentChunk.embedding.op("<=>")(embedding)
#query = select(Item.id, Item.name, (Item.embedding <=> query_vector).label('distance')).order_by('distance')
        distance_expr = DocumentChunk.embedding.op("<=>")(embedding).label("distance")
        # Build base query
        query = (
            select(
                DocumentChunk,
                distance_expr.label("distance")
            )
            .join(Document)
            .where(Document.owner_id == user_id)
            .where(DocumentChunk.embedding.isnot(None))
        )

        # Apply filters
        if request.document_ids:
            query = query.where(Document.id.in_(request.document_ids))

        if request.file_types:
            query = query.where(Document.file_type.in_(request.file_types))

        # Apply similarity threshold and order
        similarity_threshold = 1.0 - request.threshold  # Convert similarity to distance
        print("Simil", similarity_threshold)
        query = (
            query.where(
                distance_expr <= similarity_threshold
            )
            .order_by(distance_expr)
           .limit(request.limit)
        )

        query = (
            query.where(
                DocumentChunk.embedding.op("<=>")(embedding) <= 0.3
            )
            .order_by(DocumentChunk.embedding.op("<=>")(embedding))
            .limit(request.limit)
        )

        print("QUERY", query)
        # Execute query
        result = await self.db.execute(query)
        rows = result.fetchall()

        # Convert results
        results = []
        for chunk, distance in rows:
            similarity_score = 1.0 - distance  # Convert back to similarity
            chunk_response = DocumentChunkResponse.model_validate(chunk)
            chunk_response.similarity_score = similarity_score
            results.append(chunk_response)

        return results

    async def _text_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """Perform full-text search."""
        # Build text search query
        search_terms = request.query.lower().split()

        # Create LIKE conditions for each term
        conditions = []
        for term in search_terms:
            conditions.append(func.lower(DocumentChunk.content).like(f"%{term}%"))

        query = (
            select(DocumentChunk)
            .join(Document)
            .where(Document.owner_id == user_id)
            .where(and_(*conditions))
        )

        # Apply filters
        if request.document_ids:
            query = query.where(Document.id.in_(request.document_ids))

        if request.file_types:
            query = query.where(Document.file_type.in_(request.file_types))

        query = query.limit(request.limit)

        # Execute query
        result = await self.db.execute(query)
        chunks = result.scalars().all()

        # Calculate text similarity scores
        results = []
        for chunk in chunks:
            # Simple relevance scoring based on term frequency
            score = self._calculate_text_similarity(request.query, chunk.content)
            if score >= request.threshold:
                chunk_response = DocumentChunkResponse.model_validate(chunk)
                chunk_response.similarity_score = score
                results.append(chunk_response)

        # Sort by score and return
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        return results[: request.limit]

    async def _hybrid_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """Perform hybrid search combining vector and text search."""
        # Get vector search results
        vector_results = await self._vector_search(request, user_id)

        # Get text search results
        text_results = await self._text_search(request, user_id)

        # Combine and deduplicate results
        combined_results = {}

        # Add vector results with weight
        for result in vector_results:
            chunk_id = result.id
            combined_results[chunk_id] = result
            combined_results[chunk_id].similarity_score = (
                result.similarity_score or 0
            ) * 0.7

        # Add text results with weight
        for result in text_results:
            chunk_id = result.id
            if chunk_id in combined_results:
                # Average the scores
                current_score = combined_results[chunk_id].similarity_score or 0
                text_score = (result.similarity_score or 0) * 0.3
                combined_results[chunk_id].similarity_score = current_score + text_score
            else:
                combined_results[chunk_id] = result
                combined_results[chunk_id].similarity_score = (
                    result.similarity_score or 0
                ) * 0.3

        # Sort by combined score
        results = list(combined_results.values())
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)

        # Apply threshold filter
        filtered_results = [
            r for r in results if (r.similarity_score or 0) >= request.threshold
        ]

        return filtered_results[: request.limit]

    async def _mmr_search(
        self, request: DocumentSearchRequest, user_id: UUID
    ) -> List[DocumentChunkResponse]:
        """Perform Maximum Marginal Relevance search for diverse results."""
        # Start with vector search to get candidates
        vector_request = DocumentSearchRequest(
            query=request.query,
            document_ids=request.document_ids,
            file_types=request.file_types,
            limit=min(request.limit * 3, 50),  # Get more candidates
            threshold=max(
                request.threshold - 0.1, 0.5
            ),  # Lower threshold for candidates
            algorithm="vector",
        )

        candidates = await self._vector_search(vector_request, user_id)

        if not candidates:
            return []

        # MMR algorithm parameters
        lambda_param = 0.7  # Balance between relevance and diversity
        selected = []

        # Select first result (highest relevance)
        selected.append(candidates[0])
        remaining = candidates[1:]

        # Iteratively select diverse results
        while len(selected) < request.limit and remaining:
            best_score = -1
            best_idx = -1

            for i, candidate in enumerate(remaining):
                # Calculate relevance score
                relevance = candidate.similarity_score or 0

                # Calculate maximum similarity to already selected
                max_similarity = 0
                if selected:
                    # Simple text-based similarity for MMR
                    for selected_chunk in selected:
                        similarity = self._calculate_text_similarity(
                            candidate.content, selected_chunk.content
                        )
                        max_similarity = max(max_similarity, similarity)

                # MMR score
                mmr_score = (
                    lambda_param * relevance - (1 - lambda_param) * max_similarity
                )

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if best_idx >= 0:
                selected.append(remaining.pop(best_idx))
            else:
                break

        return selected

    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """Calculate simple text similarity score."""
        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())

        if not query_terms:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(query_terms.intersection(content_terms))
        union = len(query_terms.union(content_terms))

        if union == 0:
            return 0.0

        return intersection / union

    async def get_similar_chunks(
        self, chunk_id: int, user_id: UUID, limit: int = 5
    ) -> List[DocumentChunkResponse]:
        """
        Find chunks similar to a given chunk.

        Args:
            chunk_id: Reference chunk ID
            user_id: User ID for access control
            limit: Maximum results to return

        Returns:
            List[DocumentChunkResponse]: Similar chunks
        """
        # Get reference chunk
        chunk_result = await self.db.execute(
            select(DocumentChunk)
            .join(Document)
            .where(and_(DocumentChunk.id == chunk_id, Document.owner_id == user_id))
        )
        reference_chunk = chunk_result.scalar_one_or_none()

        if not reference_chunk or not reference_chunk.embedding:
            raise NotFoundError("Reference chunk not found or has no embedding")

        distance_expr = DocumentChunk.embedding.op("<=>")(reference_chunk.embedding)

        # Find similar chunks
        query = (
            select(
                DocumentChunk,
                distance_expr.label("distance")
            )
            .join(Document)
            .where(Document.owner_id == user_id)
            .where(DocumentChunk.id != chunk_id)  # Exclude the reference chunk
            .where(DocumentChunk.embedding.isnot(None))
            .order_by(distance_expr)
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.fetchall()

        # Convert results
        results = []
        for chunk, distance in rows:
            similarity_score = 1.0 - distance
            chunk_response = DocumentChunkResponse.model_validate(chunk)
            chunk_response.similarity_score = similarity_score
            results.append(chunk_response)

        return results
