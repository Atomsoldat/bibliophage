"""Database repository module for FerretDB/MongoDB operations.

This module provides a centralized interface for all database operations,
abstracting away PyMongo's async API and providing domain-specific methods for
documents and PDFs.

Architecture:
- Singleton connection management (one AsyncMongoClient for the entire app)
- Domain-specific methods that speak the application's language
- Easy to mock for testing
- Single source of truth for all database operations

Usage:
    from database import get_database

    db = get_database()
    await db.store_pdf_document(pdf_id, metadata, batches)
    document = await db.get_pdf_by_id(pdf_id)
"""

import logging
from datetime import datetime
from typing import Any, Optional

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from config import get_settings

logger = logging.getLogger(__name__)


class DocumentDatabase:
    """Repository for document and PDF database operations.

    This class encapsulates all database interactions, providing domain-specific
    methods for working with documents and PDFs. Services should use this class
    instead of accessing Motor directly.
    """

    def __init__(self, mongo_client: AsyncMongoClient):
        """Initialize the database repository.

        Args:
            mongo_client: PyMongo async MongoDB client
        """
        self.client = mongo_client
        self.db = mongo_client.bibliophage
        self.documents_collection = self.db.documents
        self.pdfs_collection = self.db.pdfs

        logger.info("DocumentDatabase repository initialized")

    async def initialize_indexes(self):
        """Create database indexes for optimal query performance.

        This should be called once at application startup to ensure
        all necessary indexes exist.
        """
        # PDF document indexes
        await self.pdfs_collection.create_index([("name", ASCENDING)])
        await self.pdfs_collection.create_index([("system", ASCENDING)])
        await self.pdfs_collection.create_index([("type", ASCENDING)])
        await self.pdfs_collection.create_index([("tags", ASCENDING)])
        await self.pdfs_collection.create_index([("created_at", DESCENDING)])

        # Text document indexes
        await self.documents_collection.create_index([("name", ASCENDING)])
        await self.documents_collection.create_index([("type", ASCENDING)])
        await self.documents_collection.create_index([("tags", ASCENDING)])
        await self.documents_collection.create_index([("created_at", DESCENDING)])

        logger.info("Database indexes created/verified")

    # ========================================================================
    # PDF Document Operations
    # ========================================================================

    async def store_pdf_document(
        self,
        document_id: str,
        name: str,
        system: str,
        doc_type: str,
        origin_path: str,
        page_count: int,
        file_size: int,
        batches: list[dict[str, Any]],
        batch_config: dict[str, Any],
        use_smart_batching: bool,
        tags: list[str],
        created_at: datetime,
    ) -> str:
        """Store a PDF document with its processed batches in the database.

        Args:
            document_id: Unique identifier for the document
            name: Document name
            system: System the document belongs to
            doc_type: Type of document
            origin_path: Original file path
            page_count: Total number of pages
            file_size: Size of PDF file in bytes
            batches: List of processed batches with markdown content
            batch_config: Batch processing configuration used
            use_smart_batching: Whether smart batching was used
            tags: List of tags for the document
            created_at: Document creation timestamp

        Returns:
            The document_id of the stored document
        """
        successful_batches = sum(1 for b in batches if b.get('success'))
        failed_batches = len(batches) - successful_batches

        document = {
            '_id': document_id,
            'name': name,
            'system': system,
            'type': doc_type,
            'origin_path': origin_path,
            'page_count': page_count,
            'file_size': file_size,
            'batch_count': len(batches),
            'successful_batches': successful_batches,
            'failed_batches': failed_batches,
            'batches': batches,
            'batch_config': batch_config,
            'use_smart_batching': use_smart_batching,
            'created_at': created_at,
            'updated_at': created_at,
            'tags': tags,
        }

        await self.pdfs_collection.insert_one(document)
        logger.info(f"PDF document stored with ID: {document_id}")
        return document_id

    async def get_pdf_by_id(self, document_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a PDF document by its ID.

        Args:
            document_id: The unique identifier of the PDF document

        Returns:
            The document dictionary if found, None otherwise
        """
        document = await self.pdfs_collection.find_one({'_id': document_id})
        return document

    async def search_pdfs(
        self,
        name_query: Optional[str] = None,
        system_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        tags: Optional[list[str]] = None,
        page_size: int = 50,
        page_number: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search for PDF documents with optional filters.

        Args:
            name_query: Text to search in document names (case-insensitive regex)
            system_filter: Filter by system
            type_filter: Filter by document type
            tags: Filter by tags (documents must have all specified tags)
            page_size: Number of results per page
            page_number: Page number (0-indexed)

        Returns:
            Tuple of (list of matching documents, total count)
        """
        query = {}

        if name_query:
            query['name'] = {'$regex': name_query, '$options': 'i'}
        if system_filter:
            query['system'] = system_filter
        if type_filter:
            query['type'] = type_filter
        if tags:
            query['tags'] = {'$all': tags}

        # Get total count
        total_count = await self.pdfs_collection.count_documents(query)

        # Get paginated results
        cursor = self.pdfs_collection.find(query).sort('created_at', DESCENDING)
        cursor.skip(page_number * page_size).limit(page_size)
        documents = await cursor.to_list(length=page_size)

        return documents, total_count

    async def update_pdf_metadata(
        self,
        document_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """Update metadata fields of a PDF document.

        Args:
            document_id: The document to update
            updates: Dictionary of fields to update

        Returns:
            True if document was updated, False if not found
        """
        updates['updated_at'] = datetime.now()

        result = await self.pdfs_collection.update_one(
            {'_id': document_id},
            {'$set': updates}
        )

        return result.modified_count > 0

    # ========================================================================
    # Text Document Operations
    # ========================================================================

    async def store_document(
        self,
        document_id: str,
        name: str,
        content: str,
        doc_type: str,
        tags: list[str],
        created_at: datetime,
    ) -> str:
        """Store a text document in the database.

        Args:
            document_id: Unique identifier for the document
            name: Document name
            content: Full document content
            doc_type: Type of document
            tags: List of tags for the document
            created_at: Document creation timestamp

        Returns:
            The document_id of the stored document
        """
        document = {
            '_id': document_id,
            'name': name,
            'content': content,
            'type': doc_type,
            'character_count': len(content),
            'tags': tags,
            'created_at': created_at,
            'updated_at': created_at,
        }

        await self.documents_collection.insert_one(document)
        logger.info(f"Text document stored with ID: {document_id}")
        return document_id

    async def get_document_by_id(self, document_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a text document by its ID.

        Args:
            document_id: The unique identifier of the document

        Returns:
            The document dictionary if found, None otherwise
        """
        document = await self.documents_collection.find_one({'_id': document_id})
        return document

    async def update_document(
        self,
        document_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        doc_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Optional[dict[str, Any]]:
        """Update a text document.

        Args:
            document_id: The document to update
            name: New name (if provided)
            content: New content (if provided)
            doc_type: New type (if provided)
            tags: New tags (if provided)

        Returns:
            The updated document if found, None otherwise
        """
        updates = {'updated_at': datetime.now()}

        if name is not None:
            updates['name'] = name
        if content is not None:
            updates['content'] = content
            updates['character_count'] = len(content)
        if doc_type is not None:
            updates['type'] = doc_type
        if tags is not None:
            updates['tags'] = tags

        result = await self.documents_collection.find_one_and_update(
            {'_id': document_id},
            {'$set': updates},
            return_document=True  # Return the updated document
        )

        return result

    async def search_documents(
        self,
        name_query: Optional[str] = None,
        content_query: Optional[str] = None,
        type_filter: Optional[str] = None,
        tags: Optional[list[str]] = None,
        page_size: int = 50,
        page_number: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search for text documents with optional filters.

        Args:
            name_query: Text to search in document names (case-insensitive)
            content_query: Text to search in document content (case-insensitive)
            type_filter: Filter by document type
            tags: Filter by tags (documents must have all specified tags)
            page_size: Number of results per page
            page_number: Page number (0-indexed)

        Returns:
            Tuple of (list of matching documents, total count)
        """
        query = {}

        if name_query:
            query['name'] = {'$regex': name_query, '$options': 'i'}
        if content_query:
            query['content'] = {'$regex': content_query, '$options': 'i'}
        if type_filter:
            query['type'] = type_filter
        if tags:
            query['tags'] = {'$all': tags}

        # Get total count
        total_count = await self.documents_collection.count_documents(query)

        # Get paginated results (excluding full content for list views)
        cursor = self.documents_collection.find(
            query,
            {'content': 0}  # Exclude content field for performance
        ).sort('created_at', DESCENDING)
        cursor.skip(page_number * page_size).limit(page_size)
        documents = await cursor.to_list(length=page_size)

        return documents, total_count

    async def delete_document(self, document_id: str) -> bool:
        """Delete a text document by ID.

        Args:
            document_id: The document to delete

        Returns:
            True if document was deleted, False if not found
        """
        result = await self.documents_collection.delete_one({'_id': document_id})
        return result.deleted_count > 0

    # ========================================================================
    # Direct Collection Access (for special cases)
    # ========================================================================

    def get_pdfs_collection(self):
        """Get direct access to PDFs collection.

        Use this sparingly - only when you need operations not covered
        by the repository methods above.
        """
        return self.pdfs_collection

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
        await db.store_pdf_document(...)
    """
    global _database, _mongo_client

    if _database is None:
        settings = get_settings()
        _mongo_client = AsyncMongoClient(
            str(settings.database.doc_db_url)
        )
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
