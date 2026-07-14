# Phase 1: Backend Foundation - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers three backend capabilities: (1) a working `update_document` RPC so users can save edits to existing documents, (2) junction table wiring so systems and tags round-trip correctly through store/load/update, and (3) a domain-based directory restructure of the Python server. No frontend changes. No new RPCs.

</domain>

<decisions>
## Implementation Decisions

### Update Semantics
- **D-01:** Full replace strategy. Client sends the complete `Document` message; backend replaces all fields. No partial updates, no FieldMask.
- **D-02:** When content changes, set `embeddings_current=false` to flag stale embeddings. Do NOT re-embed inline — re-embedding is a separate operation.
- **D-03:** Return the full updated document in `UpdateDocumentResponse.document`, re-fetched from DB so the frontend gets server-computed fields (`updated_at`, `character_count`).
- **D-04:** If the document ID doesn't exist, return `success=false` with message "Document not found". No upsert behavior.

### Systems & Tags Data Model
- **D-05:** Systems must pre-exist in the `systems` table. When a document references a system name, resolve it by looking up `systems.title`. If any system name is unknown, fail the entire store/update operation with an error.
- **D-06:** Tags must pre-exist in the `tags` table. Same strict validation as systems — fail on unknown tag names.
- **D-07:** Tag values (the `repeated string values` from proto `Tag`) are stored as JSONB in the existing `tags.info` column. No schema migration needed.
- **D-08:** Junction table wiring: delete-and-reinsert pattern within a transaction for both `map_documents_to_systems` and `map_documents_to_tags` on store and update.

### Restructuring Strategy
- **D-09:** Big bang restructure — move all 16 files into domain packages in a single commit. The codebase is small enough for this to be manageable.
- **D-10:** Shared files (`proto_converters.py`, `config.py`, `server.py`) stay at `src/` root. They are cross-cutting and don't belong to a single domain.
- **D-11:** Skip backward-compatible `__init__.py` re-exports (STRUCT-03 not needed). Big bang updates all imports at once, so re-exports would be dead code from day one.

### Ordering & Dependencies
- **D-12:** Execute restructure first (pure refactor, no behavior change), then wire junction tables in new locations, then implement `update_document`. Each step builds on the previous.
- **D-13:** Junction table wiring and `update_document` are separate plans. Three plans total: (1) restructure, (2) junction tables, (3) update_document.

### Claude's Discretion
- Target domain packages: `documents/`, `ingestion/`, `embeddings/`, `chat/`, `graph/`, `db/` — exact file-to-package mapping is Claude's discretion based on dependency analysis.
- SQL query construction for junction table JOINs — implementation details left to planner.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Proto Definitions
- `api/bibliophage/v1alpha3/document.proto` — UpdateDocument RPC (lines 13, 203-219), Document message (lines 48-83), DocumentType/SourceType enums
- `api/bibliophage/v1alpha3/common.proto` — Tag message (lines 11-17): `name` + `repeated string values`

### Database Schema
- `python-server/src/db_schema/documents.sql` — Junction tables `map_documents_to_systems` (lines 61-66), `map_documents_to_tags` (lines 69-73), lookup tables `systems` (lines 52-57), `tags` (lines 45-50)

### Current Implementation (read before restructuring)
- `python-server/src/document_service_implementation.py` — `update_document` stub with pseudocode (lines 112-160)
- `python-server/src/postgres_db.py` — `store_document` with junction TODOs (lines 200-201), `search_documents` with broken column refs (lines 246, 249), `transaction()` context manager (lines 155-165)
- `python-server/src/proto_converters.py` — `row_to_proto_document` with systems/tags TODOs (lines 57-66), `metadata_proto_to_dict` (lines 102-117)
- `python-server/src/server.py` — Singleton init in lifespan (lines 33-41), service registration (lines 88-94)

### Requirements
- `.planning/REQUIREMENTS.md` — NOTE-01, NOTE-06, NOTE-07, STRUCT-01, STRUCT-02, STRUCT-03 mapped to this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `postgres_db.transaction()` context manager (lines 155-165): Use for atomic junction table delete-reinsert
- `row_to_proto_document()` converter (proto_converters.py): Extend to JOIN and assemble systems/tags from junction tables
- `metadata_proto_to_dict()` helper: Reuse for update_document metadata handling
- `datetime_to_proto_ts()` helper: Reuse for timestamp conversion in update response

### Established Patterns
- Singleton pattern: Module-level `_instance` with getter function. All new domain packages must follow this.
- Service implementation: Class with async methods matching proto RPC signatures. Import DB singleton via `get_postgres_db()`.
- Error handling: `try/except` with `logger.exception()`, return response with `success=false` and `message`.

### Integration Points
- `server.py` imports all service implementations — must be updated after restructure
- Test imports in `python-server/tests/` — must be updated after restructure
- `conftest.py` fixtures create/cleanup test documents — will need junction table awareness

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Backend Foundation*
*Context gathered: 2026-06-08*
