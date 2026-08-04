## Context

See proposal.md for motivation. Relevant current state:

- The tag system's real schema (`python-server/src/db/schema/documents.sql`) is `tags(tag_id, title)` + `tag_values(tag_value_id, tag_value, tag_id)` + `map_documents_to_tags(document_id, tag_id, tag_value_id)`. `tags.title` and `tag_values.tag_value` both have `CHECK (... = lower(...))` — tag names and values are lowercase-only.
- **The tag read/write code does not match that schema.** `postgres_db.py` (`store_document`, `update_document`, `_enrich_documents_with_junction_data`) reads and writes a `tags.info` column that does not exist anywhere in the schema, and never touches `tag_values` or the `tag_value_id` column on the mapping table. Any document store/update that includes tags, or any read that enriches documents with tags, currently fails against the real schema (`column "info" does not exist`). Use the database schema definition as the authoritative source of truth.
- **`proto_converters.py`'s `row_to_proto_document` also references a `systems` field** (`proto.systems.extend(...)`, `row.get("systems", [])`) that doesn't exist on `Document`/`DocumentListItem` in the current `v1alpha3/document.proto`, nor in the generated `document_pb2.pyi` — confirmed by direct inspection of both files. Calling this function raises `AttributeError`. A test (`test_row_to_proto_document_systems_populated`) still asserts the old behavior.
- Both of the above are leftovers from the earlier canon/system-removal refactor (commit `f091a93`) that were never reconciled with the schema changes that followed it. They are not caused by this change, but this change's core requirement — write and read a `document_type` tag — runs directly through `store_document`, `update_document`, `_enrich_documents_with_junction_data`, and `row_to_proto_document`. There is no way to implement "document type as a tag" without those functions actually working.
- No migration tooling exists in this project. Schema changes to date (the last five commits) have all been made by editing the `CREATE TABLE IF NOT EXISTS` scripts in place and relying on `initialise_schema` to (re)create tables — there is no `ALTER TABLE` / versioned-migration precedent to follow.

## Goals / Non-Goals

**Goals:**
- Make `document_type` a tag end-to-end: proto, DB, UI. Set only by the user — no component infers or defaults its value from content or metadata.
- Make the tag write/read path this change depends on actually functional against the real schema (`tags` + `tag_values` + `map_documents_to_tags`), since it's a hard prerequisite, not an unrelated cleanup.
- Do fix `proto_converters.py`'s dead `systems` reference beyond what's required to stop `row_to_proto_document` from throwing (i.e. delete the two dead lines). Do remove other parts of `proto_converters.py` or `postgres_db.py`, so long as the removal targets dead code, or code that implements functionality that will be removed in this step.

**Non-Goals:**
- Do not build tag-based search/filtering (deferred, per proposal).
- Do not touch `Metadata.publication_type` (deferred, per proposal).
- Do not introduce a migration framework. Schema edits follow existing project convention (edit the `CREATE TABLE` script in place).
- Do not infer, default, or predict a `document_type` value anywhere (not during PDF ingestion, not elsewhere). The prior enum-removal exploration considered classifying PDFs automatically on ingest; that idea is dropped for this change — the tag is user-set only.
- Do not touch `SourceType`/authority weighting. That's a separate change (`remove-source-type`), scoped and sequenced independently — see proposal.md's Scope note.

## Decisions

### Edit `v1alpha3/document.proto` in place, don't bump to v1alpha4
The prior canon-removal change (`f091a93`) edited `v1alpha3/document.proto` directly rather than forking a new version, even though it removed fields. `v1alpha1`/`v1alpha2` appear to be historical snapshots, not parallel-maintained APIs. Following the same precedent keeps this change consistent with how the project has been versioning its API so far, and avoids the overhead of standing up a `v1alpha4` tree for a pre-launch, single-consumer (the bundled web UI) API.

### Repair the tag read/write path as a prerequisite, scoped narrowly
Rewrite `store_document`/`update_document`'s tag-handling to resolve tag values through `tag_values` (create-if-missing, unique on `(tag_id, tag_value)`) and write `tag_value_id` into `map_documents_to_tags`, and rewrite `_enrich_documents_with_junction_data` to join through `tag_values` instead of reading `tags.info`. Delete the two dead `systems` lines in `row_to_proto_document`. This is the minimum needed to make `document_type` tags actually persist and read back — not a general tag-system audit.

