"""Database repository module for FerretDB/MongoDB operations.

This module provides a centralized interface for all database operations,
abstracting away PyMongo's async API and providing domain-specific methods for
documents.

Architecture:
- Singleton connection management (one AsyncMongoClient for the entire app)
- Domain-specific methods that speak the application's language
- Easy to mock for testing
- Single source of truth for all database operations

Usage:
    from database import get_database

    db = get_database()
    await db.store_document(document_id, name, ...)
    document = await db.get_document_by_id(document_id)
"""

import logging
from datetime import datetime
from typing import Any, Optional

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from config import get_settings

logger = logging.getLogger(__name__)


class DocumentDatabase:
    """Repository for document database operations.

    This class encapsulates all database interactions for the unified Document model,
    which handles both user-created content and PDF-sourced documents. Services should
    use this class instead of accessing the pymongo directly.
    """

    def __init__(self, mongo_client: AsyncMongoClient):
        """Initialize the database repository.

        Args:
            mongo_client: PyMongo async MongoDB client
        """
        self.client = mongo_client
        self.db = mongo_client.bibliophage
        self.documents_collection = self.db.documents

        logger.info("DocumentDatabase repository initialized")

    async def initialize_indexes(self):
        """Create database indexes for optimal query performance.

        This should be called once at application startup to ensure
        all necessary indexes exist.
        """
        # Document indexes
        await self.documents_collection.create_index([("name", ASCENDING)])
        await self.documents_collection.create_index([("systems", ASCENDING)])
        await self.documents_collection.create_index([("type", ASCENDING)])
        await self.documents_collection.create_index([("source_type", ASCENDING)])
        await self.documents_collection.create_index([("tags.name", ASCENDING)])
        await self.documents_collection.create_index([("created_at", DESCENDING)])

        logger.info("Database indexes created/verified")

    # ========================================================================
    # Document Operations
    # ========================================================================

    async def store_document(
        self,
        document_id: str,
        name: str,
        systems: list[str],
        source_type: str,
        content: str,
        doc_type: str,
        tags: list[dict[str, Any]],
        created_at: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Store a document in the database.

        Args:
            document_id: Unique identifier for the document
            name: Document name
            systems: List of RPG systems this document belongs to (must have at least one)
            source_type: Source type for authority weighting (e.g., CORE, SUPPLEMENT, GM_NOTES)
            content: Full document content (markdown for PDFs, plain text for notes)
            doc_type: Type of document (e.g., RULEBOOK, NOTE, ADVENTURE)
            tags: List of structured tags [{"name": str, "values": [str, ...]}]
            created_at: Document creation timestamp
            metadata: Optional metadata dict for file-based content with keys:
                - file_size: int (bytes)
                - publication_type: str (optional)
                - pdf: dict (optional) with loading_batch_count, vector_chunk_count, page_count

        Returns:
            The document_id of the stored document
        """
        # Create snippet for search results (max 200 characters)
        content_snippet = content[:200] + "..." if len(content) > 200 else content

        document = {
            "_id": document_id,
            "name": name,
            "systems": systems,
            "source_type": source_type,
            "content": content,
            "content_snippet": content_snippet,
            "type": doc_type,
            "character_count": len(content),
            "tags": tags,
            "created_at": created_at,
            "updated_at": created_at,
        }

        # Add metadata if provided (for file-based content)
        if metadata is not None:
            document["metadata"] = metadata

        await self.documents_collection.insert_one(document)
        logger.info(f"Document stored with ID: {document_id}")
        return document_id

    async def get_document_by_id(self, document_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a document by its ID.

        Args:
            document_id: The unique identifier of the document

        Returns:
            The document dictionary if found, None otherwise
        """
        document = await self.documents_collection.find_one({"_id": document_id})
        return document

    async def update_document(
        self,
        document_id: str,
        name: Optional[str] = None,
        systems: Optional[list[str]] = None,
        source_type: Optional[str] = None,
        content: Optional[str] = None,
        doc_type: Optional[str] = None,
        tags: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Update a document.

        Args:
            document_id: The document to update
            name: New name (if provided)
            systems: New systems list (if provided)
            source_type: New source type (if provided)
            content: New content (if provided)
            doc_type: New type (if provided)
            tags: New tags (if provided)
            metadata: New metadata (if provided)

        Returns:
            The updated document if found, None otherwise
        """
        updates = {"updated_at": datetime.now()}

        if name is not None:
            updates["name"] = name
        if systems is not None:
            updates["systems"] = systems
        if source_type is not None:
            updates["source_type"] = source_type
        if content is not None:
            updates["content"] = content
            updates["character_count"] = len(content)
            # Update snippet when content changes
            updates["content_snippet"] = (
                content[:200] + "..." if len(content) > 200 else content
            )
        if doc_type is not None:
            updates["type"] = doc_type
        if tags is not None:
            updates["tags"] = tags
        if metadata is not None:
            updates["metadata"] = metadata

        result = await self.documents_collection.find_one_and_update(
            {"_id": document_id},
            {"$set": updates},
            return_document=True,  # Return the updated document
        )

        return result

    async def search_documents(
        self,
        name_query: Optional[str] = None,
        content_query: Optional[str] = None,
        type_filter: Optional[str] = None,
        system_filters: Optional[list[str]] = None,
        tag_filters: Optional[list[dict[str, str]]] = None,
        page_size: int = 50,
        page_number: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search for documents with optional filters.

        Args:
            name_query: Text to search in document names (case-insensitive)
            content_query: Text to search in document content (case-insensitive)
            type_filter: Filter by document type
            system_filters: Filter by systems (returns documents where systems contains ANY of these)
            tag_filters: Filter by tags [{"name": str, "value": str}] (documents must match ALL)
            page_size: Number of results per page
            page_number: Page number (0-indexed)

        Returns:
            Tuple of (list of matching documents, total count)
        """
        query = {}

        if name_query:
            query["name"] = {"$regex": name_query, "$options": "i"}
        if content_query:
            query["content"] = {"$regex": content_query, "$options": "i"}
        if type_filter:
            query["type"] = type_filter
        if system_filters:
            # Match documents where systems array contains ANY of the specified values
            query["systems"] = {"$in": system_filters}
        if tag_filters:
            # Match documents that have ALL specified tag filters
            # Each filter checks: tag.name == name AND value in tag.values
            tag_conditions = []
            for tag_filter in tag_filters:
                tag_conditions.append(
                    {
                        "tags": {
                            "$elemMatch": {
                                "name": tag_filter["name"],
                                "values": tag_filter["value"],
                            }
                        }
                    }
                )
            if tag_conditions:
                query["$and"] = tag_conditions

        # Get total count
        total_count = await self.documents_collection.count_documents(query)

        # Get paginated results (excluding full content for list views)
        cursor = self.documents_collection.find(
            query,
            {"content": 0},  # Exclude content field for performance
        ).sort("created_at", DESCENDING)
        cursor.skip(page_number * page_size).limit(page_size)
        documents = await cursor.to_list(length=page_size)

        return documents, total_count

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID.

        Args:
            document_id: The document to delete

        Returns:
            True if document was deleted, False if not found
        """
        result = await self.documents_collection.delete_one({"_id": document_id})
        return result.deleted_count > 0

    # ========================================================================
    # Direct Collection Access (for special cases)
    # ========================================================================

    def get_documents_collection(self):
        """Get direct access to documents collection.

        Use this sparingly - only when you need operations not covered
        by the repository methods above.
        """
        return self.documents_collection


# ============================================================================
# Singleton Pattern - One database connection for the entire application
# ============================================================================

_database: Optional[DocumentDatabase] = None
_mongo_client: Optional[AsyncMongoClient] = None


def get_database() -> DocumentDatabase:
    """Get the application's database repository (singleton pattern).

    This is the main function services should use to access the database.
    It ensures only one PyMongo AsyncMongoClient connection is created for the
    entire application, which is more efficient than creating multiple connections.

    Returns:
        DocumentDatabase: The database repository instance

    Example:
        db = get_database()
        await db.store_document(...)
    """
    global _database, _mongo_client

    if _database is None:
        settings = get_settings()
        _mongo_client = AsyncMongoClient(str(settings.database.doc_db_url))
        _database = DocumentDatabase(_mongo_client)
        logger.info("Database connection initialized (singleton)")

    return _database


async def close_database():
    """Close the database connection.

    This should be called when the application shuts down to cleanly
    close the PyMongo AsyncMongoClient connection.
    """
    global _database, _mongo_client

    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _database = None
        logger.info("Database connection closed")
