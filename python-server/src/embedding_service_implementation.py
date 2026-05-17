"""Embedding service implementation.

Implements the EmbeddingService RPCs for chunk generation, embedding management,
and vector operations. Orchestrates chunking strategies and postgres_db.


In general, when we talk about a chunk, we mean the data + the metadata (i.e. the full thing as it is stored in the DB).
The boundary is the thing defining the chunk, but does not contain the data, it is only metadata. We use boundaries when we have
no need to fetch and mess with the actual data. Actually using this convention in all of the code is still a WIP...
"""

import logging
from dataclasses import dataclass
from typing import Any

import bibliophage.v1alpha3.embedding_pb2 as api
import chunking_strategies
from config import get_settings
from postgres_db import get_postgres_db

logger = logging.getLogger(__name__)


@dataclass
class BoundaryDiff:
    """Result of comparing desired boundaries against existing chunks."""

    to_embed: list[Any]  # ChunkBoundary protos
    to_delete: list[str]  # chunk_ids


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
        """Embed a document, reconciling against existing chunks when boundaries are provided.

        With desired_boundaries: compares against stored chunks by (start, end) position,
        skips unchanged chunks, deletes orphans, and embeds only new/modified boundaries.
        Without desired_boundaries: generates boundaries from config and replaces all chunks.
        """
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

        if request.desired_boundaries:
            return await self._reconcile_and_embed(
                request.document_id, content, list(request.desired_boundaries)
            )
        return await self._full_embed(request, content)

    # TODO: This function looks misplaced and at least partially redundant
    # DB stuff should live in the DB module
    # that way other modules can make use of it (background jobs, migrations, who knows what else)
    # The name should be get_chunks() or something like that according to our convention in the docstring
    # come up with something expressive
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

    # ── embed orchestration ──────────────────────────────────────────────
    # TODO: we should run embedding in the background

    async def _full_embed(
        self,
        request: api.EmbedDocumentRequest,
        content: str,
    ) -> api.EmbedDocumentResponse:
        """Full embed: drop all existing chunks, generate boundaries from config, embed everything."""

        # drop all existing chunks, because the user did not give us info which ones to keep
        await self.db.delete_document_chunks(request.document_id)

        # come up with our own boundaries based on the strategy selected by the user
        try:
            strategy = chunking_strategies.get_strategy(request.config.strategy)
            boundaries = await strategy.propose_chunks(
                content, request.config, request.document_id,
            )
        except Exception as e:
            logger.error(f"Error generating boundaries: {e}", exc_info=True)
            return api.EmbedDocumentResponse(
                success=False,
                message=f"Failed to generate boundaries: {e!s}",
            )

        try:
            embedded_count = await self.db.embed_chunks(
                document_id=request.document_id,
                chunks=self._boundaries_to_chunks(boundaries, content),
            )
        except Exception as e:
            logger.error(f"Error embedding chunks: {e}", exc_info=True)
            return api.EmbedDocumentResponse(
                success=False, message=f"Failed to embed chunks: {e!s}",
            )

        embedding_status = await self._build_embedding_status(request.document_id)
        return api.EmbedDocumentResponse(
            success=True,
            message=f"Embedded {embedded_count} chunks (full)",
            embedding_status=embedding_status,
        )

    async def _reconcile_and_embed(
        self,
        document_id: str,
        content: str,
        boundaries_desired: list[api.ChunkBoundary],
    ) -> api.EmbedDocumentResponse:
        """Compare desired boundaries against existing chunks and only embed the diff."""

        # TODO: This could do with some cleanup
        # I feel like it would be tidier to just always speak the language of the API in this case
        # even at the DB layer of our python code
        # This is a list of dicts
        boundaries_current = await self.db.get_boundaries_for_document(document_id)

        diff = self._diff_boundaries(boundaries_desired, boundaries_current)

        await self.db.delete_chunks_by_ids(diff.to_delete)

        logger.info(
            f"Reconcile for {document_id}: "
            f"{len(diff.to_embed)} to embed, "
            f"{len(diff.to_delete)} to delete, "
            f"{len(boundaries_desired) - len(diff.to_embed)} unchanged"
        )

        embedded_count = 0
        if diff.to_embed:
            try:
                embedded_count = await self.db.embed_chunks(
                    document_id=document_id,
                    chunks=self._boundaries_to_chunks(diff.to_embed, content),
                )
            except Exception as e:
                logger.error(f"Error embedding chunks: {e}", exc_info=True)
                return api.EmbedDocumentResponse(
                    success=False, message=f"Failed to embed chunks: {e!s}",
                )

        # TODO: Why do we do this here?
        embedding_status = await self._build_embedding_status(document_id)
        return api.EmbedDocumentResponse(
            success=True,
            message=f"Reconciled: embedded {embedded_count}, deleted {len(diff.to_delete)}",
            embedding_status=embedding_status,
        )

    @staticmethod
    def _diff_boundaries(
        boundaries_desired: list[api.ChunkBoundary],
        boundaries_current: list[dict[str, Any]],
    ) -> BoundaryDiff:
        """Determine which boundaries need embedding and which existing chunks need deletion."""
        # These are a list of ChunkBoundaries ...
        boundaries_to_embed = []

        # define a set of tuples, we match the exact pairings later
        # set theory, yaaaay
        desired_positions = {(i.char_start, i.char_end) for i in boundaries_desired}
        current_positions = {(i["start_position"], i["end_position"]) for i in boundaries_current}

        for i in boundaries_desired:
            if (i.char_start, i.char_end) in current_positions:
                # chunks that have the correct boundaries already do not need to be embedded
                pass
            else:
                boundaries_to_embed.append(i)

        chunk_ids_to_delete = []
        for i in boundaries_current:
            if (i["start_position"], i["end_position"]) in desired_positions:
                # chunks that have the correct boundaries already do not need to be deleted
                pass
            else:
                chunk_ids_to_delete.append(i["chunk_id"])

        return BoundaryDiff(to_embed=boundaries_to_embed, to_delete=chunk_ids_to_delete)


    @staticmethod
    def _boundaries_to_chunks(
        boundaries: list[api.ChunkBoundary],
        content: str,
    ) -> list[dict[str, Any]]:
        """Convert proto boundaries to chunk dicts for the DB layer.
        Populate chunk content via string slice of the parent document
        """
        return [
            {
                "content": content[i.char_start : i.char_end],
                "metadata": {
                    "char_start": i.char_start,
                    "char_end": i.char_end,
                    "description": i.description,
                },
            }
            for i in boundaries
        ]

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
