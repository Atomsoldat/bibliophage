## 1. API / Proto

- [x] 1.1 Remove `SourceType` enum, `Document.source_type`, and `DocumentListItem.source_type` from `api/bibliophage/v1alpha3/document.proto`
- [x] 1.2 Remove `ContextDocumentInfo.authority` from `api/bibliophage/v1alpha3/chat.proto`
- [x] 1.3 Regenerate Python proto bindings (`document_pb2.py`/`.pyi`, `chat_pb2.py`/`.pyi`)
- [x] 1.4 Regenerate TypeScript proto bindings (`document_pb.ts`, `chat_pb.ts` and related)

## 2. Database schema

- [x] 2.1 Drop the `source_type` column from `python-server/src/db/schema/documents.sql` (no data migration, per design.md)

## 3. Server-side: document storage

- [x] 3.1 Update `store_document`/`update_document` in `postgres_db.py` to drop the `source_type` parameter and its column reference in the INSERT/UPDATE statements
- [x] 3.2 Remove the `proto.source_type = getattr(document_api, source_type_str, ...)` block from `row_to_proto_document` in `proto_converters.py`
- [x] 3.3 Update `documents/service.py` (`store_document`, `update_document`) to drop `SourceType` enum conversions (`document_api.SourceType.Name(...)`)

## 4. Server-side: ingestion

- [x] 4.1 In `ingestion/service.py`, delete the remaining PDF-type classification if/elif block entirely (it currently only produces `source_type`, `document_type` inference having already been removed) — nothing replaces it. Leave `request.pdf.type` alone where it feeds `Metadata.publication_type`
- [x] 4.2 Update the `store_document` call in `ingestion/service.py` to stop passing a `source_type` argument

## 5. Server-side: chat / LLM context

- [x] 5.1 In `chat/llm_access.py`, delete `AUTHORITY_WEIGHTS`, `AUTHORITY_LABELS`, `_get_authority_label`, and `DocumentContext.authority_weight`
- [x] 5.2 Remove the `source_type` field from `chat/llm_access.py`'s `DocumentContext` dataclass
- [x] 5.3 Update `_build_context_prompt` to drop the `sort_by_authority` parameter and sorting step, and change the per-document label from `--- Source: {name} ({authority_label}) ---` to `--- Source: {name} ---`
- [x] 5.4 Remove the "Prioritise information from Official Rules sources over other sources" line from `generate_content`'s default system prompt
- [x] 5.5 Remove the `"authority": doc.authority_weight` entry from `query_with_context`'s returned metadata
- [x] 5.6 In `chat/service.py`, remove the `source_type=...` argument from the `DocumentContext(...)` call site in `_fetch_context_documents`
- [x] 5.7 In `chat/service.py`'s `_build_metadata_chunk`, remove `authority=doc.authority_weight` from the `ContextDocumentInfo(...)` construction

## 6. Web UI

- [x] 6.1 Update `GlobalEditorWindows.vue` to drop `sourceType: SourceType.GM_NOTES` when creating new journal entries — the field no longer exists

## 7. Tests

- [x] 7.1 Update `python-server/tests/test_proto_converters.py`: remove/replace `source_type`-column and `SOURCE_TYPE_UNSPECIFIED` assertions
- [x] 7.2 Update `conftest.py`, `test_document.py`, `test_graph_db.py`, `test_graph_service.py` to stop setting `source_type`/`GM_NOTES` on constructed documents/requests
- [x] 7.3 Add a test confirming ingestion no longer sets any `source_type` value
- [x] 7.4 Add/update tests for `_build_context_prompt` confirming no authority-based sorting or labeling occurs
