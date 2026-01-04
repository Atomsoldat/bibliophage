#!/bin/bash
set -e

# This script runs during PostgreSQL initialization to enable the pgvector extension
# The ankane/pgvector image includes the extension, we just need to enable it

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable the pgvector extension for vector similarity search
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Verify extension is installed
    SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
EOSQL

echo "pgvector extension enabled successfully"
