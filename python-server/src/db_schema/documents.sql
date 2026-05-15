-- the idea here is that we use every typical approach
-- for representing "multiple values per entry"
-- then we can see how we like each of them and
-- possibly migrate the others as needed
-- i.e. junction tables, JSONB or maybe array columns with GIN indices



-- we do not generate default values, other than IDs and dates (the database is authoritative on that)
-- the database has the job of enforcing the database schema, i.e. to ensure constraints are met
-- but the database should not presume what a client might have meant, when he left a field emptym
-- instead, it should slap him on the wrist and tell him to fix his code

-- we adjust column names that are identical with SQL keywords and would otherwise require quoting
-- we prefix the table name to the id field of each table
-- other than that, we do not perform additional namespacing
-- unless it actually is required for clarity

-- we keep our schema in sql files
-- TODO: How do we best document the meaning of our fields then?


-- systems are mapped to documents via a mapping table
-- tags are mapped to documents via a mapping table
CREATE TABLE IF NOT EXISTS documents (
  document_id UUID DEFAULT uuidv7(),
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
  content TEXT NOT NULL,
  -- GENERATED means the value is derived from something else 
  -- and can not be inserted or updated directly
  -- STORED means populated at write time, not recalculated each time
  -- || is SQL string concatenation
  content_snippet TEXT GENERATED ALWAYS AS (
    CASE WHEN length(content) > 200 THEN left(content, 200) || '...' ELSE content END
  ) STORED,
  document_type TEXT NOT NULL,
  character_count INT NOT NULL,
  created_at TIMESTAMP DEFAULT now() NOT NULL,
  updated_at TIMESTAMP DEFAULT now() NOT NULL,
  PRIMARY KEY (document_id)
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id UUID DEFAULT uuidv7(),
    title TEXT NOT NULL,
    info TEXT,
    PRIMARY KEY (tag_id)
);

CREATE TABLE IF NOT EXISTS systems (
    system_id UUID DEFAULT uuidv7(),
    title TEXT NOT NULL,
    info TEXT,
    PRIMARY KEY (system_id)
);

-- TODO: we could have a column that describes how canonical/applicable
-- a document is for a system (core / extended / third party / ...)
CREATE TABLE IF NOT EXISTS map_documents_to_systems (
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    system_id UUID REFERENCES systems(system_id) ON DELETE CASCADE,
    info TEXT,
    PRIMARY KEY (document_id, system_id)
);


CREATE TABLE IF NOT EXISTS map_documents_to_tags (
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);


-- documents have tags, not topics
-- embeddings have topics, not tags (if we ever get to that)
-- *maybe* we can map topics and tags if we really want to...