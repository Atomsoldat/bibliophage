## Context

See proposal.md for motivation. Relevant current state:

- The tag data model (`tags` / `tag_values` / `map_documents_to_tags`) and the value-assignment code path (`postgres_db.py`'s `_apply_document_tags`, used by `store_document` and `update_document`) already work: tag values auto-create on assignment via `ON CONFLICT` upsert, and unknown tag *names* are already rejected (`ValueError`, tagged `D-06` in the code). There is simply no way to create a tag name anywhere — no proto message, no RPC, no UI.
- `UpdateDocument` is currently full-replace for the whole `Document` message, including `tags` (delete-reinsert junction rows per an earlier decision, D-01/D-08). Proto3 `repeated` fields have no presence concept — they cannot be marked `optional` — so there is no way to express "leave tags alone" within that same full-replace message shape short of introducing `google.protobuf.FieldMask` machinery.
- `ingestion/service.py`'s `LoadPdf` calls `db.store_document(systems=list(request.pdf.systems), ...)`, but `store_document`'s real signature takes `(name, content, tags, metadata)` — no `systems` parameter exists. This throws on every call and is unrelated to tags; it is a leftover from the systems/canon-removal refactor (`f091a93`, `347fefb`) that was never reconciled here, the same class of bug the archived `document-type-as-tag` change found and fixed elsewhere in this same file's neighborhood.
- `pdf.proto`'s `Pdf`/`PdfListItem` still carry `type` and `systems` fields from before that same refactor. `document.proto`'s `Metadata.publication_type` is a second, never-reconciled way of recording a document's kind, explicitly called out as a deferred non-goal in the archived `document-type-as-tag` change's design.md.
- No migration tooling exists in this project. Schema changes to date have all been made by editing the `CREATE TABLE IF NOT EXISTS` scripts in `documents.sql` in place.

## Goals / Non-Goals

**Goals:**
- Make tag names a governed, first-class resource with its own lifecycle (create/rename/delete/color), while leaving tag values exactly as open as they already are.
- Give tag assignment its own API surface, decoupled from `UpdateDocument`, so no caller needs to fetch-merge-replace a document's entire tag set to change one value.
- Retire every remaining dedicated field that duplicates what a tag already expresses (`Metadata.publication_type`, `Pdf.type`, `Pdf.systems`), consistent with the precedent already set for `document_type`.
- Fix the two standing bugs that block tags from ever reaching a document via PDF ingestion or the note editor.

**Non-Goals:**
- Merge/dedup of tags or values (see Decisions below).
- Tag-based search/filter UI (separate future change).
- Any migration of existing `publication_type` data — dropped with no backfill, per established project convention.
- Changing anything about `SourceType`/authority weighting (unrelated, already handled by `remove-source-type`).

## Decisions

### Split tag mutation out of `UpdateDocument` rather than introduce FieldMask
`UpdateDocument` stays full-replace but narrows to `name`/`content`/`metadata`. Tag mutation moves to dedicated RPCs (`AssignTagValues`/`DeleteTagValues`) that take exactly the document id(s), tag id, and value(s) they touch — no partial-update semantics to get right, because there's nothing partial about their request shape. The tag is addressed by `tag_id` rather than name, disambiguating it from the `document_ids` present in the same request (the same id-vs-name convention used across `TagService`'s other multi-id requests).

**Alternative considered**: add `google.protobuf.FieldMask` to `UpdateDocumentRequest` so a client can specify which fields to touch in one general-purpose RPC. Rejected — `tags` is a `repeated` field, and a field mask naming `"tags"` is still ambiguous about whether it means "replace the whole list" or something element-wise; a mask-aware implementation would need to reason about that ambiguity for no field other than `tags` in this message. Narrow RPCs sidestep the ambiguity entirely rather than resolving it, and directly fix a real, already-observed bug (the note editor silently wiping tags because no caller reliably resends the complete set).

