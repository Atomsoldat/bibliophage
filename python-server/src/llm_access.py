"""LLM access module for Bibliophage.

Provides LLM operations with document source authority awareness.
Uses LangChain for provider abstraction (currently Ollama).
"""

import logging
from dataclasses import dataclass
from typing import Any

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings

logger = logging.getLogger(__name__)

# Singleton instance
_llm_client: "LLMClient | None" = None

# Authority weights determine how prominently documents appear in context
# Higher values = more authoritative sources
AUTHORITY_WEIGHTS: dict[str, float] = {
    "GM_NOTES": 1.2,
    "RULEBOOK": 1.0,
    "SUPPLEMENT": 0.9,
    "SESSION_LOG_RECORD": 0.6,
    "PLAYER_NOTES": 0.5,
    "GENERATED": 0.3,
    "COMMUNITY": 0.4,
    "SOURCE_TYPE_UNSPECIFIED": 0.5,
}

# Human-readable labels for source types
AUTHORITY_LABELS: dict[str, str] = {
    "RULEBOOK": "Official Rules",
    "SUPPLEMENT": "Official Supplement",
    "GM_NOTES": "GM Notes",
    "PLAYER_NOTES": "Player Notes",
    "SESSION_LOG_RECORD": "Session Log",
    "GENERATED": "LLM-Generated",
    "COMMUNITY": "Community Content",
}


@dataclass
class DocumentContext:
    """Represents a document with its content and metadata for LLM context."""

    content: str
    source_type: str  # Maps to SourceType enum value
    document_type: str  # Maps to DocumentType enum value
    name: str
    id: str

    @property
    def authority_weight(self) -> float:
        """Calculate authority weight based on source type."""
        return AUTHORITY_WEIGHTS.get(self.source_type, 0.5)


class LLMClient:
    """Singleton LLM client with context-aware operations."""

    def __init__(self) -> None:
        """Initialise LLM client with settings from config."""
        settings = get_settings()

        self.chat_model = ChatOllama(
            base_url=settings.ollama.ollama_url,
            model=settings.ollama.ollama_default_model,
            temperature=settings.ollama.ollama_temperature,
            num_predict=settings.ollama.ollama_max_tokens,
            timeout=settings.ollama.ollama_timeout,
        )

        logger.info(
            "Initialised LLM client: %s with model %s",
            settings.ollama.ollama_url,
            settings.ollama.ollama_default_model,
        )

    def _build_context_prompt(
        self, documents: list[DocumentContext], sort_by_authority: bool = True,
    ) -> str:
        """Build a formatted context string from documents.

        Args:
            documents: List of document contexts
            sort_by_authority: If True, sort by authority weight (highest first)

        Returns:
            Formatted context string with source attribution

        """
        if sort_by_authority:
            documents = sorted(
                documents,
                key=lambda d: d.authority_weight,
                reverse=True,
            )

        context_parts = []
        for doc in documents:
            # Format each document with clear source attribution
            authority_label = self._get_authority_label(doc.source_type)
            context_parts.append(
                f"--- Source: {doc.name} ({authority_label}) ---\n{doc.content}\n",
            )

        return "\n".join(context_parts)

    def _get_authority_label(self, source_type: str) -> str:
        """Get human-readable authority label for source type."""
        return AUTHORITY_LABELS.get(source_type, "Unknown Source")

    async def generate_content(
        self,
        prompt: str,
        context_documents: list[DocumentContext],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate new content based on context documents.

        Args:
            prompt: User's generation request
            context_documents: List of source documents for context
            system_prompt: Optional system prompt override

        Returns:
            Dict with 'content' (generated text) and 'metadata' (model info, etc.)

        """
        try:
            # Build context from documents
            context = self._build_context_prompt(context_documents)

            # Default system prompt emphasises source authority
            if system_prompt is None:
                system_prompt = (
                    "You are a creative assistant for tabletop RPG content generation. "
                    "Use the provided context documents to generate new content. "
                    "Prioritise information from Official Rules sources over other sources. "
                    "Be consistent with established lore and rules."
                )

            # Construct messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Context:\n{context}\n\nRequest: {prompt}"),
            ]

            # Generate
            response = await self.chat_model.ainvoke(messages)

            logger.info("Generated content for prompt: %s...", prompt[:50])

            return {
                "content": response.content,
                "metadata": {
                    "model": self.chat_model.model,
                    "source_documents": [doc.id for doc in context_documents],
                },
            }

        except Exception:
            logger.exception("Error generating content")
            raise

    async def summarise(
        self,
        content: str,
        max_length: int | None = None,
        style: str = "concise",
    ) -> dict[str, Any]:
        """Summarise text content.

        Args:
            content: Text to summarise
            max_length: Optional max length in words
            style: Summary style ('concise', 'detailed', 'bullet_points')

        Returns:
            Dict with 'summary' text and 'metadata'

        """
        try:
            # Build style-specific prompt
            style_instructions = {
                "concise": "Provide a brief, concise summary.",
                "detailed": "Provide a detailed summary covering key points.",
                "bullet_points": "Provide a summary as bullet points of key information.",
            }

            instruction = style_instructions.get(style, style_instructions["concise"])

            if max_length:
                instruction += f" Keep it under {max_length} words."

            messages = [
                SystemMessage(
                    content="You are a helpful assistant that summarises text.",
                ),
                HumanMessage(content=f"{instruction}\n\nText to summarise:\n{content}"),
            ]

            response = await self.chat_model.ainvoke(messages)

            logger.info(
                "Summarised content (%d chars -> %d chars)",
                len(content),
                len(response.content),
            )

            return {
                "summary": response.content,
                "metadata": {
                    "model": self.chat_model.model,
                    "style": style,
                    "original_length": len(content),
                },
            }

        except Exception:
            logger.exception("Error summarizing content")
            raise

    async def query_with_context(
        self,
        question: str,
        context_documents: list[DocumentContext],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Answer a question using context documents (RAG-style).

        Args:
            question: User's question
            context_documents: Relevant documents to draw answers from
            system_prompt: Optional system prompt override

        Returns:
            Dict with 'answer' and 'metadata' (including source document IDs)

        """
        try:
            # Build context
            context = self._build_context_prompt(context_documents)

            # Default system prompt for Q&A
            if system_prompt is None:
                system_prompt = (
                    "You are a knowledgeable assistant for tabletop RPG questions. "
                    "If the context does not contain enough or incomplete information, say so clearly."
                )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
            ]

            response = await self.chat_model.ainvoke(messages)

            logger.info("Answered query: %s...", question[:50])

            return {
                "answer": response.content,
                "metadata": {
                    "model": self.chat_model.model,
                    "source_documents": [
                        {
                            "id": doc.id,
                            "name": doc.name,
                            "authority": doc.authority_weight,
                        }
                        for doc in context_documents
                    ],
                },
            }

        except Exception:
            logger.exception("Error answering query")
            raise


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client  # noqa: PLW0603
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
