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
from psycopg import sql
from typing import Any

from psycopg.types.json import Json
from psycopg.rows import dict_row

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
            RETURNING document_id, created_at, character_count
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

            # TODO: insert systems into map_documents_to_systems
            # TODO: insert tags into map_documents_to_tags

            return {
                "document_id": str(row[0]),
                "created_at": (
                    row[1]
                ),  # psycopg already maps dates to the python datetime type
                "character_count": int(row[2]),
            }

        response = await self.execute_transaction(insert_all)
        logger.info(f"Document inserted with id {response['document_id']}")
        return response

    async def delete_document(
        self,
        document_id: str,
    ) -> bool:
        """Delete a document from the database.

        Args:
            document_id: Document ID

        Returns:
            True on Success, False on Failure

        """
        delete_sql = """
            DELETE FROM documents
            WHERE document_id = %(document_id)s
        """

        async with self._pool.connection() as conn:
            cursor = await conn.execute(delete_sql, {"document_id": document_id})
            logger.info(f"Deleted {cursor.rowcount} document(s)")
            return cursor.rowcount == 1

    async def get_document_by_id(
        self,
        document_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve a document by its ID.

        Args:
            document_id: The unique identifier of the document

        Returns:
            The document dict if found, None otherwise

        """
        # Using * here might become not so great if documents ends up having tons of columns
        # we will fix that once it becomes a problem : ^)
        fetch_sql = """
            SELECT *
            FROM documents
            WHERE document_id = %(document_id)s
        """
        async with self._pool.connection() as conn:
            cursor = await conn.execute(fetch_sql, {"document_id": document_id})
            cursor.row_factory = dict_row
            return await cursor.fetchone()

    async def search_documents(
        self,
        name_query: str | None = None,
        content_query: str | None = None,
        type_filters: list[str] | None = None,
        system_filters: list[str] | None = None,
        tag_filters: list[dict[str, str]] | None = None,
        page_size: int = 50,
        page_number: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search for documents with optional filters.

        Args:
            name_query: Text to search in document names (case-insensitive)
            content_query: Text to search in document content (case-insensitive)
            type_filters: Filter by document type
            system_filters: Filter by systems (returns documents where systems contains ANY of these)
            tag_filters: Filter by tags [{"name": str, "value": str}] (documents must match ALL)
            page_size: Number of results per page
            page_number: Page number (0-indexed)

        Returns:
            Tuple of (list of matching documents, total count)

        """
        conditions = []
        params = {}

        if name_query:
            conditions.append(sql.SQL("title ILIKE %(name_query)s"))
            params["name_query"] = "%" + name_query + "%"
        if content_query:
            # TODO: build this using pg_trgm (or something similar) and an extra column in our table
            # apparently, with the right configuration, this allows us to support
            # multiple languages more smoothly
            # see our comment above about using SELECT * on the documents table, that might
            # get messy, if we have all kinds of text search related data in there
            #
            # https://www.postgresql.org/docs/current/pgtrgm.html
            # https://dba.stackexchange.com/questions/271412/trigram-similarity-pg-trgm-with-german-umlauts
            # https://www.reddit.com/r/PostgreSQL/comments/1ca30w3/how_to_index_a_text_column_containing_nonenglish/
            # there is also this, but that requires packaging the extension ourselves
            # https://pgroonga.github.io/reference/pgroonga-versus-textsearch-and-pg-trgm.html
            raise NotImplementedError
        if type_filters:
            conditions.append(sql.SQL("document_type = ANY(%(type_filters)s)"))
            params["type_filters"] = type_filters
        if system_filters:
            conditions.append(sql.SQL("document_system = ANY(%(system_filters)s)"))
            params["system_filters"] = system_filters
        if tag_filters:
            conditions.append(sql.SQL("document_tag = ANY(%(tag_filters)s)"))
            params["tag_filters"] = tag_filters

        params_count = params
        # perform shallow copy, otherwise we get a pointer to the same variable
        params_data = params.copy()
        params_data["page_size"] = page_size
        params_data["offset"] = page_number * page_size

        query_data = sql.SQL("SELECT * FROM documents")
        query_count = sql.SQL("SELECT COUNT(*) FROM documents")

        if conditions:
            query_data = (
                query_data + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
            )
            query_count = (
                query_count + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
            )

        # TODO: we could make this configurable by the client
        query_data = query_data + sql.SQL(" ORDER BY updated_at DESC")
        query_data = query_data + sql.SQL(" LIMIT %(page_size)s")
        query_data = query_data + sql.SQL(" OFFSET %(offset)s")

        documents = []
        async with self._pool.connection() as conn:
            cursor = await conn.execute(query_data, params_data)
            cursor.row_factory = dict_row
            documents = await cursor.fetchall()
            # TODO: some arithmetics to figure out how many pages there are in total
            # so that we can tell this to the frontend

        # I think that running a whole extra query just to figure out how many documents
        # matching our query exist might be overblown
        # maybe we can just do some math to say
        # whether there are more... we have to fulfill the API contract for now
        total_matches = 0
        async with self._pool.connection() as conn:
            cursor = await conn.execute(query_count, params_count)
            count_result = await cursor.fetchone()
            total_matches = count_result[0]

        # we might want to use a named, server side cursor if we end up handling vast
        # amounts of data, let's see how that ends up working out
        # for now, this gets all the data from the database and immediately wires it to
        # the client (that being the python server)

        # FIXME: We are currently returning the document content, which is wasteful

        return documents, total_matches
