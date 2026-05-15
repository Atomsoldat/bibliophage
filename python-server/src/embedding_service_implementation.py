"""Embedding service implementation.

Implements the EmbeddingService RPCs for chunk generation, embedding management,
and vector operations. This service orchestrates interactions between:
- DocumentDatabase (FerretDB) for chunk boundaries storage
- VectorDatabase (pgvector) for vector embeddings
- Chunking strategies for generating boundaries
"""

import logging
from typing import Any

from google.protobuf import timestamp_pb2

import bibliophage.v1alpha3.embedding_pb2 as api
import chunking_strategies
import postgres_vector_db
from config import get_settings
from postgres_document_db import get_document_db

logger = logging.getLogger(__name__)


class EmbeddingServiceImplementation:
    """Implementation of the EmbeddingService RPC interface."""

    def __init__(self):
        """Initialize the embedding service with database and config."""
        self.db = get_document_db()
        self.settings = get_settings()
        logger.info("Embedding service initialized")

    async def propose_chunks(
        self,
        request: api.ProposeChunksRequest,
        ctx,
    ) -> api.ProposeChunksResponse:
        """Generate chunk boundary proposals for a document.

        This RPC:
        1. Fetches the document content from the database
        2. Selects the appropriate chunking strategy
        3. Generates chunk boundaries
        4. Calculates statistics
        5. Returns proposals without storing them

        Args:
            request: ProposeChunksRequest with document_id and config
            ctx: RPC context

        Returns:
            ProposeChunksResponse with proposed boundaries and statistics

        """
        logger.info(f"ProposeChunks request for document: {request.document_id}")

        # Fetch document from database
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

        # Get chunking strategy and generate boundaries
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

        # Calculate statistics directly from protobuf objects
        chunk_sizes = [b.char_end - b.char_start for b in proto_boundaries]

        # Calculate statistics
        stats = api.ChunkStatistics()
        stats.total_chunks = len(chunk_sizes)
        stats.total_content_length = len(content)

        if chunk_sizes:
            stats.avg_chunk_size = sum(chunk_sizes) // len(chunk_sizes)
            stats.min_chunk_size = min(chunk_sizes)
            stats.max_chunk_size = max(chunk_sizes)
        else:
            stats.avg_chunk_size = 0
            stats.min_chunk_size = 0
            stats.max_chunk_size = 0

        # Build response
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
        """Embed a document with specified or generated boundaries.

        This RPC:
        1. Fetches the document content
        2. Uses provided boundaries OR generates them based on config
        3. Extracts chunk content from the document
        4. Generates embeddings via postgres_vector_db
        5. Marks embeddings as current

        Args:
            request: EmbedDocumentRequest with document_id, config, and optional boundaries
            ctx: RPC context

        Returns:
            EmbedDocumentResponse with embedding status

        """
        logger.info(f"EmbedDocument request for document: {request.document_id}")

        # Fetch document from database
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
            # Generate boundaries from config
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

        # Extract chunk content for embedding
        chunks_with_content = []
        for boundary in proto_boundaries:
            chunk_content = content[boundary.char_start : boundary.char_end]
            chunks_with_content.append(
                {
                    "chunk_id": boundary.chunk_id,
                    "content": chunk_content,
                    "metadata": {
                        "char_start": boundary.char_start,
                        "char_end": boundary.char_end,
                        "description": boundary.description,
                    },
                }
            )

        # Embed chunks in vector database
        try:
            embedded_count = await postgres_vector_db.embed_chunks(
                request.document_id,
                chunks_with_content,
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

        # Store chunk boundaries
        config_dict = self._proto_config_to_dict(request.config)
        boundaries_dicts = [self._proto_boundary_to_dict(b) for b in proto_boundaries]
        await self.db.store_chunk_boundaries(
            request.document_id,
            config_dict,
            boundaries_dicts,
        )

        # Mark embeddings as current
        await self.db.mark_embeddings_current(
            request.document_id,
            self.settings.embedding.embedding_model_name,
            embedded_count,
        )

        # Build embedding status response
        boundaries_doc = await self.db.get_chunk_boundaries(request.document_id)
        embedding_status = self._build_embedding_status(
            boundaries_doc["embedding_status"]
        )

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
        """Retrieve existing chunk boundaries for a document.

        Args:
            request: GetChunkBoundariesRequest with document_id
            ctx: RPC context

        Returns:
            GetChunkBoundariesResponse with boundaries, config, and embedding status

        """
        logger.info(f"GetChunkBoundaries request for document: {request.document_id}")

        # Fetch chunk boundaries from database
        boundaries_doc = await self.db.get_chunk_boundaries(request.document_id)

        if boundaries_doc is None:
            return api.GetChunkBoundariesResponse(
                success=False,
                message=f"No chunk boundaries found for document {request.document_id}",
            )

        # Convert to protobuf
        proto_boundaries = []
        for chunk in boundaries_doc["chunk_boundaries"]:
            boundary = self._dict_to_proto_boundary(chunk)
            proto_boundaries.append(boundary)

        # Convert config
        config = self._dict_to_proto_config(boundaries_doc["chunking_config"])

        # Convert embedding status
        embedding_status = self._build_embedding_status(
            boundaries_doc["embedding_status"]
        )

        return api.GetChunkBoundariesResponse(
            success=True,
            message=f"Found {len(proto_boundaries)} chunk boundaries",
            boundaries=proto_boundaries,
            config=config,
            embedding_status=embedding_status,
        )

    async def update_chunk_boundaries(
        self,
        request: api.UpdateChunkBoundariesRequest,
        ctx,
    ) -> api.UpdateChunkBoundariesResponse:
        """Update chunk boundaries for a document (marks embeddings stale).

        This RPC:
        1. Validates the new boundaries (no gaps, no overlaps)
        2. Stores updated boundaries in FerretDB
        3. Marks embeddings as stale (embeddings_current = false)

        Args:
            request: UpdateChunkBoundariesRequest with document_id, boundaries, and config
            ctx: RPC context

        Returns:
            UpdateChunkBoundariesResponse with updated boundaries and status

        """
        logger.info(
            f"UpdateChunkBoundaries request for document: {request.document_id}"
        )

        # Validate document exists
        doc_data = await self.db.get_document_by_id(request.document_id)
        if doc_data is None:
            return api.UpdateChunkBoundariesResponse(
                success=False,
                message=f"Document with ID {request.document_id} not found",
            )

        # Validate boundaries (basic checks)
        try:
            self._validate_boundaries(request.boundaries, len(doc_data["content"]))
        except ValueError as e:
            return api.UpdateChunkBoundariesResponse(
                success=False,
                message=f"Invalid boundaries: {e!s}",
            )

        # Store updated boundaries in database (convert to dicts for storage)
        config_dict = self._proto_config_to_dict(request.config)
        boundaries_dicts = [self._proto_boundary_to_dict(b) for b in request.boundaries]
        await self.db.store_chunk_boundaries(
            request.document_id,
            config_dict,
            boundaries_dicts,
        )

        logger.info(
            f"Updated {len(request.boundaries)} boundaries for document {request.document_id}"
        )

        # Fetch updated status
        boundaries_doc = await self.db.get_chunk_boundaries(request.document_id)
        embedding_status = self._build_embedding_status(
            boundaries_doc["embedding_status"]
        )

        return api.UpdateChunkBoundariesResponse(
            success=True,
            message=f"Updated {len(chunk_boundaries)} chunk boundaries (embeddings marked stale)",
            boundaries=request.boundaries,
            embedding_status=embedding_status,
        )

    async def delete_embeddings(
        self,
        request: api.DeleteEmbeddingsRequest,
        ctx,
    ) -> api.DeleteEmbeddingsResponse:
        """Delete all embeddings for a document.

        This RPC:
        1. Deletes vector embeddings from pgvector
        2. Deletes chunk boundaries from FerretDB

        Args:
            request: DeleteEmbeddingsRequest with document_id
            ctx: RPC context

        Returns:
            DeleteEmbeddingsResponse with count of deleted chunks

        """
        logger.info(f"DeleteEmbeddings request for document: {request.document_id}")

        # Delete from vector database
        chunks_deleted = await postgres_vector_db.delete_document_chunks(
            request.document_id
        )

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

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _proto_config_to_dict(self, config: api.ChunkingConfig) -> dict[str, Any]:
        """Convert protobuf ChunkingConfig to dict for chunking strategies."""
        config_dict = {
            "strategy": api.ChunkingStrategy.Name(config.strategy),
        }

        if config.HasField("token_chunk_size"):
            config_dict["token_chunk_size"] = config.token_chunk_size
        if config.HasField("token_chunk_overlap"):
            config_dict["token_chunk_overlap"] = config.token_chunk_overlap
        if config.HasField("max_heading_level"):
            config_dict["max_heading_level"] = config.max_heading_level
        if config.HasField("config_version"):
            config_dict["config_version"] = config.config_version

        return config_dict

    def _dict_to_proto_config(self, config_dict: dict[str, Any]) -> api.ChunkingConfig:
        """Convert dict config to protobuf ChunkingConfig."""
        config = api.ChunkingConfig()

        # Convert strategy string to enum
        strategy_name = config_dict.get("strategy", "CHUNKING_STRATEGY_UNSPECIFIED")
        config.strategy = getattr(api, strategy_name, api.CHUNKING_STRATEGY_UNSPECIFIED)

        if "token_chunk_size" in config_dict:
            config.token_chunk_size = config_dict["token_chunk_size"]
        if "token_chunk_overlap" in config_dict:
            config.token_chunk_overlap = config_dict["token_chunk_overlap"]
        if "max_heading_level" in config_dict:
            config.max_heading_level = config_dict["max_heading_level"]
        if "config_version" in config_dict:
            config.config_version = config_dict["config_version"]

        return config

    def _proto_boundary_to_dict(self, boundary: api.ChunkBoundary) -> dict[str, Any]:
        """Convert protobuf ChunkBoundary to dict."""
        result = {
            "chunk_id": boundary.chunk_id,
            "char_start": boundary.char_start,
            "char_end": boundary.char_end,
            "description": boundary.description,
            "preview": boundary.preview,
        }

        if boundary.HasField("token_start"):
            result["token_start"] = boundary.token_start
        if boundary.HasField("token_end"):
            result["token_end"] = boundary.token_end

        if boundary.HasField("markdown_ref"):
            result["markdown_ref"] = {
                "heading_path": list(boundary.markdown_ref.heading_path),
                "start_heading_level": boundary.markdown_ref.start_heading_level,
            }

        if boundary.HasField("pdf_ref"):
            result["pdf_ref"] = {
                "start_page": boundary.pdf_ref.start_page,
                "end_page": boundary.pdf_ref.end_page,
            }

        return result

    def _dict_to_proto_boundary(self, chunk: dict[str, Any]) -> api.ChunkBoundary:
        """Convert dict chunk to protobuf ChunkBoundary."""
        boundary = api.ChunkBoundary()
        boundary.chunk_id = chunk["chunk_id"]
        boundary.char_start = chunk["char_start"]
        boundary.char_end = chunk["char_end"]
        boundary.description = chunk.get("description", "")
        boundary.preview = chunk.get("preview", "")

        if "token_start" in chunk:
            boundary.token_start = chunk["token_start"]
        if "token_end" in chunk:
            boundary.token_end = chunk["token_end"]

        if "markdown_ref" in chunk:
            md_ref = api.MarkdownReference()
            md_ref.heading_path.extend(chunk["markdown_ref"]["heading_path"])
            md_ref.start_heading_level = chunk["markdown_ref"]["start_heading_level"]
            boundary.markdown_ref.CopyFrom(md_ref)

        if "pdf_ref" in chunk:
            pdf_ref = api.PdfPageReference()
            pdf_ref.start_page = chunk["pdf_ref"]["start_page"]
            pdf_ref.end_page = chunk["pdf_ref"]["end_page"]
            boundary.pdf_ref.CopyFrom(pdf_ref)

        return boundary

    def _build_embedding_status(
        self, status_dict: dict[str, Any]
    ) -> api.EmbeddingStatus:
        """Convert dict embedding status to protobuf EmbeddingStatus."""
        status = api.EmbeddingStatus()
        status.is_embedded = status_dict.get("is_embedded", False)
        status.embeddings_current = status_dict.get("embeddings_current", False)
        status.total_chunks = status_dict.get("total_chunks", 0)

        if status_dict.get("embedded_at"):
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(status_dict["embedded_at"])
            status.embedded_at.CopyFrom(timestamp)

        if status_dict.get("embedding_model"):
            status.embedding_model = status_dict["embedding_model"]

        if status_dict.get("vector_collection"):
            status.vector_collection = status_dict["vector_collection"]

        return status

    def _validate_boundaries(
        self, boundaries: list[api.ChunkBoundary], content_length: int
    ):
        """Validate chunk boundaries for consistency.

        Checks:
        - Boundaries are sorted by char_start
        - No gaps between chunks
        - No overlaps between chunks
        - All boundaries within content length

        Args:
            boundaries: List of ChunkBoundary protobuf objects
            content_length: Total length of document content

        Raises:
            ValueError: If validation fails

        """
        if not boundaries:
            return

        # Sort by char_start
        sorted_boundaries = sorted(boundaries, key=lambda x: x.char_start)

        # Check each boundary
        for i, boundary in enumerate(sorted_boundaries):
            # Check within content bounds
            if boundary.char_start < 0 or boundary.char_end > content_length:
                raise ValueError(
                    f"Boundary {boundary.chunk_id} out of content bounds "
                    f"({boundary.char_start}-{boundary.char_end} vs 0-{content_length})",
                )

            # Check start < end
            if boundary.char_start >= boundary.char_end:
                raise ValueError(
                    f"Boundary {boundary.chunk_id} has invalid range "
                    f"({boundary.char_start}-{boundary.char_end})",
                )

            # Check for gaps and overlaps with next boundary
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
