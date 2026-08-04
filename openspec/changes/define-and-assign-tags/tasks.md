## 1. Backend (Leon) — Proto surface

- [x] 1.1 Define a `TagService` proto covering:
[x] create tag (name, optional color), 
[x] delete tag,
[x] create tag value (tag name, value),
[x] delete tag value
[x] rename tag,
[x] rename tag value,
[x] update tag color,
[x] list tags (name filter; returns name, color, value_count, document_count),
[x] a tag's values are read via `GetTags`/`GetTag`'s returned `Tag.values` (no separate list-values RPC; `ListAllTagValues` was removed),
. No merge RPCs — see design.md's Decisions.

- [x] 1.2 Add `AssignTagValues`/`DeleteTagValues` RPCs to `DocumentService`. Both take one or more document ids and a tag id; `AssignTagValues` also takes value(s) (auto-creates any unseen under an existing tag), `DeleteTagValues`'s value(s) are optional (omitted removes the whole tag from those documents). Both reject an unknown tag id and apply atomically across all given document ids.
- [x] 1.3 Narrow `UpdateDocumentRequest`/`UpdateDocument` so `tags` is no longer read or written by this RPC. `Document`/`DocumentListItem` keep `tags` as a read-only field for `GetDocument`/`SearchDocuments`.
- [x] 1.4 Remove `Metadata.publication_type` from `document.proto`.
- [x] 1.5 Remove `type` and `systems` from `Pdf`/`PdfListItem` in `pdf.proto`.
- [x] 1.6 Regenerate Python + TS bindings for all of the above.

## 2. Backend (Leon) — Schema & data layer

- [x] 2.1 Add a `colour` column to `tags` in `documents.sql` (edit the `CREATE TABLE IF NOT EXISTS` in place, per existing project convention).
- [ ] 2.2 Implement the tag governance surface (1.1) against `tags`/`tag_values`: cascading delete, usage-count queries for list responses, and rename/create collisions surfaced as clean errors rather than raw DB exceptions.
- [ ] 2.3 Implement `AssignTagValue`/`RemoveTagValue` (1.2), reusing/adapting the existing value-upsert logic in `_apply_document_tags`; wrap multi-document requests in a single transaction for all-or-nothing semantics.
- [ ] 2.4 Remove tag handling from `update_document`'s write path; keep it in `store_document` and in the read-side enrichment (`get_document_by_id`, `search_documents`).

## 3. Backend (Leon) — Ingestion fix

- [x] 3.1 Fix `ingestion/service.py`'s `load_pdf`: stop passing the nonexistent `systems` keyword to `store_document`; pass `request.pdf.tags` straight through as the document's tags, with no type/system inference.
- [x] 3.2 Remove the now-dead `systems`/`type` validation and metadata-building code in `load_pdf` that referenced the removed proto fields.

## 4. Frontend (Claude) — Shared tag infrastructure

- [x] 4.1 Add `composables/useTagApi.ts` (mirrors `useDocumentApi.ts`), wrapping the `TagService` client: list tags, list tag values, create/rename/delete tag, create/rename/delete tag value, update tag color.
- [x] 4.2 Add `assignTagValue`/`removeTagValue` methods to `useDocumentApi.ts`.
- [x] 4.3 Add `stores/tags.ts` (Pinia setup store, mirrors `stores/documents.ts`): caches known tag names/values, exposes search-filtered lookups for autocomplete, and invalidates/reloads so governance edits (create/rename/delete) are reflected in every open `TagInput`/`TagManager` instance.

## 5. Frontend (Claude) — `TagInput.vue`

- [x] 5.1 Build the two-level typeahead: lock a tag key from `stores/tags.ts` (existing tags only, no free text accepted as a key), then autocomplete or free-type a value under the locked key.
- [x] 5.2 When a typed key has no matches, show a "no tag called '…' — manage tags" affordance instead of a dropdown.
- [x] 5.3 Add a "manage tags" button next to the input that opens `TagManager.vue` in an overlay (6.3), pre-filled with the typed name if opened via the no-match affordance.
- [x] 5.4 Support two usage modes: "assign" (calls `assignTagValue`/`removeTagValue` directly per chip added/removed, for an already-existing document) and "collect" (exposes selected tags as plain data to a parent, for forms like PDF upload that submit everything together).

## 6. Frontend (Claude) — `TagManager.vue` and its two mount points

- [x] 6.1 Build `TagManager.vue`: browse/search tags and values (with usage counts), create/rename/delete tag, create/rename/delete value, set tag color. Delete actions show a confirmation using the usage counts already fetched ("this affects N documents" / "this deletes M values across N documents") — no extra request. Per-value rename/delete required adding an `id` field to `TagValue` (tag.proto) — done during this session with the user, bindings regenerated.
- [x] 6.2 Add a `/tags` route (`router/index.ts`) mounting `TagManager.vue` in a page shell. Also added a Sidebar nav entry for discoverability.
- [x] 6.3 Add an overlay (drawer or modal) wrapper for `TagManager.vue`, usable from the "manage tags" button (5.3) without navigating away from the view it was opened from.

## 7. Frontend (Claude) — Note editor

- [x] 7.1 Add a `tags` field to `EditorWindowConfig` (`stores/editorWindows.ts`), following the existing `documentId`/`title`/`content`/`isNew` partial-update pattern.
- [x] 7.2 Add a `tags` `defineModel` to `TextEditorCard.vue` (same pattern as its existing models) and render `TagInput` in "assign" mode, bound to the open document's id once it has one.
- [x] 7.3 `Library.vue`'s `handleEditDocument`: pass the already-fetched `response.document.tags` into `openWindow(...)` (currently fetched and discarded).
- [x] 7.4 Wire `TagInput`'s add/remove actions to fire immediately, independent of the content "Save" button. Update `GlobalEditorWindows.vue: handleSave` to stop sending `tags` through `storeDocument`/`updateDocument` (both now scoped to name/content/metadata per 1.3) — `updateDocument` already didn't send tags; nothing further needed there.

## 8. Frontend (Claude) — PDF upload

- [x] 8.1 Remove `PdfUpload.vue`'s dangling `rpgSystem` reference and the "RPG System" and "Publication Type" `FormSelect`s.
- [x] 8.2 Add `TagInput` (in "collect" mode) to `PdfUpload.vue`, letting the user assign `canon`, `document_type`, and any other tags before submitting; populate `LoadPdfRequest.pdf.tags` from it on submit.

## 9. Frontend (Claude) — Bulk metadata edit

- [x] 9.1 Replace `MetadataEditModal.vue`'s free-text tag input with `TagInput`. Split into two `TagInput`s (tags to add / tags to remove) since the new assign/remove RPCs are incremental, not full-replace; dropped the dead `Type` field (`Metadata.publication_type` no longer exists) and the now-unused `initialDocument` prop/computed.
- [x] 9.2 Rework `useBulkMetadataEdit.ts` to call `assignTagValue`/`removeTagValue` with the full array of selected document ids in one call per tag/value change, replacing the current per-document fetch/replace/write-back loop.
