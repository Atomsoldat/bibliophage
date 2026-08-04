## Why

`SourceType` is a hardcoded, closed classification of "how trustworthy is this document" (`CORE`, `SUPPLEMENT`, `GM_NOTES`, `PLAYER_NOTES`, `SESSION_LOG_RECORD`, `GENERATED`, `COMMUNITY`) that reorders and labels LLM context ("Official Rules" vs "Player Notes" vs "LLM-Generated") based on a value the user has to correctly assign up front. That's a premature, speculative authority model this project isn't ready to get right yet. Better to treat every document equally for now and reintroduce authority weighting later, deliberately, once there's an actual need driving its design (e.g. once real conflicting-source scenarios show up in practice).

## Scope note

This was originally explored bundled together with `DocumentType` removal, then split into two changes per user request. This change assumes `document-type-as-tag` has already landed: `document_type`/`DocumentType` no longer exist, ingestion no longer infers a document type, and the tag read/write path (`store_document`/`update_document`/`_enrich_documents_with_junction_data`) has already been repaired to work against the real tag schema. This change does not touch tags at all — `source_type` has no tag-based replacement, it is simply removed.

## What Changes

- **BREAKING**: Remove the `SourceType` enum and the `Document.source_type` / `DocumentListItem.source_type` fields from the `bibliophage.v1alpha3` document API. There is no replacement field — authority is simply not tracked.
- **BREAKING**: Drop the `documents.source_type` column (and its `NOT NULL` constraint) from the Postgres schema. No data migration — existing column values are discarded (same rationale as `document_type`: no migration tooling, no environment with data worth preserving).
- **BREAKING**: Remove `ContextDocumentInfo.authority` from `chat.proto` — the chat streaming metadata no longer reports a per-document authority score, since none is computed.
- Ingestion (`ingestion/service.py`) drops its PDF-type-string classification entirely. After `document-type-as-tag`, the classification if/elif block only produces `source_type` (its `doc_type` branch was already removed); this change deletes that remaining block outright — nothing replaces it. `request.pdf.type` itself is untouched where it feeds `Metadata.publication_type` (out of scope).
- `chat/llm_access.py`: remove `AUTHORITY_WEIGHTS`, `AUTHORITY_LABELS`, `DocumentContext.source_type`, `DocumentContext.authority_weight`, and `_get_authority_label`. `_build_context_prompt` stops sorting documents by authority (keeps whatever order it's given) and stops labeling each source with an authority tag (`--- Source: {name} ({label}) ---` becomes `--- Source: {name} ---`). The default system prompt's "Prioritise information from Official Rules sources over other sources" instruction is removed (nothing distinguishes sources anymore).
- Web UI: drop the `SourceType.GM_NOTES` default in `GlobalEditorWindows.vue` — new journal entries get no source type, since the field no longer exists.
- Out of scope: designing what a future authority/trust system looks like. This change only removes the current one; how (or whether) it comes back later is deliberately undecided — "when it is actually needed."

## Capabilities

### New Capabilities
- `document-authority`: documents carry no authority/trust classification; LLM context assembly treats every document equally (no weighting, sorting, or labeling by source authority).

### Modified Capabilities
(none)

## Impact

- **API**: `api/bibliophage/v1alpha3/document.proto` — remove `SourceType` enum, `Document.source_type`, `DocumentListItem.source_type`. `api/bibliophage/v1alpha3/chat.proto` — remove `ContextDocumentInfo.authority`. Regenerate Python and TS proto bindings.
- **DB**: `python-server/src/db/schema/documents.sql` — drop `source_type` column; no data migration.
- **Python server**: `db/postgres_db.py` (store/update document methods), `documents/service.py`, `proto_converters.py`, `chat/llm_access.py` (`AUTHORITY_WEIGHTS`, `AUTHORITY_LABELS`, `DocumentContext`, `_build_context_prompt`, `_get_authority_label`), `chat/service.py` (`_fetch_context_documents`, `_build_metadata_chunk`, `query_with_context` metadata), `ingestion/service.py` (delete the remaining PDF-type classification block).
- **Web UI**: `GlobalEditorWindows.vue`.
- **Tests**: `test_proto_converters.py`, `test_document.py`, `test_graph_db.py`, `test_graph_service.py`, `conftest.py` all set or assert `source_type` (mostly `GM_NOTES`) on documents; need updating.
- No change to `document_type`/tags (handled by the prerequisite `document-type-as-tag` change), `Metadata.publication_type`, or the generic tag query/filter API.
