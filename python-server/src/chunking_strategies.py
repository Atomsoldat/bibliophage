"""Chunking strategy implementations for document content splitting.

This module provides various strategies for splitting document content into
chunks suitable for vector embedding. Each strategy offers different tradeoffs
between respecting document structure and maintaining consistent chunk sizes.

Architecture:
- Abstract base class (ChunkingStrategy) defines the interface
- Concrete strategies implement specific chunking algorithms
- Strategy registry provides factory pattern for strategy selection

Usage:
    from chunking_strategies import get_strategy
    from bibliophage.v1alpha3.embedding_pb2 import ChunkingStrategy, ChunkingConfig

    config = ChunkingConfig(
        strategy=ChunkingStrategy.MARKDOWN_STRUCTURE,
        max_heading_level=3
    )
    strategy = get_strategy(config.strategy)
    boundaries = await strategy.propose_chunks("document content", config, "doc-id")
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from langchain.text_splitter import RecursiveCharacterTextSplitter

from bibliophage.v1alpha3.embedding_pb2 import (
    ChunkBoundary,
    ChunkingConfig,
    MarkdownReference,
    PdfPageReference,
)
from bibliophage.v1alpha3.embedding_pb2 import (
    ChunkingStrategy as ChunkingStrategyEnum,
)

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """Internal representation of a chunk during processing."""

    char_start: int
    char_end: int
    content: str
    description: str
    heading_path: list[str] | None = None
    heading_level: int | None = None
    start_page: int | None = None
    end_page: int | None = None


# ABC -> Abstract Base Class
# This is the template all ChunkingStrategies have to
# fulfill
class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    async def propose_chunks(
        self,
        content: str,
        config: ChunkingConfig,
        document_id: str,
    ) -> list[ChunkBoundary]:
        """Generate chunk boundary proposals for the given content.

        Args:
            content: Document content to chunk
            config: Chunking configuration parameters
            document_id: Document identifier for generating chunk IDs

        Returns:
            List of ChunkBoundary protobuf messages with all metadata populated

        """


class TokenBasedStrategy(ChunkingStrategy):
    """Token-based chunking using RecursiveCharacterTextSplitter.

    This strategy splits content based on token counts with configurable overlap.
    It attempts to split at natural boundaries (paragraphs, sentences) while
    respecting the token limits.
    """

    async def propose_chunks(
        self,
        content: str,
        config: ChunkingConfig,
        document_id: str,
    ) -> list[ChunkBoundary]:
        """Split content into token-based chunks."""
        chunk_size = config.token_chunk_size if config.token_chunk_size else 512
        chunk_overlap = config.token_chunk_overlap if config.token_chunk_overlap else 50

        logger.info(
            "Splitting content with token-based strategy: chunk_size=%d, overlap=%d",
            chunk_size,
            chunk_overlap,
        )

        # LangChain's RecursiveCharacterTextSplitter splits on natural boundaries
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,  # Character count as proxy for tokens
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Split the content
        chunks = text_splitter.split_text(content)

        # Convert to ChunkBoundary messages
        boundaries: list[ChunkBoundary] = []
        current_pos = 0

        for i, chunk_text in enumerate(chunks):
            # Find actual position in content (accounting for overlap)
            chunk_start = content.find(chunk_text, current_pos)
            if chunk_start == -1:
                # Fallback if exact match not found
                chunk_start = current_pos
            chunk_end = chunk_start + len(chunk_text)

            # Generate preview (first 100 chars)
            preview = chunk_text[:100].strip()
            if len(chunk_text) > 100:
                preview += "..."

            # Description based on position
            description = f"Chunk {i + 1}"

            boundary = ChunkBoundary(
                char_start=chunk_start,
                char_end=chunk_end,
                token_start=i * chunk_size,  # Approximate token position
                token_end=(i + 1) * chunk_size,
                description=description,
                preview=preview,
            )

            boundaries.append(boundary)
            current_pos = chunk_start + 1  # Move forward for next search

        logger.info("Generated %d token-based chunks", len(boundaries))
        return boundaries


class MarkdownStructureStrategy(ChunkingStrategy):
    """Markdown structure-based chunking.

    This strategy splits content at heading boundaries, respecting the document's
    hierarchical structure. Chunks correspond to sections defined by headings.
    """

    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    async def propose_chunks(
        self,
        content: str,
        config: ChunkingConfig,
        document_id: str,
    ) -> list[ChunkBoundary]:
        """Split content at markdown heading boundaries."""
        max_level = config.max_heading_level if config.max_heading_level else 3

        logger.info(
            "Splitting content with markdown structure strategy: max_level=%d",
            max_level,
        )

        # Find all headings
        headings: list[tuple[int, int, int, str]] = []  # (pos, level, end_pos, text)
        for match in self._HEADING_PATTERN.finditer(content):
            level = len(match.group(1))  # Count # symbols
            if level <= max_level:
                heading_text = match.group(2).strip()
                headings.append((match.start(), level, match.end(), heading_text))

        # If no headings found, treat entire content as single chunk
        if not headings:
            logger.warning("No headings found, creating single chunk")
            return [
                ChunkBoundary(
                    char_start=0,
                    char_end=len(content),
                    description="Complete document",
                    preview=content[:100].strip()
                    + ("..." if len(content) > 100 else ""),
                    markdown_ref=MarkdownReference(
                        heading_path=[],
                        start_heading_level=0,
                    ),
                ),
            ]

        # Build chunks between headings
        chunks: list[ChunkData] = []
        heading_stack: list[tuple[int, str]] = []  # Stack of (level, text)

        for i, (pos, level, _end_pos, text) in enumerate(headings):
            # Update heading stack (pop higher or equal levels)
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, text))

            # Determine chunk boundaries
            chunk_start = pos
            chunk_end = headings[i + 1][0] if i + 1 < len(headings) else len(content)

            chunk_content = content[chunk_start:chunk_end]
            heading_path = [h[1] for h in heading_stack]

            chunks.append(
                ChunkData(
                    char_start=chunk_start,
                    char_end=chunk_end,
                    content=chunk_content,
                    description=text,
                    heading_path=heading_path,
                    heading_level=level,
                ),
            )

        # Convert to ChunkBoundary messages
        boundaries: list[ChunkBoundary] = []
        for i, chunk in enumerate(chunks):
            preview = chunk.content[:100].strip()
            if len(chunk.content) > 100:
                preview += "..."

            markdown_ref = None
            if chunk.heading_path and chunk.heading_level:
                markdown_ref = MarkdownReference(
                    heading_path=chunk.heading_path,
                    start_heading_level=chunk.heading_level,
                )

            boundary = ChunkBoundary(
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                description=chunk.description,
                preview=preview,
                markdown_ref=markdown_ref,
            )

            boundaries.append(boundary)

        logger.info("Generated %d markdown structure chunks", len(boundaries))
        return boundaries


class MarkdownWithTokenLimitStrategy(ChunkingStrategy):
    """Hybrid strategy combining markdown structure with token limits.

    This strategy respects markdown heading boundaries but splits large sections
    that exceed the token limit. Best of both worlds: structure-aware but prevents
    oversized chunks.
    """

    async def propose_chunks(
        self,
        content: str,
        config: ChunkingConfig,
        document_id: str,
    ) -> list[ChunkBoundary]:
        """Split content at headings, with token limit fallback."""
        max_chunk_size = config.token_chunk_size if config.token_chunk_size else 1000

        logger.info(
            "Splitting content with hybrid strategy: max_chunk_size=%d",
            max_chunk_size,
        )

        # First, split by markdown structure
        markdown_strategy = MarkdownStructureStrategy()
        initial_chunks = await markdown_strategy.propose_chunks(
            content,
            config,
            document_id,
        )

        # Then, split any oversized chunks using token-based approach
        final_boundaries: list[ChunkBoundary] = []
        chunk_counter = 0

        for chunk in initial_chunks:
            chunk_size = chunk.char_end - chunk.char_start

            if chunk_size <= max_chunk_size:
                # Chunk is within limit, keep as-is but update ID
                final_boundaries.append(chunk)
                chunk_counter += 1
            else:
                # Chunk too large, split it using token-based approach
                chunk_content = content[chunk.char_start : chunk.char_end]
                token_strategy = TokenBasedStrategy()

                # Create temporary config for token-based splitting
                temp_config = ChunkingConfig(
                    strategy=ChunkingStrategyEnum.TOKEN_BASED,
                    token_chunk_size=max_chunk_size,
                    token_chunk_overlap=50,
                )

                sub_chunks = await token_strategy.propose_chunks(
                    chunk_content,
                    temp_config,
                    document_id,
                )

                # Adjust positions and add to final list
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_id = f"{document_id}:chunk:{chunk_counter}"
                    sub_chunk.char_start += chunk.char_start
                    sub_chunk.char_end += chunk.char_start
                    sub_chunk.description = f"{chunk.description} (part {len(final_boundaries) - chunk_counter + 1})"

                    # Preserve markdown reference if available
                    if chunk.HasField("markdown_ref"):
                        sub_chunk.markdown_ref.CopyFrom(chunk.markdown_ref)

                    final_boundaries.append(sub_chunk)
                    chunk_counter += 1

        logger.info(
            "Generated %d hybrid chunks (from %d structural chunks)",
            len(final_boundaries),
            len(initial_chunks),
        )
        return final_boundaries


class PdfPageBasedStrategy(ChunkingStrategy):
    """PDF page-based chunking.

    This strategy splits content at PDF page markers (<!-- PAGE N -->).
    Useful for documents where page-level granularity is important.
    """

    _PAGE_MARKER_PATTERN = re.compile(r"<!--\s*PAGE\s+(\d+)\s*-->", re.IGNORECASE)

    async def propose_chunks(
        self,
        content: str,
        config: ChunkingConfig,
        document_id: str,
    ) -> list[ChunkBoundary]:
        """Split content at PDF page markers."""
        logger.info("Splitting content with PDF page-based strategy")

        # Find all page markers
        page_markers: list[tuple[int, int, int]] = []  # (pos, page_num, end_pos)
        for match in self._PAGE_MARKER_PATTERN.finditer(content):
            page_num = int(match.group(1))
            page_markers.append((match.start(), page_num, match.end()))

        # If no page markers found, fall back to single chunk
        if not page_markers:
            logger.warning("No page markers found, creating single chunk")
            return [
                ChunkBoundary(
                    char_start=0,
                    char_end=len(content),
                    description="Complete document (no page markers)",
                    preview=content[:100].strip()
                    + ("..." if len(content) > 100 else ""),
                ),
            ]

        # Build chunks between page markers
        boundaries: list[ChunkBoundary] = []

        for i, (pos, page_num, _end_pos) in enumerate(page_markers):
            chunk_start = pos
            chunk_end = (
                page_markers[i + 1][0] if i + 1 < len(page_markers) else len(content)
            )

            chunk_content = content[chunk_start:chunk_end]
            preview = chunk_content[:100].strip()
            if len(chunk_content) > 100:
                preview += "..."

            # Determine page range
            end_page = (
                page_markers[i + 1][1] - 1 if i + 1 < len(page_markers) else page_num
            )

            pdf_ref = PdfPageReference(
                start_page=page_num,
                end_page=end_page,
            )

            boundary = ChunkBoundary(
                char_start=chunk_start,
                char_end=chunk_end,
                description=f"Page {page_num}"
                + (f"-{end_page}" if end_page > page_num else ""),
                preview=preview,
                pdf_ref=pdf_ref,
            )

            boundaries.append(boundary)

        logger.info("Generated %d page-based chunks", len(boundaries))
        return boundaries


def get_strategy(strategy_enum: ChunkingStrategyEnum) -> ChunkingStrategy:
    """Factory function to get chunking strategy by enum value.

    Args:
        strategy_enum: ChunkingStrategy protobuf enum value

    Returns:
        Concrete ChunkingStrategy implementation

    Raises:
        ValueError: If strategy_enum is invalid, unspecified, or USER_DEFINED

    """
    strategy_map: dict[ChunkingStrategyEnum, type[ChunkingStrategy]] = {
        ChunkingStrategyEnum.TOKEN_BASED: TokenBasedStrategy,
        ChunkingStrategyEnum.MARKDOWN_STRUCTURE: MarkdownStructureStrategy,
        ChunkingStrategyEnum.MARKDOWN_WITH_TOKEN_LIMIT: MarkdownWithTokenLimitStrategy,
        ChunkingStrategyEnum.PDF_PAGE_BASED: PdfPageBasedStrategy,
    }

    if strategy_enum == ChunkingStrategyEnum.CHUNKING_STRATEGY_UNSPECIFIED:
        msg = "Chunking strategy not specified"
        raise ValueError(msg)

    if strategy_enum == ChunkingStrategyEnum.USER_DEFINED:
        msg = "USER_DEFINED strategy cannot generate boundaries - boundaries must be provided in the request"
        raise ValueError(msg)

    strategy_class = strategy_map.get(strategy_enum)
    if not strategy_class:
        msg = f"Unknown chunking strategy: {strategy_enum}"
        raise ValueError(msg)

    return strategy_class()
