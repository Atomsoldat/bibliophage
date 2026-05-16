"""Embedding service implementation.

Implements the EmbeddingService RPCs for chunk generation, embedding management,
and vector operations. Orchestrates chunking strategies and postgres_db.
"""

import logging
from typing import Any

import bibliophage.v1alpha3.embedding_pb2 as api
import chunking_strategies
from config import get_settings
from postgres_db import get_postgres_db

logger = logging.getLogger(__name__)


class EmbeddingServiceImplementation:
    """Implementation of the EmbeddingService RPC interface."""

    def __init__(self):
        self.db = get_postgres_db()
        self.settings = get_settings()
        logger.info("Embedding service initialized")

    async def propose_chunks(
        self,
        request: api.ProposeChunksRequest,
        ctx,
    ) -> api.ProposeChunksResponse:
        """Generate chunk boundary proposals without storing them."""
        logger.info(f"ProposeChunks request for document: {request.document_id}")

        doc_data = await self.db.get_document_by_id(request.document_id)
        if doc_data is None:
            return api.ProposeChunksResponse(
                success=False,
                message=f"Document with ID {request.document_id} not found",
            )

        content = doc_data["content"]
        if not content:
            return api.ProposeChunksResponse(
                success=False,
                message=f"Document {request.document_id} has no content to chunk",
            )

        try:
            strategy = chunking_strategies.get_strategy(request.config.strategy)
            proto_boundaries = await strategy.propose_chunks(
                content,
                request.config,
                request.document_id,
            )
        except ValueError as e:
            return api.ProposeChunksResponse(
                success=False,
                message=f"Invalid chunking strategy or config: {e!s}",
            )
        except Exception as e:
            logger.error(f"Error generating chunks: {e}", exc_info=True)
            return api.ProposeChunksResponse(
                success=False,
                message=f"Failed to generate chunks: {e!s}",
            )

        chunk_sizes = [b.char_end - b.char_start for b in proto_boundaries]

        stats = api.ChunkStatistics()
        stats.total_chunks = len(chunk_sizes)
        stats.total_content_length = len(content)
        if chunk_sizes:
            stats.avg_chunk_size = sum(chunk_sizes) // len(chunk_sizes)
            stats.min_chunk_size = min(chunk_sizes)
            stats.max_chunk_size = max(chunk_sizes)

        proposal = api.ChunkProposal()
        proposal.boundaries.extend(proto_boundaries)
        proposal.config.CopyFrom(request.config)
        proposal.statistics.CopyFrom(stats)

        return api.ProposeChunksResponse(
            success=True,
            message=f"Generated {len(proto_boundaries)} chunks",
            proposal=proposal,
        )

    async def embed_document(
        self,
        request: api.EmbedDocumentRequest,
        ctx,
    ) -> api.EmbedDocumentResponse:
        """Embed a document: chunk it, generate embeddings, store in document_chunks."""
        logger.info(f"EmbedDocument request for document: {request.document_id}")

        doc_data = await self.db.get_document_by_id(request.document_id)
        if doc_data is None:
            return api.EmbedDocumentResponse(
                success=False,
                message=f"Document with ID {request.document_id} not found",
            )

        content = doc_data["content"]
        if not content:
            return api.EmbedDocumentResponse(
                success=False,
                message=f"Document {request.document_id} has no content to embed",
            )

        # Determine chunk boundaries: use provided or generate
        if request.boundaries:
            logger.info(f"Using {len(request.boundaries)} provided boundaries")
            proto_boundaries = list(request.boundaries)
        else:
            logger.info("Generating boundaries from config")
            try:
                strategy = chunking_strategies.get_strategy(request.config.strategy)
                proto_boundaries = await strategy.propose_chunks(
                    content,
                    request.config,
                    request.document_id,
                )
            except Exception as e:
                logger.error(f"Error generating chunks: {e}", exc_info=True)
                return api.EmbedDocumentResponse(
                    success=False,
                    message=f"Failed to generate chunks: {e!s}",
                )

        # Build chunk dicts for postgres_db.embed_chunks
        chunks_for_db = []
        for boundary in proto_boundaries:
            chunk_content = content[boundary.char_start : boundary.char_end]
            chunks_for_db.append({
                "content": chunk_content,
                "metadata": {
                    "char_start": boundary.char_start,
                    "char_end": boundary.char_end,
                    "description": boundary.description,
                },
            })

        try:
            embedded_count = await self.db.embed_chunks(
                request.document_id,
                chunks_for_db,
            )
            logger.info(
                f"Embedded {embedded_count} chunks for document {request.document_id}"
            )
        except Exception as e:
            logger.error(f"Error embedding chunks: {e}", exc_info=True)
            return api.EmbedDocumentResponse(
                success=False,
                message=f"Failed to embed chunks: {e!s}",
            )

        embedding_status = await self._build_embedding_status(request.document_id)

        return api.EmbedDocumentResponse(
            success=True,
            message=f"Successfully embedded {embedded_count} chunks",
            embedding_status=embedding_status,
        )

    async def get_chunk_boundaries(
        self,
        request: api.GetChunkBoundariesRequest,
        ctx,
    ) -> api.GetChunkBoundariesResponse:
        """Retrieve existing chunk boundaries from document_chunks table."""
        logger.info(f"GetChunkBoundaries request for document: {request.document_id}")

        chunk_rows = await self.db.fetchall(
            "SELECT chunk_id, start_position, end_position, content, metadata "
            "FROM document_chunks WHERE document_id = %(document_id)s "
            "ORDER BY start_position",
            {"document_id": request.document_id},
        )

        if not chunk_rows:
            return api.GetChunkBoundariesResponse(
                success=False,
                message=f"No chunk boundaries found for document {request.document_id}",
            )

        proto_boundaries = []
        for row in chunk_rows:
            meta = row.get("metadata") or {}
            boundary = api.ChunkBoundary(
                chunk_id=str(row["chunk_id"]),
                char_start=row["start_position"],
                char_end=row["end_position"],
                description=meta.get("description", ""),
                preview=row["content"][:100] + "..." if len(row["content"]) > 100 else row["content"],
            )
            proto_boundaries.append(boundary)

        embedding_status = await self._build_embedding_status(request.document_id)

        # TODO: ChunkingConfig is not stored per-document yet — we return an empty config
        return api.GetChunkBoundariesResponse(
            success=True,
            message=f"Found {len(proto_boundaries)} chunk boundaries",
            boundaries=proto_boundaries,
            embedding_status=embedding_status,
        )

    async def update_chunk_boundaries(
        self,
        request: api.UpdateChunkBoundariesRequest,
        ctx,
    ) -> api.UpdateChunkBoundariesResponse:
        """Update chunk boundaries for a document.

        TODO: Re-implement against PostgreSQL. This would need to delete existing
        chunks and insert new boundary-only rows (without embeddings), effectively
        marking the document as needing re-embedding.
        """
        raise NotImplementedError(
            "UpdateChunkBoundaries is not yet implemented against PostgreSQL. "
            "This would need to delete existing chunks and insert new boundary-only "
            "rows (without embeddings), effectively marking the document as needing "
            "re-embedding."
        )

    async def delete_embeddings(
        self,
        request: api.DeleteEmbeddingsRequest,
        ctx,
    ) -> api.DeleteEmbeddingsResponse:
        """Delete all embeddings for a document."""
        logger.info(f"DeleteEmbeddings request for document: {request.document_id}")

        chunks_deleted = await self.db.delete_document_chunks(request.document_id)

        if chunks_deleted == 0:
            return api.DeleteEmbeddingsResponse(
                success=False,
                message=f"No embeddings found for document {request.document_id}",
                chunks_deleted=0,
            )

        return api.DeleteEmbeddingsResponse(
            success=True,
            message=f"Deleted {chunks_deleted} chunks",
            chunks_deleted=chunks_deleted,
        )

    # ── helpers ─────────────────────────────────────────────────────────

    async def _build_embedding_status(self, document_id: str) -> api.EmbeddingStatus:
        """Derive embedding status from what's actually in document_chunks."""
        total_chunks = await self.db.get_chunk_count(document_id)
        is_embedded = total_chunks > 0

        status = api.EmbeddingStatus(
            is_embedded=is_embedded,
            # TODO: embeddings_current is always True for now — we don't track
            # whether content changed since last embedding
            embeddings_current=is_embedded,
            total_chunks=total_chunks,
            embedding_model=self.settings.embedding.embedding_model_name,
            vector_collection="document_chunks",
        )
        return status

    def _validate_boundaries(
        self, boundaries: list[api.ChunkBoundary], content_length: int
    ):
        """Validate chunk boundaries for consistency."""
        if not boundaries:
            return

        sorted_boundaries = sorted(boundaries, key=lambda x: x.char_start)

        for i, boundary in enumerate(sorted_boundaries):
            if boundary.char_start < 0 or boundary.char_end > content_length:
                raise ValueError(
                    f"Boundary {boundary.chunk_id} out of content bounds "
                    f"({boundary.char_start}-{boundary.char_end} vs 0-{content_length})",
                )

            if boundary.char_start >= boundary.char_end:
                raise ValueError(
                    f"Boundary {boundary.chunk_id} has invalid range "
                    f"({boundary.char_start}-{boundary.char_end})",
                )

            if i < len(sorted_boundaries) - 1:
                next_boundary = sorted_boundaries[i + 1]
                if boundary.char_end < next_boundary.char_start:
                    raise ValueError(
                        f"Gap between chunks {boundary.chunk_id} and {next_boundary.chunk_id}",
                    )
                if boundary.char_end > next_boundary.char_start:
                    raise ValueError(
                        f"Overlap between chunks {boundary.chunk_id} and {next_boundary.chunk_id}",
                    )
