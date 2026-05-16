"""PostgreSQL database module for Bibliophage.

Single module for all PostgreSQL operations: connection pool management,
document CRUD, vector embeddings, and similarity search.

Usage:
    db = get_postgres_db()
    await db.store_document(name, ...)
    results = await db.search_similar("query text")

References:
    - https://www.psycopg.org/psycopg3/docs/advanced/pool.html
    - https://www.psycopg.org/psycopg3/docs/api/pool.html#the-connectionpool-clas
    - https://www.psycopg.org/psycopg3/docs/advanced/async.html
"""

from __future__ import annotations

import importlib.resources
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from pgvector.psycopg import register_vector_async
from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row
from psycopg.types.json import Json, Jsonb
from psycopg_pool import AsyncConnectionPool

from config import get_settings

logger = logging.getLogger(__name__)

# ── singletons ──────────────────────────────────────────────────────────

_db: BibliophageDatabase | None = None
_embeddings_model: HuggingFaceEmbeddings | None = None


def get_postgres_db() -> BibliophageDatabase:
    """Get the application database singleton."""
    global _db
    if _db is None:
        settings = get_settings()
        _db = BibliophageDatabase(
            connection_url=str(settings.database.vector_db_url),
        )
        logger.info("BibliophageDatabase instance created")
    return _db


