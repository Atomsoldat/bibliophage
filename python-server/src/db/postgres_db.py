"""PostgreSQL database module for Bibliophage.

Single module for all PostgreSQL operations: connection pool management,
document CRUD, vector embeddings, and similarity search.

Usage:
    db = get_postgres_db()
    await db.store_document(name, ...)
    results = await db.search_similar(query_embedding)

References:
    - https://www.psycopg.org/psycopg3/docs/advanced/pool.html
    - https://www.psycopg.org/psycopg3/docs/api/pool.html#the-connectionpool-clas
    - https://www.psycopg.org/psycopg3/docs/advanced/async.html
"""

from __future__ import annotations

import importlib.resources
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from pgvector.psycopg import register_vector_async
from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row
from psycopg.types.json import Json, Jsonb
from psycopg_pool import AsyncConnectionPool

from config import get_settings

logger = logging.getLogger(__name__)

#### singletons ##########################

_db: BibliophageDatabase | None = None


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


async def close_database():
    """Close all database connections. Call on app shutdown."""
    global _db
    if _db is not None:
        await _db.close_pool()
        _db = None
        logger.info("BibliophageDatabase connection pool closed")


#### database ##########################


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

    #### pool lifecycle ##########################

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
        # graph_edges references documents(document_id), so documents.sql must come first.
        for ddl_file in ("documents.sql", "vectors.sql", "graph.sql"):
            ddl_path = importlib.resources.files("db.schema").joinpath(ddl_file)
            ddl = ddl_path.read_text(encoding="utf-8")
            await self.execute_script(ddl)
            logger.info("Schema initialisation executed (%s)", ddl_file)

    #### SQL primitives ##########################

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
        async with self._pool.connection() as conn, conn.transaction():
            yield conn

    #### document CRUD ##########################

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
        """Insert a document and wire junction tables within a transaction.

        Returns dict with document_id, created_at, character_count.
        Raises ValueError if any system or tag name is unknown.
        """
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
        doc_params = {
            "name": name,
            "source_type": source_type,
            "metadata": Json(metadata or {}),
            "content": content,
            "doc_type": doc_type,
            "character_count": character_count,
        }

        async with self.transaction() as conn:
            # Insert the document and retrieve generated fields
            cursor = await conn.execute(insert_sql, doc_params)
            cursor.row_factory = dict_row
            row = await cursor.fetchone()
            document_id = str(row["document_id"])

            # Resolve system names — fail fast if any are unknown (D-05)
            if systems:
                sys_cursor = await conn.execute(
                    "SELECT system_id, title FROM systems WHERE title = ANY(%(names)s)",
                    {"names": systems},
                )
                sys_cursor.row_factory = dict_row
                found_systems = await sys_cursor.fetchall()
                found_titles = {r["title"] for r in found_systems}
                unknown = [s for s in systems if s not in found_titles]
                if unknown:
                    errmsg = f"Unknown system(s): {', '.join(unknown)}"
                    raise ValueError(errmsg)
                for sys_row in found_systems:
                    await conn.execute(
                        "INSERT INTO map_documents_to_systems (document_id, system_id) "
                        "VALUES (%(document_id)s, %(system_id)s)",
                        {"document_id": document_id, "system_id": sys_row["system_id"]},
                    )

            # Resolve tag names — fail fast if any are unknown (D-06)
            if tags:
                tag_names = [t["name"] for t in tags]
                tag_cursor = await conn.execute(
                    "SELECT tag_id, title FROM tags WHERE title = ANY(%(names)s)",
                    {"names": tag_names},
                )
                tag_cursor.row_factory = dict_row
                found_tags = await tag_cursor.fetchall()
                found_tag_map = {r["title"]: r["tag_id"] for r in found_tags}
                unknown = [n for n in tag_names if n not in found_tag_map]
                if unknown:
                    errmsg = f"Unknown tag(s): {', '.join(unknown)}"
                    raise ValueError(errmsg)
                for tag in tags:
                    tag_id = found_tag_map[tag["name"]]
                    # Store tag values as JSON string in tags.info (D-07)
                    await conn.execute(
                        "UPDATE tags SET info = %(info)s WHERE tag_id = %(tag_id)s",
                        {"info": json.dumps(tag.get("values", [])), "tag_id": tag_id},
                    )
                    await conn.execute(
                        "INSERT INTO map_documents_to_tags (document_id, tag_id) "
                        "VALUES (%(document_id)s, %(tag_id)s)",
                        {"document_id": document_id, "tag_id": tag_id},
                    )

        result = {
            "document_id": document_id,
            "created_at": row["created_at"],
            "character_count": int(row["character_count"]),
        }
        logger.info(f"Document inserted: {result['document_id']}")
        return result

    async def _enrich_documents_with_junction_data(
        self,
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Add systems and tags from junction tables to each document row.

        Batches the junction table queries across all document IDs to avoid N+1.
        Mutates each row dict in-place and returns the list.
        """
        if not documents:
            return documents

        doc_ids = [str(d["document_id"]) for d in documents]

        systems_rows = await self.fetchall(
            "SELECT m.document_id, s.title "
            "FROM map_documents_to_systems m "
            "JOIN systems s ON m.system_id = s.system_id "
            "WHERE m.document_id = ANY(%(ids)s)",
            {"ids": doc_ids},
        )
        tags_rows = await self.fetchall(
            "SELECT m.document_id, t.title, t.info "
            "FROM map_documents_to_tags m "
            "JOIN tags t ON m.tag_id = t.tag_id "
            "WHERE m.document_id = ANY(%(ids)s)",
            {"ids": doc_ids},
        )

        # Index by document_id for O(1) lookup
        systems_by_doc: dict[str, list[str]] = {}
        for r in systems_rows:
            key = str(r["document_id"])
            systems_by_doc.setdefault(key, []).append(r["title"])

        tags_by_doc: dict[str, list[dict[str, Any]]] = {}
        for r in tags_rows:
            key = str(r["document_id"])
            tags_by_doc.setdefault(key, []).append({
                "name": r["title"],
                "values": json.loads(r["info"]) if r["info"] else [],
            })

        for doc in documents:
            key = str(doc["document_id"])
            doc["systems"] = systems_by_doc.get(key, [])
            doc["tags"] = tags_by_doc.get(key, [])

        return documents

    async def get_document_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Retrieve a document by ID, enriched with systems and tags."""
        fetch_sql = sql.SQL("SELECT * FROM documents WHERE document_id = %(document_id)s")
        row = await self.fetchone(fetch_sql, {"document_id": document_id})
        if row is None:
            return None
        rows = await self._enrich_documents_with_junction_data([row])
        return rows[0]

    async def update_document(
        self,
        document_id: str,
        name: str,
        systems: list[str],
        source_type: str,
        content: str,
        doc_type: str,
        tags: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Update a document by ID using full replace semantics (D-01).

        All fields are overwritten. If content changed, sets embeddings_current=false (D-02).
        Junction tables are delete-reinserted within the transaction (D-08).
        Returns {"document_id": document_id} on success, or None if not found (D-04).
        Raises ValueError for unknown system or tag names (D-05, D-06).
        """
        character_count = len(content)

        async with self.transaction() as conn:
            # Check existence and lock the row; detect content change (D-04)
            cursor = await conn.execute(
                "SELECT content FROM documents WHERE document_id = %(document_id)s FOR UPDATE",
                {"document_id": document_id},
            )
            cursor.row_factory = dict_row
            existing = await cursor.fetchone()
            if existing is None:
                return None

            # Determine if content changed — stale embeddings when it does (D-02)
            embeddings_current = existing["content"] == content

            # Full replace of all document fields (D-01)
            update_sql = sql.SQL("""
                UPDATE documents
                SET title = %(name)s,
                    source_type = %(source_type)s,
                    metadata = %(metadata)s,
                    content = %(content)s,
                    document_type = %(doc_type)s,
                    character_count = %(character_count)s,
                    updated_at = now(),
                    embeddings_current = %(embeddings_current)s
                WHERE document_id = %(document_id)s
            """)
            await conn.execute(update_sql, {
                "name": name,
                "source_type": source_type,
                "metadata": Jsonb(metadata or {}),
                "content": content,
                "doc_type": doc_type,
                "character_count": character_count,
                "embeddings_current": embeddings_current,
                "document_id": document_id,
            })

            # Resolve system names — fail fast if any are unknown (D-05)
            if systems:
                sys_cursor = await conn.execute(
                    "SELECT system_id, title FROM systems WHERE title = ANY(%(names)s)",
                    {"names": systems},
                )
                sys_cursor.row_factory = dict_row
                found_systems = await sys_cursor.fetchall()
                found_titles = {r["title"] for r in found_systems}
                unknown = [s for s in systems if s not in found_titles]
                if unknown:
                    errmsg = f"Unknown system(s): {', '.join(unknown)}"
                    raise ValueError(errmsg)

                # Delete-reinsert junction rows for systems (D-08)
                await conn.execute(
                    "DELETE FROM map_documents_to_systems WHERE document_id = %(document_id)s",
                    {"document_id": document_id},
                )
                for sys_row in found_systems:
                    await conn.execute(
                        "INSERT INTO map_documents_to_systems (document_id, system_id) "
                        "VALUES (%(document_id)s, %(system_id)s)",
                        {"document_id": document_id, "system_id": sys_row["system_id"]},
                    )
            else:
                # No systems provided — clear any existing mappings
                await conn.execute(
                    "DELETE FROM map_documents_to_systems WHERE document_id = %(document_id)s",
                    {"document_id": document_id},
                )

            # Resolve tag names — fail fast if any are unknown (D-06)
            if tags:
                tag_names = [t["name"] for t in tags]
                tag_cursor = await conn.execute(
                    "SELECT tag_id, title FROM tags WHERE title = ANY(%(names)s)",
                    {"names": tag_names},
                )
                tag_cursor.row_factory = dict_row
                found_tags = await tag_cursor.fetchall()
                found_tag_map = {r["title"]: r["tag_id"] for r in found_tags}
                unknown = [n for n in tag_names if n not in found_tag_map]
                if unknown:
                    errmsg = f"Unknown tag(s): {', '.join(unknown)}"
                    raise ValueError(errmsg)

                # Delete-reinsert junction rows for tags (D-08)
                await conn.execute(
                    "DELETE FROM map_documents_to_tags WHERE document_id = %(document_id)s",
                    {"document_id": document_id},
                )
                for tag in tags:
                    tag_id = found_tag_map[tag["name"]]
                    # Store tag values as JSON string in tags.info (D-07)
                    await conn.execute(
                        "UPDATE tags SET info = %(info)s WHERE tag_id = %(tag_id)s",
                        {"info": json.dumps(tag.get("values", [])), "tag_id": tag_id},
                    )
                    await conn.execute(
                        "INSERT INTO map_documents_to_tags (document_id, tag_id) "
                        "VALUES (%(document_id)s, %(tag_id)s)",
                        {"document_id": document_id, "tag_id": tag_id},
                    )
            else:
                # No tags provided — clear any existing mappings
                await conn.execute(
                    "DELETE FROM map_documents_to_tags WHERE document_id = %(document_id)s",
                    {"document_id": document_id},
                )

        logger.info("Document updated: %s (embeddings_current=%s)", document_id, embeddings_current)
        return {"document_id": document_id}

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
        """Search documents with optional filters. Returns (rows, total_count).

        system_filters matches documents associated with ANY of the given system names.
        tag_filters matches documents associated with ALL of the given tag names.
        Each result row is enriched with systems and tags from junction tables.
        """
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
            # EXISTS subquery replaces the broken "document_system = ANY(...)" ref
            conditions.append(sql.SQL(
                "EXISTS ("
                "  SELECT 1 FROM map_documents_to_systems m"
                "  JOIN systems s ON m.system_id = s.system_id"
                "  WHERE m.document_id = documents.document_id"
                "  AND s.title = ANY(%(system_filters)s)"
                ")"
            ))
            params["system_filters"] = system_filters
        if tag_filters:
            # One EXISTS condition per tag filter — document must match ALL
            for idx, tag_f in enumerate(tag_filters):
                name_key = "tag_name_" + str(idx)
                conditions.append(
                    sql.SQL(
                        "EXISTS ("
                        "  SELECT 1 FROM map_documents_to_tags m"
                        "  JOIN tags t ON m.tag_id = t.tag_id"
                        "  WHERE m.document_id = documents.document_id"
                        "  AND t.title = "
                    )
                    + sql.Placeholder(name_key)
                    + sql.SQL(")")
                )
                params[name_key] = tag_f["name"]

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
        documents = await self._enrich_documents_with_junction_data(documents)

        count_row = await self.fetchone(query_count, params)
        total = count_row["count"] if count_row else 0

        return documents, total


    #### canon CRUD ##########################
    # TODO (:

    #### vector / chunk operations ##########################

    async def store_chunks(
        self,
        document_id: str,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> int:
        """Persist chunks with their pre-computed embedding vectors. Returns count inserted.

        Each chunk dict must have: content, metadata (with char_start, char_end).
        The `embeddings` list must be the same length as `chunks`, ordered to match.
        Computing the vectors is the responsibility of embeddings.embed_texts.
        """
        if not chunks:
            errmsg="Chunks list cannot be empty"
            raise ValueError(errmsg)
        if len(chunks) != len(embeddings):
            errmsg = (
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) "
                "length mismatch"
            )
            raise ValueError(errmsg)

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

        # executemany needs a cursor to be instantiated
        # the conn.execute() we normally use for one-offs is syntactic sugar on the connection class  that
        # does the cursor creation for us behind the scenes and returns a cursor
        # https://www.psycopg.org/psycopg3/docs/api/pool.html#psycopg_pool.AsyncConnectionPool
        # https://www.psycopg.org/psycopg3/docs/api/pool.html#psycopg_pool.AsyncConnectionPool.connection
        # https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.AsyncConnection.execute
        # https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.AsyncConnection.cursor
        # https://www.psycopg.org/psycopg3/docs/api/cursors.html#psycopg.AsyncCursor.executemany
        async with self._pool.connection() as conn:
            cursor = conn.cursor()
            await cursor.executemany(insert_sql, rows, returning=True)
            # psycopg3 executemany with returning=True returns a count
            # but rowcount after executemany reflects last statement only,
            # so we use len(rows) as the authoritative count

        logger.info(f"Inserted {len(rows)} chunks for document {document_id}")
        return len(rows)

    async def get_boundaries_for_document(
        self,
        document_id: str,
    ) -> list[dict[str, Any]]:
        """Return chunk_id, start_position, end_position for all chunks of a document."""
        return await self.fetchall(
            "SELECT chunk_id, start_position, end_position "
            "FROM document_chunks WHERE document_id = %(document_id)s",
            {"document_id": document_id},
        )

    async def delete_chunks_by_ids(self, chunk_ids: list[str]) -> int:
        """Delete specific chunks by their IDs. Returns count deleted."""
        if not chunk_ids:
            return 0
        delete_sql = sql.SQL(
            "DELETE FROM document_chunks WHERE chunk_id = ANY(%(chunk_ids)s)"
        )
        count = await self.execute(delete_sql, {"chunk_ids": chunk_ids})
        logger.info(f"Deleted {count} chunks by ID")
        return count

    async def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        delete_sql = sql.SQL(
            "DELETE FROM document_chunks WHERE document_id = %(document_id)s"
        )
        count = await self.execute(delete_sql, {"document_id": document_id})
        logger.info(f"Deleted {count} chunks for document {document_id}")
        return count

    async def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Vector similarity search. Returns list of dicts with chunk_id, document_id, content, metadata, similarity.

        The caller is responsible for producing `query_embedding` (see
        embeddings.embed_query).
        """
        if top_k <= 0:
            errmsg = "top_k must be positive"
            raise ValueError(errmsg)

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

    #### graph operations ##########################

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str = "RELATED",
        directed: bool = False,
    ) -> dict[str, Any]:
        """Insert an edge between two documents.

        For undirected edges (directed=False) the endpoints are stored in
        canonical order (source_id < target_id). The database enforces this
        via a CHECK constraint; we swap here so the call site does not have
        to think about it.

        Returns the inserted row as a dict with edge_id, source_id, target_id,
        relationship, directed, created_at.
        """
        if not directed and source_id > target_id:
            source_id, target_id = target_id, source_id

        insert_sql = sql.SQL("""
            INSERT INTO graph_edges
                (source_id, target_id, relationship, directed)
            VALUES
                (%(source_id)s, %(target_id)s, %(relationship)s, %(directed)s)
            RETURNING edge_id, source_id, target_id, relationship, directed, created_at
        """)
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "relationship": relationship,
            "directed": directed,
        }
        row = await self.fetchone(insert_sql, params)
        logger.info(
            "Edge inserted: %s (%s → %s, %s)",
            row["edge_id"], row["source_id"], row["target_id"], row["relationship"],
        )
        return row

    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge by id. Returns True if a row was removed."""
        delete_sql = sql.SQL("DELETE FROM graph_edges WHERE edge_id = %(edge_id)s")
        count = await self.execute(delete_sql, {"edge_id": edge_id})
        return count == 1

    async def get_neighbours(
        self,
        document_id: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return (neighbour_documents, incident_edges) for the given document.

        An edge is incident to the document if either endpoint matches.
        Neighbour rows are full documents — search_documents-shaped — so the
        existing row_to_proto_document helper can convert them to DocumentListItems.
        """
        edges_sql = sql.SQL("""
            SELECT edge_id, source_id, target_id, relationship, directed, created_at
            FROM graph_edges
            WHERE source_id = %(document_id)s OR target_id = %(document_id)s
        """)
        edges = await self.fetchall(edges_sql, {"document_id": document_id})

        neighbour_ids = {
            str(edge["target_id"]) if str(edge["source_id"]) == document_id
            else str(edge["source_id"])
            for edge in edges
        }
        if not neighbour_ids:
            return [], edges

        neighbours_sql = sql.SQL("""
            SELECT * FROM documents WHERE document_id = ANY(%(ids)s)
        """)
        neighbours = await self.fetchall(neighbours_sql, {"ids": list(neighbour_ids)})
        neighbours = await self._enrich_documents_with_junction_data(neighbours)
        return neighbours, edges

    async def list_edges_between(
        self,
        document_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Return every edge whose endpoints both lie in document_ids."""
        if not document_ids:
            return []
        query = sql.SQL("""
            SELECT edge_id, source_id, target_id, relationship, directed, created_at
            FROM graph_edges
            WHERE source_id = ANY(%(ids)s) AND target_id = ANY(%(ids)s)
        """)
        return await self.fetchall(query, {"ids": document_ids})
