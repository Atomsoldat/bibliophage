-- Enable pgvector extension (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;

-- start_position is equal to the first character index in the parent document text,
-- that is part of the chunk
-- 
-- chunk_length is equal to the number of characters contained in the chunk
-- 
-- end_position is equal to the  index of the first character after the beginning
-- of the chunk in the parent document, that no longer belongs to the chunk
-- so start_position + chunk_length = end_position
--
-- this kind of convention is a common thing in many programming languages, but not in all
-- there's a whole flame war going on since forever whether arrays
-- should be zero indexed / open or closed on either side / ...
-- and judging by how much i have read on the topic for what should be an implementation detail
-- i don't think there is a universal answer
--
-- since we do the substring extraction in python code, and  python represents strings as sequences,
-- it made sense to me to store the data in a way that makes the python code more concise
-- https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str
-- substring = my_string[1:5]
-- as per our previous definitions
-- substring = my_string[start_position:end_position]
-- see the notes on how they interpret the meaning of the beginning and the end of a sequence slice
-- https://docs.python.org/3/library/stdtypes.html#typesseq
-- 
-- minor side note: PostgreSQL does this differently for substrings, which is how we
-- fell down this rabbit hole (do it in python vs do it in postgres) to begin with
-- e.g.
-- substr(string text, start integer [, count integer ] ) → text
-- or
-- substring(string from start for count)
-- https://www.postgresql.org/docs/18/functions-string.html
CREATE TABLE IF NOT EXISTS document_chunks (
    vector_id UUID DEFAULT uuidv7(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    start_position INT NOT NULL,
    end_position INT NOT NULL,
    -- we decided for the more pythonic way of representing our bounds for now
    --chunk_length INT NOT NULL,
    -- 1024 matches BAAI/bge-large-en-v1.5
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (vector_id),
    CHECK (start_position >= 0 AND end_position > start_position)
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

