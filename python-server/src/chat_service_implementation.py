"""Chat service implementation for Bibliophage.

Provides streaming LLM chat with document context awareness.
Uses LangChain's streaming API for token-by-token responses.
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import vector_operations
from bibliophage.v1alpha3 import chat_pb2 as api
from document_database_pg import get_document_db
from llm_access import DocumentContext, get_llm_client

logger = logging.getLogger(__name__)

# Default number of chunks to retrieve via vector search
DEFAULT_RETRIEVAL_TOP_K = 5


@dataclass
class RetrievedChunkInfo:
    """Information about a chunk retrieved via vector search."""

    chunk_id: str
    document_id: str
    document_name: str
    content: str
    similarity: float


class ChatServiceImplementation:
    """Implementation of ChatService with streaming support."""

    def __init__(self) -> None:
        """Initialize the chat service with database and LLM client."""
        self.db = get_document_db()
        self.llm = get_llm_client()
        logger.info("Chat service initialized")

    async def stream_chat(
        self,
        request: api.ChatRequest,
        # TODO: Find actual Connect RPC context type and add type hint
        # Disables: ANN001 (missing type annotation), ARG002 (unused argument)
        ctx,  # noqa: ANN001, ARG002
    ) -> AsyncIterator[api.ChatResponseChunk]:
        """Stream chat responses token-by-token using LangChain's astream.

        This is a server-streaming RPC that yields ChatResponseChunk messages
        as the LLM generates tokens.
        """
        logger.info("Received StreamChat request: %s...", request.message[:50])

        try:
            # Retrieve context documents if provided
            context_documents = []
            if request.context_document_ids:
                context_documents = await self._fetch_context_documents(
                    request.context_document_ids,
                )

            # Perform vector search if auto-retrieval is enabled (default: True)
            retrieved_chunks: list[RetrievedChunkInfo] = []
            enable_auto_retrieval = (
                request.enable_auto_retrieval
                if request.HasField("enable_auto_retrieval")
                else True
            )
            if enable_auto_retrieval:
                top_k = (
                    request.retrieval_top_k
                    if request.HasField("retrieval_top_k")
                    else DEFAULT_RETRIEVAL_TOP_K
                )
                retrieved_chunks = await self._fetch_retrieved_chunks(
                    query=request.message,
                    top_k=top_k,
                )
                logger.info(
                    "Retrieved %d chunks via vector search", len(retrieved_chunks)
                )

            # Send metadata chunk first (before tokens)
            metadata_chunk = self._build_metadata_chunk(
                context_documents, retrieved_chunks
            )
            yield metadata_chunk

            # Build messages for LLM (system + history + user message)
            messages = self._build_llm_messages(
                user_message=request.message,
                context_documents=context_documents,
                retrieved_chunks=retrieved_chunks,
                conversation_history=request.conversation_history,
                system_prompt=(
                    request.system_prompt if request.HasField("system_prompt") else None
                ),
            )

            # Stream tokens from LLM using astream
            async for chunk in self.llm.chat_model.astream(messages):
                # chunk.content contains the token text
                token_chunk = api.ChatResponseChunk(
                    type=api.TOKEN,
                    content=chunk.content,
                )
                yield token_chunk

            # Send completion chunk
            done_chunk = api.ChatResponseChunk(
                type=api.DONE,
                content="",
            )
            yield done_chunk

            logger.info("Chat streaming completed successfully")

        except Exception:
            logger.exception("Error during chat streaming")
            error_chunk = api.ChatResponseChunk(
                type=api.ERROR,
                content="An error occurred while generating the response.",
            )
            yield error_chunk

    async def _fetch_context_documents(
        self,
        document_ids: list[str],
    ) -> list[DocumentContext]:
        """Fetch and convert documents to DocumentContext format."""
        context_documents = []

        for doc_id in document_ids:
            doc_data = await self.db.get_document_by_id(doc_id)
            if not doc_data:
                logger.warning("Document %s not found in database", doc_id)
                continue

            context_documents.append(
                DocumentContext(
                    id=doc_data["_id"],
                    name=doc_data["name"],
                    content=doc_data["content"],
                    source_type=doc_data.get("source_type", "SOURCE_TYPE_UNSPECIFIED"),
                    document_type=doc_data["type"],
                ),
            )

        return context_documents

    async def _fetch_retrieved_chunks(
        self,
        query: str,
        top_k: int,
    ) -> list[RetrievedChunkInfo]:
        """Perform vector search and enrich results with document names."""
        try:
            search_results = await vector_operations.search_similar(
                query=query,
                top_k=top_k,
            )
        except Exception:
            logger.exception("Vector search failed")
            return []

        # Enrich with document names
        retrieved_chunks: list[RetrievedChunkInfo] = []
        for result in search_results:
            doc_id = result["document_id"]
            doc_data = await self.db.get_document_by_id(doc_id)
            doc_name = doc_data["name"] if doc_data else "Unknown Document"

            retrieved_chunks.append(
                RetrievedChunkInfo(
                    chunk_id=result["chunk_id"],
                    document_id=doc_id,
                    document_name=doc_name,
                    content=result["content"],
                    similarity=result["similarity"],
                ),
            )

        return retrieved_chunks

    def _build_metadata_chunk(
        self,
        context_documents: list[DocumentContext],
        retrieved_chunks: list[RetrievedChunkInfo],
    ) -> api.ChatResponseChunk:
        """Build metadata chunk with context document and retrieved chunk info."""
        metadata = api.ChunkMetadata(
            model=self.llm.chat_model.model,
            context_documents=[
                api.ContextDocumentInfo(
                    id=doc.id,
                    name=doc.name,
                    authority=doc.authority_weight,
                )
                for doc in context_documents
            ],
            retrieved_chunks=[
                api.RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    content=chunk.content,
                    similarity=chunk.similarity,
                )
                for chunk in retrieved_chunks
            ],
        )

        return api.ChatResponseChunk(
            type=api.METADATA,
            content="",
            metadata=metadata,
        )

    def _build_llm_messages(
        self,
        user_message: str,
        context_documents: list[DocumentContext],
        retrieved_chunks: list[RetrievedChunkInfo],
        conversation_history: list[api.ChatMessage],
        system_prompt: str | None,
    ) -> list:
        """Build LangChain message list with context and history."""
        messages = []

        # System prompt with context
        if system_prompt is None:
            system_prompt = (
                "You are a knowledgeable assistent for tabletop RPG questions. "
                "If the context does not contain enough or incomplete information, say so clearly."
            )

        # Add context documents to system prompt (selected documents section)
        if context_documents:
            context_text = self.llm._build_context_prompt(context_documents)  # noqa: SLF001
            system_prompt += f"\n\n=== SELECTED DOCUMENTS ===\n{context_text}"

        # Add retrieved chunks (auto-retrieved excerpts section)
        if retrieved_chunks:
            excerpts = []
            for chunk in retrieved_chunks:
                relevance_pct = int(chunk.similarity * 100)
                excerpts.append(
                    f"--- From: {chunk.document_name} ({relevance_pct}% relevant) ---\n"
                    f"{chunk.content}",
                )
            system_prompt += (
                "\n\n=== RELEVANT EXCERPTS (Auto-Retrieved) ===\n"
                + "\n\n".join(excerpts)
            )

        messages.append(SystemMessage(content=system_prompt))

        # Add conversation history
        message_types = {"user": HumanMessage, "assistant": AIMessage}
        for msg in conversation_history:
            if msg.role in message_types:
                messages.append(message_types[msg.role](content=msg.content))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        return messages
