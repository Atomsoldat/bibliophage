## Why

The tag system's data model and value-assignment plumbing already work, but there is no way anywhere in bibliophage — no proto message, no RPC, no UI — to define a new tag name. The two places tags most need to attach, PDF ingestion and note-taking, are currently broken or incomplete for unrelated reasons on top of that. Nothing else on the tag roadmap (search/filter by tag) is buildable until documents can actually be tagged end-to-end.

## What Changes

- Add tag governance: create, rename, delete, and (optionally) color tag names and their values, from a dedicated management surface reachable both as a standalone view and as an in-context overlay next to every place tags are assigned, so defining a missing tag never means abandoning what you were doing.
- Add a dedicated tag-assignment API (`AssignTagValue`/`RemoveTagValue`) that mutates a document's tags directly and atomically, across one or more documents at once, replacing the previous fetch-whole-document/replace-all-tags/write-back pattern.
- **BREAKING**: `UpdateDocument` no longer accepts or mutates `tags` — it is scoped to `name`/`content`/`metadata` only. Callers change tags via the new assignment RPCs.
- **BREAKING**: Remove `Metadata.publication_type` — superseded by the existing `document_type` tag.
- **BREAKING**: Remove `Pdf`/`PdfListItem`'s `type` and `systems` fields — superseded by the `document_type` tag and an ordinary `canon` tag respectively. No dedicated proto field for either going forward.
- Fix `LoadPdf`: it currently calls a nonexistent `store_document(systems=...)` keyword argument, so every PDF upload throws before anything else happens. Pass the request's tags straight through instead, with no type/system inference.
- Fix the floating note editor silently wiping a document's tags on every content save — tags were fetched on open but never threaded through the edit/save pipeline.
- Web UI: a reusable tag-entry input (autocompletes tag keys from existing tags only; autocompletes or creates tag values ad hoc) used in the note editor, the PDF upload form, and the bulk metadata-edit modal; a tag management view usable standalone and as an overlay.

## Capabilities

### New Capabilities
- `tag-governance`: creating, renaming, deleting, and coloring tag names and their values; listing tags and values with usage counts for autocomplete and for informed deletion.
- `tag-assignment`: assigning and removing tag values on one or more documents directly, independent of document content/metadata updates; the exclusive mechanism by which any open-ended document facet (RPG-system/canon affiliation, publication kind, genre, etc.) attaches to a document going forward — no per-facet dedicated proto fields.

### Modified Capabilities
- `document-classification`: extends the existing "no dedicated type field, use a tag instead" requirement to also cover `Metadata.publication_type` and `Pdf`/`PdfListItem.type`, both retired in favor of the `document_type` tag.

## Impact

- **Proto**: `document.proto` (`Metadata` loses `publication_type`; `UpdateDocumentRequest`/`Document` semantics around `tags` narrow as described above), `pdf.proto` (`Pdf`/`PdfListItem` lose `type` and `systems`), a new `TagService` proto surface, new `DocumentService` RPCs for tag assignment.
- **Backend**: new tag CRUD service/DB layer; `documents/service.py` gains tag-assignment handling and loses tag handling from `update_document`; `ingestion/service.py`'s `load_pdf` fixed to stop crashing and to pass tags through; `db/schema/documents.sql` gains a `color` column on `tags`.
- **Frontend**: new `TagInput.vue`, `TagManager.vue`, a `/tags` route, `stores/tags.ts`, `composables/useTagApi.ts`; changes to `PdfUpload.vue`, `MetadataEditModal.vue`, `useBulkMetadataEdit.ts`, `TextEditorCard.vue`, `TextEditorWindow.vue`, `GlobalEditorWindows.vue`, `stores/editorWindows.ts`, and `Library.vue`.
