-- graph_edges: connections between documents
--
-- Nodes are simply documents. An edge is therefore just a pair of document_ids plus an optional
-- relationship label.
--
-- For undirected edges we enforce a canonical storage order
-- (source_id < target_id) via a CHECK constraint. That makes a plain UNIQUE
-- on (source_id, target_id, relationship) sufficient to prevent duplicates,
-- without needing a partial index using LEAST/GREATEST. Directed edges may
-- go in either direction, and A→B vs B→A are correctly distinct.
--
-- The application code is responsible for swapping source/target before
-- INSERT when directed=false; the CHECK below catches anyone who forgets.

CREATE TABLE IF NOT EXISTS graph_edges (
    edge_id      UUID DEFAULT uuidv7(),
    source_id    UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    target_id    UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    relationship TEXT NOT NULL DEFAULT 'RELATED',
    directed     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT now() NOT NULL,
    PRIMARY KEY (edge_id),

    CONSTRAINT graph_edges_no_self CHECK (source_id <> target_id),
    CONSTRAINT graph_edges_canonical_undirected CHECK (directed OR source_id < target_id),

    UNIQUE (source_id, target_id, relationship)
);

CREATE INDEX IF NOT EXISTS graph_edges_source_idx ON graph_edges (source_id);
CREATE INDEX IF NOT EXISTS graph_edges_target_idx ON graph_edges (target_id);
