"""Vector operations module.

Provides high-level functions for embedding, searching, and managing document chunks
using pgvector. This module sits on top of VectorDatabase and provides the business
logic for RAG operations.

The table schema stores:
- document_id: UUID of the source document
- chunk_id: Unique identifier for the chunk (e.g., "doc-uuid:chunk:0")
- content: The actual text content of the chunk
- embedding: Vector representation (pgvector type)
- metadata: JSONB field for additional chunk information (heading path, page numbers, etc.)
- created_at: Timestamp of when the chunk was embedded
"""
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from pgvector.psycopg import register_vector_async
from psycopg import sql
from psycopg.types.json import Jsonb

from config import get_settings
from vector_db import VectorDatabase

logger = logging.getLogger(__name__)

# Singleton instances
_vector_db: VectorDatabase | None = None
_embeddings_model: HuggingFaceEmbeddings | None = None


def get_vector_database() -> VectorDatabase:
    """Get the vector database singleton instance.

    Returns:
        VectorDatabase: Configured vector database repository

    Raises:
        Exception: If database initialization fails
    """
    global _vector_db
    if _vector_db is None:
        settings = get_settings()
        _vector_db = VectorDatabase(
            connection_url=str(settings.database.vector_db_url)
        )
        logger.info("Vector database instance created")
    return _vector_db


