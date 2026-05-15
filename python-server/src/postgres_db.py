"""Unified database repository for Bibliophage.

Single entry point for all PostgreSQL operations: document CRUD, vector
embeddings, and similarity search.  Replaces the former split between
postgres_document_db and postgres_vector_db.

Usage:
    db = get_postgres_db()
    await db.store_document(name, ...)
    results = await db.search_similar("query text")
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from pgvector.psycopg import register_vector_async
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Json, Jsonb

from config import get_settings
from postgres_repository import PostgresRepository

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


# ── repository ──────────────────────────────────────────────────────────


class BibliophageDatabase(PostgresRepository):
    """Unified repository for documents and vector chunks."""

    def __init__(
        self,
        connection_url: str,
        min_size: int = 4,
        max_size: int = 100,
    ):
        super().__init__(
            connection_url=connection_url,
            configure_callback=register_vector_async,
            min_size=min_size,
            max_size=max_size,
        )

    async def initialise_schema(self) -> None:
        """Create all tables (documents + vector chunks) if they don't exist."""
        await self.initialise_db_schema("documents.sql")
        await self.initialise_db_schema("vectors.sql")

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
        content_snippet = content[:200] + "..." if character_count > 200 else content

        insert_sql = """
            INSERT INTO documents
                (title, source_type, metadata, content, content_snippet,
                 document_type, character_count)
            VALUES
                (%(name)s, %(source_type)s, %(metadata)s, %(content)s,
                 %(content_snippet)s, %(doc_type)s, %(character_count)s)
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

        # TODO: insert systems into map_documents_to_systems
        # TODO: insert tags into map_documents_to_tags

        async def _insert(conn) -> dict[str, Any]:
            cursor = await conn.execute(insert_sql, params)
            row = await cursor.fetchone()
            return {
                "document_id": str(row[0]),
                "created_at": row[1],
                "character_count": int(row[2]),
            }

        result = await self.execute_transaction(_insert)
        logger.info(f"Document inserted: {result['document_id']}")
        return result

    async def get_document_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Retrieve a document by ID. Returns dict with column names as keys."""
        fetch_sql = """
            SELECT * FROM documents WHERE document_id = %(document_id)s
        """
        async with self._pool.connection() as conn:
            cursor = await conn.execute(fetch_sql, {"document_id": document_id})
            cursor.row_factory = dict_row
            return await cursor.fetchone()

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document (cascades to document_chunks). Returns True if deleted."""
        delete_sql = "DELETE FROM documents WHERE document_id = %(document_id)s"
        async with self._pool.connection() as conn:
            cursor = await conn.execute(delete_sql, {"document_id": document_id})
            return cursor.rowcount == 1

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

        async with self._pool.connection() as conn:
            cursor = await conn.execute(query_data, params_data)
            cursor.row_factory = dict_row
            documents = await cursor.fetchall()

        async with self._pool.connection() as conn:
            cursor = await conn.execute(query_count, params)
            total = (await cursor.fetchone())[0]

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

        now = datetime.now(UTC)

        insert_sql = sql.SQL("""
            INSERT INTO document_chunks
                (document_id, chunk_id, content, embedding,
                 start_position, end_position, metadata, created_at)
            VALUES
                (%(document_id)s, %(chunk_id)s, %(content)s, %(embedding)s,
                 %(start_position)s, %(end_position)s, %(metadata)s, %(created_at)s)
            ON CONFLICT (chunk_id) DO NOTHING
        """)

        rows = []
        for i, chunk in enumerate(chunks):
            meta = chunk.get("metadata", {})
            rows.append({
                "document_id": document_id,
                "chunk_id": chunk["chunk_id"],
                "content": chunk["content"],
                "embedding": embeddings[i],
                "start_position": meta.get("char_start", 0),
                "end_position": meta.get("char_end", len(chunk["content"])),
                "metadata": Jsonb(meta),
                "created_at": now,
            })

        async def _insert(cursor):
            await cursor.executemany(insert_sql, rows)
            return cursor.rowcount

        count = await self.execute("", callback=_insert)
        logger.info(f"Inserted {count} chunks for document {document_id}")
        return count

    async def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        async def _count(cursor):
            return cursor.rowcount

        count = await self.execute(
            "DELETE FROM document_chunks WHERE document_id = %s",
            params=(document_id,),
            callback=_count,
        )
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
            search_sql = """
                SELECT chunk_id, document_id, content, metadata,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            params = (query_embedding, query_embedding, top_k)
        else:
            search_sql = """
                SELECT chunk_id, document_id, content, metadata,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            params = (query_embedding, document_id, query_embedding, top_k)

        async def _fetch(cursor):
            rows = await cursor.fetchall()
            return [
                {
                    "chunk_id": r[0],
                    "document_id": r[1],
                    "content": r[2],
                    "metadata": r[3],
                    "similarity": float(r[4]),
                }
                for r in rows
            ]

        results = await self.execute(search_sql, params=params, callback=_fetch)
        logger.info(f"Found {len(results)} similar chunks")
        return results

    async def get_chunk_count(self, document_id: str) -> int:
        """Get number of chunks for a document."""
        async def _count(cursor):
            row = await cursor.fetchone()
            return row[0] if row else 0

        return await self.execute(
            "SELECT COUNT(*) FROM document_chunks WHERE document_id = %s",
            params=(document_id,),
            callback=_count,
        )
