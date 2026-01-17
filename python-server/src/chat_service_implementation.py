"""Chat service implementation for Bibliophage.

Provides streaming LLM chat with document context awareness.
Uses LangChain's streaming API for token-by-token responses.
"""

import logging
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from bibliophage.v1alpha3 import chat_pb2 as api
from database import get_database
from llm_access import DocumentContext, get_llm_client

logger = logging.getLogger(__name__)


class ChatServiceImplementation:
    """Implementation of ChatService with streaming support."""

    def __init__(self) -> None:
        """Initialize the chat service with database and LLM client."""
        self.db = get_database()
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

            # Send metadata chunk first (before tokens)
            metadata_chunk = self._build_metadata_chunk(context_documents)
            yield metadata_chunk

            # Build messages for LLM (system + history + user message)
            messages = self._build_llm_messages(
                user_message=request.message,
                context_documents=context_documents,
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
        self, document_ids: list[str],
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

    def _build_metadata_chunk(
        self, context_documents: list[DocumentContext],
    ) -> api.ChatResponseChunk:
        """Build metadata chunk with context document info."""
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
        conversation_history: list[api.ChatMessage],
        system_prompt: str | None,
    ) -> list:
        """Build LangChain message list with context and history."""
        messages = []

        # System prompt with context
        # TODO: Outputting the sources should not be done by the LLM by default (if the user specifically asks for it, that may be a different situation), because it is not good at that
        # and it adds another responsibility with the opportunity to get things wrong
        # by default, we should just have an expandable section below the messages in which all referenced documents and chunks are listed
        if system_prompt is None:
            system_prompt = (
                "You are a knowledgeable minion for tabletop RPG questions. "
                "Answer questions based on the provided context documents."
                "Cite which sources you're drawing from when appropriate. "
                "If the citation does not pertain to a document provided in the context, state this explicitly."
                "If the context does not contain enough information, say so clearly."
            )

        # Add context documents to system prompt
        if context_documents:
            context_text = self.llm._build_context_prompt(context_documents)  # noqa: SLF001
            system_prompt += f"\n\nContext Documents:\n{context_text}"

        messages.append(SystemMessage(content=system_prompt))

        # Add conversation history
        message_types = {"user": HumanMessage, "assistant": AIMessage}
        for msg in conversation_history:
            if msg.role in message_types:
                messages.append(message_types[msg.role](content=msg.content))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        return messages
