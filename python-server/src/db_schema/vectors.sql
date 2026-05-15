-- Enable pgvector extension (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    vector_id UUID DEFAULT uuidv7(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_id TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    -- 1024 matches BAAI/bge-large-en-v1.5
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (vector_id)
);

-- Create index on document_id for efficient fetching/deletion by document
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
    ON document_chunks(document_id);

-- Create HNSW (Hierarchical Navigable Small World) index for fast similarity search
-- Using cosine distance as we normalize embeddings
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);

-- Create GIN index on metadata for filtering by chunk properties
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
    ON document_chunks
    USING gin (metadata);

