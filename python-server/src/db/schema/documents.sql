-- the idea here is that we use every typical approach
-- for representing "multiple values per entry"
-- then we can see how we like each of them and
-- possibly migrate the others as needed
-- i.e. junction tables, JSONB or maybe array columns with GIN indices



-- we do not generate default values, other than IDs and dates (the database is authoritative on that)
-- the database has the job of enforcing the database schema, i.e. to ensure constraints are met
-- but the database should not presume what a client might have meant, when he left a field empty
-- instead, it should slap him on the wrist and tell him to fix his code

-- we adjust column names that are identical with SQL keywords and would otherwise require quoting
-- we prefix the table name to the id field of each table
-- other than that, we do not perform additional namespacing
-- unless it actually is required for clarity

-- we keep our schema in sql files
-- TODO: How do we best document the meaning of our fields then?


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
  -- TODO: we could calculate this in the database
  character_count INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  embeddings_current BOOLEAN DEFAULT TRUE NOT NULL,
  PRIMARY KEY (document_id)
);

-- TODO: make sure, that users do not enter multiple permutations of the same canon / tag
-- e.g. SciFi vs scifi vs Sci-Fi
-- perhaps we can perform a trigram search before entry, and if there is a match
-- return that and ask whether this preexisting one is acceptable

-- TODO: suggest existing keys / values as the user types

-- aside from the usual metadata like genres or theme,
-- we also implement document canons / systems via tags
CREATE TABLE IF NOT EXISTS tags (
    tag_id UUID DEFAULT uuidv7(),
    title TEXT UNIQUE NOT NULL,

    PRIMARY KEY (tag_id),
    -- only allow lower case
    CHECK (title = lower(title))
);

CREATE TABLE IF NOT EXISTS tag_values (
    tag_value_id UUID DEFAULT uuidv7(),
    -- only tags with values store their values here, so this should not be NULL
    tag_value TEXT NOT NULL,
    tag_id UUID NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,

    PRIMARY KEY (tag_value_id),
    -- allow only one assignment of a given tag_value per tag_id
    UNIQUE (tag_id, tag_value),
    -- allow creating the mapping only once for each pair
    UNIQUE (tag_id, tag_value_id),
    CHECK (tag_value = lower(tag_value))
);

-- what values a tag contains for a given document (e.g. genre: scifi, fantasy, ...)
-- each tuple of document_id, tag_id, tag_value_id is unique, so we can have multiple values for a tag such as
-- genre: fantasy
-- genre: comedy
-- on a single document. All NULLs gets treated as the same tag_value_id
CREATE TABLE IF NOT EXISTS map_documents_to_tags (
    -- we put this in here so we can have something as a primary key
    -- this is necessary, because we made tag_value_id nullable
    map_id UUID DEFAULT uuidv7(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,
    tag_value_id UUID,

    PRIMARY KEY (map_id),
    -- we did not make this our primary key, because tag_value_id needs to be nullable
    UNIQUE NULLS NOT DISTINCT (document_id, tag_id, tag_value_id),
    FOREIGN KEY (tag_id ,tag_value_id) REFERENCES tag_values (tag_id, tag_value_id) ON DELETE CASCADE
);

CREATE INDEX ON map_documents_to_tags (tag_id, tag_value_id);



-- documents have tags, not topics
-- embeddings have topics, not tags (if we ever get to that)
-- *maybe* we can map topics and tags if we really want to...