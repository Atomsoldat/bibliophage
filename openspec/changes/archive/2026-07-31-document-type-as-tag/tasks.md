## 1. API / Proto

- [x] 1.1 Remove `DocumentType` enum, `Document.type`, `DocumentListItem.type`, and `DocumentFilter.type_filters` from `api/bibliophage/v1alpha3/document.proto`
- [x] 1.2 Regenerate Python proto bindings (`document_pb2.py`, `document_pb2.pyi`)
- [x] 1.3 Regenerate TypeScript proto bindings (`document_pb.ts` and related)

## 2. Database schema

- [x] 2.1 Drop the `document_type` column from `python-server/src/db/schema/documents.sql` (no data migration, per design.md)

## 3. Tag storage repair (prerequisite for document_type tags to work at all)

- [x] 3.1 Rewrite `store_document`'s tag-handling in `postgres_db.py` to resolve/create rows in `tag_values` and write `tag_value_id` into `map_documents_to_tags`, instead of the nonexistent `tags.info` column
- [x] 3.2 Apply the same fix to `update_document`'s tag-handling
- [x] 3.3 Rewrite `_enrich_documents_with_junction_data` to join through `tag_values` instead of reading `tags.info`
- [x] 3.4 Remove the dead `proto.systems` / `row.get("systems", [])` lines from `row_to_proto_document` in `proto_converters.py`
- [x] 3.5 Remove `proto.type = getattr(document_api, row["document_type"], ...)` from `row_to_proto_document`; tags (including `document_type`) already flow through the existing tag-conversion loop

## 4. Server-side: ingestion and chat

- [x] 4.1 In `ingestion/service.py`, delete the `doc_type` branch of the PDF-type inference if/elif entirely (keep the `source_type` branch unchanged — that's a separate, later change); stop passing a `doc_type` argument to `store_document` — `document_type` is only ever set if the caller included it in the upload's `tags`, exactly like any other tag, with no inference or default applied
- [x] 4.2 Remove `document_type` from `chat/llm_access.py`'s `DocumentContext` dataclass
- [x] 4.3 Remove the `document_type=doc_data["document_type"]` argument at the `DocumentContext(...)` call site in `chat/service.py`
- [x] 4.4 Update `documents/service.py` (`store_document`, `update_document`, `search_documents`) to drop all `DocumentType` enum conversions (`document_api.DocumentType.Name(...)`) and `type_filters` handling

## 5. Web UI

- [x] 5.1 Remove `web-ui/src/components/DocumentTypeFilter.vue`
- [x] 5.2 Remove its usage from `Library.vue` and `GraphSearchPanel.vue` (drop `enabledDocumentTypes` state and `typeFilters` in search requests)
- [x] 5.3 Remove `getAllDocumentTypes` / `DocumentType` re-export from `web-ui/src/utils/protoHelpers.ts`
- [x] 5.4 Update `DocumentTable.vue` to stop formatting/displaying a `type` column (or repoint it at the `document_type` tag if a display is still wanted)
- [x] 5.5 Update `GlobalEditorWindows.vue` to drop `type: DocumentType.NOTE` when creating new journal entries — no `document_type` tag is set by default; the field is left empty unless the user sets it
- [x] 5.6 Update `useBulkMetadataEdit.ts` to remove the `DocumentType` enum lookup for bulk type edits

## 6. Tests

- [x] 6.1 Update `python-server/tests/test_proto_converters.py`: remove/replace `document_type`-column and `DOCUMENT_TYPE_UNSPECIFIED` assertions, remove `test_row_to_proto_document_systems_populated` and `test_row_to_proto_document_systems_absent_yields_empty`
- [x] 6.2 Add/extend tests covering the repaired tag storage path (`store_document`/`update_document`/`_enrich_documents_with_junction_data` against `tag_values`), including a `document_type` tag round-trip
- [x] 6.3 Add a test confirming ingestion still derives `source_type` correctly from the PDF's declared type string (rulebook/expansion/adventure/bestiary cases), and that no `document_type` tag is set when the caller doesn't provide one