def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Get the embeddings model singleton instance.

    Returns:
        HuggingFaceEmbeddings: Configured HuggingFace embeddings model

    Note:
        The model is loaded lazily on first use and cached for subsequent calls.
        Model loading can take several seconds on first call.
    """
    global _embeddings_model
    if _embeddings_model is None:
        settings = get_settings()
        model_name = settings.embedding.embedding_model_name
        logger.info(f"Loading embeddings model: {model_name}")
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},  # TODO: Add GPU support via config
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info(f"Embeddings model loaded: {model_name}")
    return _embeddings_model


async def ensure_schema_exists():
    """Ensure the vector storage table exists with proper schema.

    Creates the 'document_chunks' table if it doesn't exist with:
    - id: BIGSERIAL primary key
    - document_id: TEXT (UUID of source document)
    - chunk_id: TEXT UNIQUE (e.g., "doc-uuid:chunk:0")
    - content: TEXT (chunk text content)
    - embedding: VECTOR(1024) (pgvector type - dimension matches BAAI/bge-large-en-v1.5)
    - metadata: JSONB (chunk metadata: heading paths, page numbers, etc.)
    - created_at: TIMESTAMPTZ (timestamp with timezone)

    Also creates indexes for efficient querying:
    - Index on document_id for deletion operations
    - HNSW index on embedding for similarity search
    - GIN index on metadata for filtering

    This function is idempotent - safe to call multiple times.
    """
    vector_db = get_vector_database()

    # SQL to create the table and indexes
    create_table_sql = """
    -- Enable pgvector extension (idempotent)
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Create table if not exists
    CREATE TABLE IF NOT EXISTS document_chunks (
        id BIGSERIAL PRIMARY KEY,
        document_id TEXT NOT NULL,
        chunk_id TEXT UNIQUE NOT NULL,
        content TEXT NOT NULL,
        embedding VECTOR(1024),
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- Create index on document_id for efficient deletion by document
    CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
        ON document_chunks(document_id);

    -- Create HNSW index for fast similarity search
    -- Using cosine distance as we normalize embeddings
    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops);

    -- Create GIN index on metadata for filtering by chunk properties
    CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
        ON document_chunks
        USING gin (metadata);
    """

    async def execute_schema(cursor):
        """Execute schema creation and return success."""
        # Note: psycopg doesn't support executing multiple statements in one call
        # when using server-side cursors, but we can use autocommit mode
        return True

    try:
        await vector_db.execute(create_table_sql, callback=execute_schema)
        logger.info("Vector database schema verified/created successfully")
    except Exception as e:
        logger.error(f"Failed to create vector database schema: {e}")
        raise


async def embed_chunks(
    document_id: str,
    chunks: list[dict[str, Any]]
) -> int:
    """Embed document chunks and store them in the vector database.

    Args:
        document_id: UUID of the source document
        chunks: List of chunk dictionaries with structure:
            {
                "chunk_id": "doc-uuid:chunk:0",
                "content": "text content",
                "metadata": {
                    "char_start": 0,
                    "char_end": 500,
                    "heading_path": ["Chapter 1", "Introduction"],
                    "description": "Introduction section"
                }
            }

    Returns:
        int: Number of chunks successfully embedded

    Raises:
        ValueError: If chunks list is empty or malformed
        Exception: If database operation fails

    Note:
        This function will delete any existing chunks for the document_id before
        inserting new ones to ensure consistency.
    """
    if not chunks:
        raise ValueError("Chunks list cannot be empty")

    # Validate chunk structure
    for chunk in chunks:
        if "chunk_id" not in chunk or "content" not in chunk:
            raise ValueError("Each chunk must have 'chunk_id' and 'content' fields")

    # Delete existing chunks for this document first
    await delete_document_chunks(document_id)

    # Get embeddings for all chunks
    embeddings_model = get_embeddings_model()
    contents = [chunk["content"] for chunk in chunks]

    logger.info(f"Generating embeddings for {len(contents)} chunks")
    embeddings = embeddings_model.embed_documents(contents)
    logger.info(f"Generated {len(embeddings)} embeddings")

    # Prepare insert data
    vector_db = get_vector_database()
    # TODO: think about how we handle time in generel
    # personally, i think UTC is pretty neat, but maybe people find that weird
    now = datetime.now(timezone.utc)


    async def insert_chunks(cursor):
        """Insert chunks with embeddings into database."""
        
        # define query using psycopg formatting
        insert_sql = sql.SQL("""
            INSERT INTO document_chunks
            (
                document_id,
                chunk_id,
                content,
                embedding,
                metadata,
                created_at
            )
            VALUES(
                %(document_id)s,
                %(chunk_id)s,
                %(content)s,
                %(embedding)s,
                %(metadata)s,
                %(created_at)s
            )
            ON CONFLICT (chunk_id) DO NOTHING
            """)

        rows = []
        for i, chunk in enumerate(chunks):
            rows.append({
                'document_id': document_id,
                'chunk_id': chunk['chunk_id'],
                'content': chunk['content'],
                'embedding': embeddings[i],  # The embedding vector
                'metadata': Jsonb(chunk.get('metadata', {})),  # Wrap dict in Jsonb for PostgreSQL
                'created_at': now
            })


        await cursor.executemany(
            insert_sql,
            rows
        )
        
        return cursor.rowcount

    count = await vector_db.execute("", callback=insert_chunks)
    logger.info(f"Inserted {count} chunks for document {document_id}")
    return count


async def delete_document_chunks(document_id: str) -> int:
    """Delete all chunks for a specific document.

    Args:
        document_id: UUID of the document whose chunks should be deleted

    Returns:
        int: Number of chunks deleted

    Note:
        This function is idempotent - calling it multiple times with the same
        document_id is safe and will return 0 on subsequent calls.
    """
    vector_db = get_vector_database()

    delete_sql = "DELETE FROM document_chunks WHERE document_id = %s"

    async def get_rowcount(cursor):
        """Return the number of deleted rows."""
        return cursor.rowcount

    count = await vector_db.execute(delete_sql, params=(document_id,), callback=get_rowcount)
    logger.info(f"Deleted {count} chunks for document {document_id}")
    return count


async def search_similar(
    query: str,
    top_k: int = 10,
    document_id: str | None = None
) -> list[dict[str, Any]]:
    """Search for chunks similar to the query using vector similarity.

    Args:
        query: The search query text
        top_k: Maximum number of results to return (default: 10)
        document_id: Optional filter to search within a specific document

    Returns:
        List of dictionaries with structure:
        {
            "chunk_id": "doc-uuid:chunk:0",
            "document_id": "doc-uuid",
            "content": "chunk text",
            "metadata": {...},
            "similarity": 0.85  # Cosine similarity score (0-1)
        }

    Note:
        Results are ordered by similarity (highest first).
        Uses cosine similarity as we normalize embeddings.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    # Generate embedding for query
    embeddings_model = get_embeddings_model()
    logger.info(f"Generating embedding for query: {query[:100]}...")
    query_embedding = embeddings_model.embed_query(query)

    # Build SQL with optional document_id filter
    if document_id is None:
        search_sql = """
        SELECT
            chunk_id,
            document_id,
            content,
            metadata,
            1 - (embedding <=> %s::vector) AS similarity
        FROM document_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        params = (query_embedding, query_embedding, top_k)
    else:
        search_sql = """
        SELECT
            chunk_id,
            document_id,
            content,
            metadata,
            1 - (embedding <=> %s::vector) AS similarity
        FROM document_chunks
        WHERE document_id = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        params = (query_embedding, document_id, query_embedding, top_k)

    vector_db = get_vector_database()

    async def fetch_results(cursor):
        """Fetch search results from cursor."""
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "chunk_id": row[0],
                "document_id": row[1],
                "content": row[2],
                "metadata": row[3],
                "similarity": float(row[4])
            })
        return results

    results = await vector_db.execute(search_sql, params=params, callback=fetch_results)
    logger.info(f"Found {len(results)} similar chunks")
    return results


async def get_chunk_count(document_id: str) -> int:
    """Get the number of chunks for a specific document.

    Args:
        document_id: UUID of the document

    Returns:
        int: Number of chunks stored for this document
    """
    vector_db = get_vector_database()

    count_sql = "SELECT COUNT(*) FROM document_chunks WHERE document_id = %s"

    async def fetch_count(cursor):
        """Fetch count result from cursor."""
        row = await cursor.fetchone()
        return row[0] if row else 0

    count = await vector_db.execute(count_sql, params=(document_id,), callback=fetch_count)
    return count


async def close_connections():
    """Close all database connections and clean up resources.

    This should be called when the application shuts down.
    """
    global _vector_db
    if _vector_db is not None:
        await _vector_db.close_pool()
        _vector_db = None
        logger.info("Vector operations connections closed")