def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Get the embeddings model singleton."""
    global _embeddings_model
    if _embeddings_model is None:
        settings = get_settings()
        model_name = settings.embedding.embedding_model_name
        logger.info(f"Loading embeddings model: {model_name}")
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"Embeddings model loaded: {model_name}")
    return _embeddings_model


async def close_database():
    """Close all database connections. Call on app shutdown."""
    global _db
    if _db is not None:
        await _db.close_pool()
        _db = None
        logger.info("BibliophageDatabase connection pool closed")


# ── database ────────────────────────────────────────────────────────────


class BibliophageDatabase:
    """PostgreSQL repository for documents and vector chunks.

    Manages a connection pool and provides simple methods for executing queries.
    Domain methods (store_document, search_similar, ...) are built on top of
    three primitives: fetchone, fetchall, execute.
    """

    def __init__(
        self,
        connection_url: str,
        min_size: int = 4,
        max_size: int = 100,
    ):
        self._connection_url = connection_url
        self._min_size = min_size
        self._max_size = max_size
        self._pool: AsyncConnectionPool | None = None

    # ── pool lifecycle ──────────────────────────────────────────────────

    async def ensure_initialised(self) -> None:
        """Open the connection pool. Call once during server startup."""
        if self._pool is not None:
            return
        try:
            self._pool = AsyncConnectionPool(
                open=False,
                conninfo=self._connection_url,
                min_size=self._min_size,
                max_size=self._max_size,
                close_returns=True,
                configure=register_vector_async,
                kwargs={"autocommit": True},
            )
            await self._pool.open()
            await self._pool.wait()
            logger.info("PostgreSQL connection pool initialised")
        except Exception as e:
            logger.error(f"Failed to initialise PostgreSQL pool: {e}")
            self._pool = None
            raise

    async def close_pool(self) -> None:
        """Close the connection pool. Call on shutdown."""
        if self._pool is not None:
            await self._pool.close(timeout=10.0)
            self._pool = None

    async def initialise_schema(self) -> None:
        """Create all tables if they don't exist."""
        for ddl_file in ("documents.sql", "vectors.sql"):
            ddl_path = importlib.resources.files("db_schema").joinpath(ddl_file)
            ddl = ddl_path.read_text(encoding="utf-8")
            await self.execute_script(ddl)
            logger.info("Schema initialisation executed (%s)", ddl_file)

    # ── SQL primitives ──────────────────────────────────────────────────

    async def fetchone(
        self, query: str | sql.Composable, params: Any = None,
    ) -> dict[str, Any] | None:
        """Execute a query and return a single row as a dict, or None."""
        async with self._pool.connection() as conn:
            cursor = await conn.execute(query, params)
            cursor.row_factory = dict_row
            return await cursor.fetchone()

    async def fetchall(
        self, query: str | sql.Composable, params: Any = None,
    ) -> list[dict[str, Any]]:
        """Execute a query and return all rows as a list of dicts."""
        async with self._pool.connection() as conn:
            cursor = await conn.execute(query, params)
            cursor.row_factory = dict_row
            return await cursor.fetchall()

    async def execute(
        self, query: str | sql.Composable, params: Any = None,
    ) -> int:
        """Execute a statement and return the number of affected rows."""
        async with self._pool.connection() as conn:
            cursor = await conn.execute(query, params)
            return cursor.rowcount

    async def execute_script(self, sql_script: str) -> None:
        """Execute a multi-statement DDL script (no params, no results)."""
        async with self._pool.connection() as conn:
            await conn.execute(sql_script)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        """Context manager yielding a connection inside a transaction.

        Usage:
            async with db.transaction() as conn:
                await conn.execute(insert_sql, params)
                await conn.execute(tags_sql, params)
        """
        async with self._pool.connection() as conn:
            async with conn.transaction():
                yield conn

    # ── document CRUD ───────────────────────────────────────────────────

    async def store_document(
        self,
        name: str,
        systems: list[str],
        source_type: str,
        content: str,
        doc_type: str,
        tags: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert a document. Returns dict with document_id, created_at, character_count."""
        character_count = len(content)

        insert_sql = sql.SQL("""
            INSERT INTO documents
                (title, source_type, metadata, content,
                 document_type, character_count)
            VALUES
                (%(name)s, %(source_type)s, %(metadata)s, %(content)s,
                 %(doc_type)s, %(character_count)s)
            RETURNING document_id, created_at, character_count
        """)
        params = {
            "name": name,
            "source_type": source_type,
            "metadata": Json(metadata or {}),
            "content": content,
            "doc_type": doc_type,
            "character_count": character_count,
        }

        # TODO: insert systems into map_documents_to_systems
        # TODO: insert tags into map_documents_to_tags

        row = await self.fetchone(insert_sql, params)
        result = {
            "document_id": str(row["document_id"]),
            "created_at": row["created_at"],
            "character_count": int(row["character_count"]),
        }
        logger.info(f"Document inserted: {result['document_id']}")
        return result

    async def get_document_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Retrieve a document by ID."""
        fetch_sql = sql.SQL("SELECT * FROM documents WHERE document_id = %(document_id)s")
        return await self.fetchone(fetch_sql, {"document_id": document_id})

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document (cascades to document_chunks). Returns True if deleted."""
        delete_sql = sql.SQL("DELETE FROM documents WHERE document_id = %(document_id)s")
        count = await self.execute(delete_sql, {"document_id": document_id})
        return count == 1

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
        """Search documents with optional filters. Returns (rows, total_count)."""
        conditions: list[sql.Composable] = []
        params: dict[str, Any] = {}

        if name_query:
            conditions.append(sql.SQL("title ILIKE %(name_query)s"))
            params["name_query"] = f"%{name_query}%"
        if content_query:
            raise NotImplementedError("Full-text content search not yet implemented")
        if type_filters:
            conditions.append(sql.SQL("document_type = ANY(%(type_filters)s)"))
            params["type_filters"] = type_filters
        if system_filters:
            conditions.append(sql.SQL("document_system = ANY(%(system_filters)s)"))
            params["system_filters"] = system_filters
        if tag_filters:
            conditions.append(sql.SQL("document_tag = ANY(%(tag_filters)s)"))
            params["tag_filters"] = tag_filters

        where = (
            sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
            if conditions
            else sql.SQL("")
        )

        query_data = (
            sql.SQL("SELECT * FROM documents")
            + where
            + sql.SQL(" ORDER BY updated_at DESC LIMIT %(page_size)s OFFSET %(offset)s")
        )
        query_count = sql.SQL("SELECT COUNT(*) FROM documents") + where

        params_data = {**params, "page_size": page_size, "offset": page_number * page_size}

        documents = await self.fetchall(query_data, params_data)

        count_row = await self.fetchone(query_count, params)
        total = count_row["count"] if count_row else 0

        return documents, total

    # ── vector / chunk operations ───────────────────────────────────────

    async def embed_chunks(
        self,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> int:
        """Generate embeddings for chunks and store them. Returns count inserted.

        Each chunk dict must have: chunk_id, content, metadata (with char_start, char_end).
        Deletes existing chunks for the document first.
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")

        await self.delete_document_chunks(document_id)

        model = get_embeddings_model()
        contents = [c["content"] for c in chunks]
        logger.info(f"Generating embeddings for {len(contents)} chunks")
        embeddings = model.embed_documents(contents)

        insert_sql = sql.SQL("""
            INSERT INTO document_chunks
                (document_id, content, embedding,
                 start_position, end_position, metadata)
            VALUES
                (%(document_id)s, %(content)s, %(embedding)s,
                 %(start_position)s, %(end_position)s, %(metadata)s)
        """)

        rows = []
        for i, chunk in enumerate(chunks):
            meta = chunk.get("metadata", {})
            rows.append({
                "document_id": document_id,
                "content": chunk["content"],
                "embedding": embeddings[i],
                "start_position": meta.get("char_start", 0),
                "end_position": meta.get("char_end", len(chunk["content"])),
                "metadata": Jsonb(meta),
            })

        # executemany needs a connection directly — use the pool context
        async with self._pool.connection() as conn:
            cursor = await conn.executemany(insert_sql, rows, returning=True)
            # psycopg3 executemany with returning=True returns a count
            # but rowcount after executemany reflects last statement only,
            # so we use len(rows) as the authoritative count
        count = len(rows)
        logger.info(f"Inserted {count} chunks for document {document_id}")
        return count

    async def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        delete_sql = sql.SQL(
            "DELETE FROM document_chunks WHERE document_id = %(document_id)s"
        )
        params = {"document_id": document_id}
        count = await self.execute(delete_sql, params)
        logger.info(f"Deleted {count} chunks for document {document_id}")
        return count

    async def search_similar(
        self,
        query: str,
        top_k: int = 10,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Vector similarity search. Returns list of dicts with chunk_id, document_id, content, metadata, similarity."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        model = get_embeddings_model()
        query_embedding = model.embed_query(query)

        if document_id is None:
            search_sql = sql.SQL("""
                SELECT chunk_id, document_id, content, metadata,
                       1 - (embedding <=> %(embedding)s::vector) AS similarity
                FROM document_chunks
                ORDER BY embedding <=> %(embedding)s::vector
                LIMIT %(top_k)s
            """)
            params = {"embedding": query_embedding, "top_k": top_k}
        else:
            search_sql = sql.SQL("""
                SELECT chunk_id, document_id, content, metadata,
                       1 - (embedding <=> %(embedding)s::vector) AS similarity
                FROM document_chunks
                WHERE document_id = %(document_id)s
                ORDER BY embedding <=> %(embedding)s::vector
                LIMIT %(top_k)s
            """)
            params = {
                "embedding": query_embedding,
                "document_id": document_id,
                "top_k": top_k,
            }

        return await self.fetchall(search_sql, params)

    async def get_chunk_count(self, document_id: str) -> int:
        """Get number of chunks for a document."""
        count_sql = sql.SQL(
            "SELECT COUNT(*) AS count FROM document_chunks WHERE document_id = %(document_id)s"
        )
        params = {"document_id": document_id}
        row = await self.fetchone(count_sql, params)
        return row["count"] if row else 0
