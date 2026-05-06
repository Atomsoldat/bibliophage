"""Database repository module for PostgreSQL operations related to the document database.

This module is meant to replace the ferretdb-specific module and might be merged with the
vector db module in the future. 
This module provides a centralized interface for all document database operations


Usage:
    db = get_document_db()
    await db.store_document(document_id, name, ...)
    document = await db.get_document_by_id(document_id)
"""

from __future__ import annotations
import importlib.resources
import logging
from typing import Any

from psycopg.types.json import Json

from postgres_repository import PostgresRepository
from config import get_settings

logger = logging.getLogger(__name__)

# We only want a single instance of both of these vars being used, so every instance of our
# class uses the same variables stored at the module level of our class
# the underscore prefix is the conventional way of saying "don't touch these variables"
# from outside the module
_document_db: DocumentDatabase | None = None



def get_document_db() -> DocumentDatabase:
    """Get the document database singleton instance.

    This is the function code should use to get a DocumentDatabase object to execute statements with.
    
    Returns: DocumentDatabase: Configured document database repository

    Example:
        db = get_document_db()
        await db.store_document(...)

    """
    # global keyword used to modify module level variables instead of creating a local variable
    # see above for explanation
    global _document_db

    if _document_db is None:
        settings = get_settings()
        _document_db = DocumentDatabase(
            # TODO: we should genericize this to something like postgres DB url
            connection_url=str(settings.database.vector_db_url),
        )
        logger.info("Document database instance created")

    return _document_db


async def close_database():
    """Close all database connections and clean up resources.

    This should be called when the application shuts down.
    """
    global _document_db

    if _document_db is not None:
        await _document_db.close_pool()
        _document_db = None
        logger.info("Document Database connection pool closed")


class DocumentDatabase(PostgresRepository):
    """Repository providing all document database operations."""


    def __init__(
        self,
        connection_url: str,
        min_size: int = 4,
        max_size: int = 100,
    ):
        """Initialise the document database repository.

        Args:
            connection_url: PostgreSQL connection string
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool

        """
        super().__init__(
            connection_url=connection_url,
            min_size=min_size,
            max_size=max_size,
        )
        logger.info("DocumentDatabase repository initialised")


    async def initialise_db_schema(self) -> None:
        """Create tables defined in db_schema/*.sql if they do not yet exist.

        The SQL is shipped as package data alongside the Python code so it
        travels with the application no matter how it is installed or invoked.
        """

        ddl_schema_dir = importlib.resources.files("db_schema")
        documents_ddl_file = ddl_schema_dir.joinpath("documentdb_table_documents.sql")
        documents_ddl = documents_ddl_file.read_text(encoding="utf-8")

        await self.execute_script(documents_ddl)
        logger.info("DocumentDatabase schema initialisation executed")

    # ========================================================================
    # Document Operations
    # ========================================================================


    async def store_document(
        self,
        name: str,
        systems: list[str],
        source_type: str,
        content: str,
        doc_type: str,
        tags: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a document in the database.

        Args:
            name: Document name
            systems: List of RPG systems this document belongs to (must have at least one)
            source_type: Source type for authority weighting (e.g., CORE, SUPPLEMENT, GM_NOTES)
            content: Full document content (markdown for PDFs, plain text for notes)
            doc_type: Type of document (e.g., RULEBOOK, NOTE, ADVENTURE)
            tags: List of structured tags [{"name": str, "values": [str, ...]}]
            metadata: Optional metadata dict for file-based content with keys:
                - file_size: int (bytes)
                - publication_type: str (optional)
                - pdf: dict (optional) with loading_batch_count, vector_chunk_count, page_count

        Returns:
            The document_id of the stored document

        """
        # Create snippet for search results (max 200 characters)
        character_count = len(content)
        content_snippet = content[:200] + "..." if character_count > 200 else content

        # TODO: name vs title, adjust API definitions
        # TODO: we currently don't fill created_at and updated_at and let the DB handle it                                 
        # TODO: we should come back in a while and see whether we like it that way - 20260505                              
        # TODO: is the way we handle metadata correct here? what if its empty/undefined? 
        insert_sql = """
            INSERT INTO documents
            (
                title,
                source_type,
                metadata,
                content,
                content_snippet,
                document_type,
                character_count
            )
            VALUES(
                %(name)s,
                %(source_type)s,
                %(metadata)s,
                %(content)s,
                %(content_snippet)s,
                %(doc_type)s,
                %(character_count)s
            )
            RETURNING document_id
            """

        params = {
            "name": name,
            "source_type": source_type,
            "metadata": Json(metadata or {}),
            "content": content,
            "content_snippet": content_snippet,
            "doc_type": doc_type,
            "character_count": character_count,
        }

        async def insert_all(conn) -> str:
            cursor = await conn.execute(insert_sql, params)
            row = await cursor.fetchone()
            document_id = str(row[0])

            # TODO: insert systems into map_documents_to_systems
            # TODO: insert tags into map_documents_to_tags

            return document_id

        document_id = await self.execute_transaction(insert_all)
        logger.info(f"Document inserted with id {document_id}")
        return document_id