**Alternative considered**: leave the broken tag path alone and find some other way to persist `document_type`. Rejected — there is no other tag write path in the codebase, and inventing a second, parallel one just to avoid touching the broken code would recreate the exact duplication this change is trying to remove.

### Tag value vocabulary: lowercase snake_case strings, open (not DB-enforced) vocabulary
Given the `CHECK (title = lower(title))` / `CHECK (tag_value = lower(tag_value))` constraints, `document_type` tag values are lowercase snake_case (`note`, `lore_fragment`, `session_log`, `rulebook`, `expansion`, `adventure`, `bestiary`, `character`, `location`, `object`, `quest`) — the same vocabulary as the removed enum, lowercased. Nothing in the DB enforces this specific set; it's an open tag like any other, matching how every other tag facet already works. Client-side (UI) code may use this fixed list as a suggested/known set of values, but the system does not reject other values.

**Alternative considered**: enforce the closed vocabulary via a `CHECK` constraint on `tag_values` scoped to the `document_type` tag. Rejected — that reintroduces the rigidity this change exists to remove, and no other tag currently has such a constraint.

### Ingestion treats `document_type` as an ordinary tag, with no special-casing
`ingestion/service.py` already accepts a generic `tags` list on the PDF upload request and passes it straight through to `store_document`. `document_type` needs no bespoke handling there: if the caller includes a `document_type` tag among the upload's tags, it's stored like any other tag; if not, the document simply has none. The existing `doc_type`/`source_type` if/elif block is split — the `source_type` branch (CORE/SUPPLEMENT, unrelated to this change) is kept exactly as-is, and the `doc_type` branch is deleted outright rather than repointed at a tag write.

**Alternative considered**: keep the classification logic but write its output as a suggested/default `document_type` tag the user can override. Rejected per explicit user instruction — no prediction, even as a default; the field starts empty unless the user sets it.

### No data migration for existing `document_type` column values
Following existing project convention (no migration tooling; schema changes so far have been edit-in-place), the `document_type` column is simply dropped rather than migrated into `map_documents_to_tags` rows. Confirmed with user: no environment currently has `document_type` data worth preserving, so this is a deliberate decision, not an oversight.

## Risks / Trade-offs

- **[Risk] Dropping `document_type` without migration loses existing classification data on any environment with real data** → Mitigation: confirmed acceptable with user; no migration tooling exists to do otherwise without introducing new machinery.
- **[Risk] Removing `DocumentTypeFilter.vue` regresses the only working facet-filter UX today** → Mitigation: explicitly called out in proposal.md as an accepted, temporary trade-off; restored once tag-based filtering ships.
- **[Risk] Repairing the tag read/write path touches shared code used by every tag, not just `document_type`** → Mitigation: the fix makes behavior match the already-committed schema (no behavior change to the *intended* tag contract, only to what currently crashes); covered by existing/updated unit tests in `test_proto_converters.py` plus new tests for the tag storage functions.

## Migration Plan

1. Update proto (`document.proto`), regenerate Python + TS bindings.
2. Update `documents.sql` (drop `document_type` column).
3. Fix `store_document` / `update_document` / `_enrich_documents_with_junction_data` to use `tag_values` correctly; fix `row_to_proto_document` (drop dead `systems` lines).
4. Update `ingestion/service.py` to delete the `doc_type` inference branch entirely (keep `source_type` inference unchanged); stop passing `doc_type` to `store_document` — `document_type` now only ever comes from the caller's own `tags` list, unchanged from how every other tag already flows through.
5. Update `chat/llm_access.py` (drop `DocumentContext.document_type`) and `chat/service.py` call site.
6. Update web UI: remove `DocumentTypeFilter.vue` and its call sites; update `GlobalEditorWindows.vue`, `DocumentTable.vue`, `useBulkMetadataEdit.ts`, `utils/protoHelpers.ts`.
7. Update `test_proto_converters.py` for the new shape; add coverage for tag storage.
Rollback: revert the commit(s); no external data dependency is introduced since no migration is performed.