### `AssignTagValue`/`RemoveTagValue` live on `DocumentService`, not `TagService`
These RPCs mutate a document's relationships, which is `DocumentService`'s existing responsibility (it already owns `store_document`/`update_document`'s tag-junction writes). `TagService` owns the existence and identity of tag names/values, not documents.

**Alternative considered**: put them on `TagService` since they depend on tag-name validity. Rejected — that dependency is just a foreign-key-style check (does this tag name exist), not a reason to relocate document-mutating operations away from the service that owns documents.

### Tag names: governance-only. Tag values: unchanged (open, auto-create on assignment)
No capability outside `tag-governance` may create a new tag name, including as a side effect of assignment — assignment against an unknown name is rejected, exactly as `_apply_document_tags` already does today. Tag values keep their existing auto-create-on-assignment behavior; `tag-governance` additionally allows creating a value explicitly, without a document, so a vocabulary can be seeded ahead of use.

**Alternative considered**: allow ad hoc tag *name* creation from assignment contexts (typing a brand-new key inline). Rejected per explicit product decision — the schema's own long-standing TODO about typo'd near-duplicate tags (`SciFi` vs `scifi` vs `Sci-Fi`) is exactly the failure mode unrestricted key creation invites; funneling name creation through one governed surface keeps the vocabulary intentional.

### No merge operation, this phase
Merging two tag values (or two tag names) means reassigning `map_documents_to_tags` rows from the retired side to the kept side. `map_documents_to_tags` has `UNIQUE NULLS NOT DISTINCT (document_id, tag_id, tag_value_id)` — if a document already carries both sides of the merge independently, a naive reassignment produces a duplicate row and the database rejects it. Resolving that requires either an auto-dedup step or a UI flow that shows the user which documents conflict and lets them choose — real design work, not a corner case to special-case away.

**Alternative considered**: ship merge with a naive reassignment that surfaces the constraint violation as a clean error instead of a raw DB exception. Rejected for this phase — explicit product decision to defer merge entirely rather than ship a version that sometimes just fails; revisit once conflict handling has its own design pass.

### Usage counts come from `ListTags`/`ListTagValues`, not a separate preview RPC
Both list calls return per-tag/per-value document (and value) counts as standard fields. The frontend's delete-confirmation prompts read counts already on screen from the list it's already rendering — no extra round trip before a destructive action.

**Alternative considered**: a dedicated `PreviewDeleteImpact` RPC called just before confirming. Rejected as unnecessary — the counts needed already exist on data the UI has already fetched to render the list the delete action was triggered from; the only cost of reusing them is that they can go slightly stale between list-fetch and delete-click, acceptable for a low-concurrency tool with no multi-user contention today.

### `canon` and `document_type` become ordinary tags with no backend special-casing
Both are plain tag names like any other, created through `tag-governance`, assigned through `tag-assignment`. `document_type` already has this treatment from the archived `document-type-as-tag` change; this change extends the same treatment to the last dedicated fields still standing (`Pdf.type`, `Pdf.systems`) and removes them, reviving "canon" as a tag name (not a first-class DB concept/table, unlike its earlier, since-removed incarnation).

### Schema and migration conventions carry over unchanged
`tags` gains a `color` column by editing `documents.sql`'s `CREATE TABLE IF NOT EXISTS` in place — same convention the last several schema changes used. No migration tooling is introduced. Removed fields (`publication_type`, `Pdf.type`, `Pdf.systems`) are dropped with no data migration, consistent with the precedent set by `document-type-as-tag` (which dropped `document_type`'s original column the same way) and `remove-source-type`.

## Risks / Trade-offs

- **[Risk] Removing `tags` from `UpdateDocument` is a breaking proto change** → Mitigation: the bundled web UI is this API's only consumer (single-consumer, pre-launch, same framing the archived changes already established); every caller is updated in this same change's frontend work.
- **[Risk] Tag/value deletion cascades broadly with no undo** → Mitigation: usage-count-driven confirmation prompts (spec'd under `tag-governance`) surface impact before the destructive call fires; soft-delete/undo is out of scope for this phase.
- **[Risk] `AssignTagValue`/`RemoveTagValue` accept multiple `document_ids` — partial-failure semantics need to be real, not aspirational** → Mitigation: spec requires all-or-nothing; implementation should wrap the batch in a single transaction, consistent with how `store_document`/`update_document` already use `self.transaction()`.
- **[Risk] Backend and frontend are implemented by different people in parallel** → Mitigation: this design and the specs are the agreed contract between them (RPC names/shapes, request/response semantics); tasks.md keeps the two tracks separated so either side can proceed once the proto surface is settled, without waiting on the other's implementation details.

## Migration Plan

1. Backend (User): proto changes (`TagService`, `DocumentService` additions, field removals on `Metadata`/`Pdf`/`PdfListItem`), regenerate bindings, schema edit (`tags.color`), implement tag governance + assignment against the DB, fix `LoadPdf`'s crash.
2. Frontend (Claude): once the proto surface exists, build `TagInput.vue`/`TagManager.vue` and wire them into the note editor, PDF upload form, and bulk-edit modal; fix the note editor's tag-loss bug as part of threading tags through its save path.
3. Rollback: revert the relevant commits. No external data dependency is introduced — no migration is performed for any removed field, matching the precedent already established by the two archived changes.
