## Why

`DocumentType` is a closed proto enum with a dedicated `documents.document_type` column, yet nothing in the retrieval/LLM pipeline actually reads it. The app already has a generic tag system (`tags` / `tag_values` / `map_documents_to_tags`) built for exactly this kind of open-ended classification. Keeping a parallel, hardcoded enum for one facet (document type) while every other facet (genre, tone, world, ...) goes through tags is unnecessary duplication, and the enum's own comment already flags it as too rigid ("a single Document may contain multiple types of information"). Routing document type through the tag system removes that duplication and lets the type vocabulary grow without a proto/schema change.

## What Changes

- **BREAKING**: Remove the `DocumentType` enum and the `Document.type` / `DocumentListItem.type` fields from the `bibliophage.v1alpha3` document API. Document type is now expressed as a tag named `document_type` with a single value (e.g. `document_type: rulebook`).
- **BREAKING**: Drop the `documents.document_type` column (and its `NOT NULL` constraint) from the Postgres schema. No data migration — existing column values are discarded (confirmed with user: no environment currently has data worth preserving).
- **BREAKING**: Remove `DocumentFilter.type_filters` from the search API. Filtering by document type is not reimplemented in this change (see Impact) — it returns once tag-based filtering (any-of-these-values-for-one-tag-name) ships in a later change.
- Ingestion (`ingestion/service.py`) stops inferring a document type from the uploaded PDF's declared type string. It keeps deriving `source_type` (CORE/SUPPLEMENT) from that same string unchanged — that's a separate concept, out of scope for this change — but no longer produces or writes a `document_type` value on the caller's behalf. `document_type` becomes just another tag the user may include in the upload's tag list, same as any other tag; nothing predicts or defaults it during ingestion.
- Remove the now-dead `document_type` field from `chat/llm_access.py`'s `DocumentContext` (set today, never read).
- Web UI: remove `DocumentTypeFilter.vue` and its use in `Library.vue` / `GraphSearchPanel.vue`; remove type display/formatting from `DocumentTable.vue`; drop the `DocumentType.NOTE` default in `GlobalEditorWindows.vue` entirely — new journal entries get no `document_type` tag unless the user adds one. This intentionally regresses the one currently-working facet filter in the UI — accepted tradeoff, called out in design.md, tracked for a future tag-filtering change.
- Out of scope (explicitly deferred, not touched by this change): `Metadata.publication_type` stays as-is, even though it overlaps semantically with document type. Building tag-based search/filter UI or query semantics (including OR-across-values-for-one-tag) is a later change. `SourceType`/authority weighting is untouched by this change — that's a separate change (see Scope note).

## Scope note

This was originally explored as one combined change covering both `DocumentType` and `SourceType`, then split into two changes at the user's request. This change covers `DocumentType` only. `SourceType`/authority-weighting removal is a separate change (`remove-source-type`), sequenced after this one since its design assumes `document_type` has already stopped being inferred during ingestion.

## Capabilities

### New Capabilities
- `document-classification`: how a document's type/kind is recorded and set (via the generic tag system instead of a dedicated enum field), set explicitly by the user rather than inferred.

### Modified Capabilities
(none — no prior spec exists for document search/filtering in this project; the removal of `type_filters` is captured as part of `document-classification` since the field is intrinsic to the enum being removed, not a separately specified search capability)

## Impact

- **API**: `api/bibliophage/v1alpha3/document.proto` (or a new `v1alpha4`, to be decided in design.md) — remove `DocumentType` enum, `Document.type`, `DocumentListItem.type`, `DocumentFilter.type_filters`. Regenerate Python and TS proto bindings.
- **DB**: `python-server/src/db/schema/documents.sql` — drop `document_type` column; no data migration.
- **Python server**: `db/postgres_db.py` (store/update/search document methods), `documents/service.py`, `proto_converters.py`, `chat/llm_access.py` (`DocumentContext`), `ingestion/service.py` (remove the `doc_type` inference branch; `source_type` inference is unchanged).
- **Web UI**: `DocumentTypeFilter.vue` (removed), `Library.vue`, `GraphSearchPanel.vue`, `DocumentTable.vue`, `GlobalEditorWindows.vue`, `useBulkMetadataEdit.ts`, `utils/protoHelpers.ts`.
- **Tests**: `python-server/tests/test_proto_converters.py` references `document_type` row data and `DOCUMENT_TYPE_UNSPECIFIED`; needs updating for the new shape.
- No change to `Metadata.publication_type`, the generic tag query/filter API, or `SourceType`/authority weighting (separate change).
