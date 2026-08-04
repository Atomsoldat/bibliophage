## Context

See proposal.md for motivation. Relevant current state (as it exists once `document-type-as-tag` has landed):

- `SourceType` and its authority weighting are deeply wired into the chat path: `chat/llm_access.py` has `AUTHORITY_WEIGHTS`/`AUTHORITY_LABELS` dicts, `DocumentContext.authority_weight`/`source_type`, `_build_context_prompt` sorts documents by authority and labels each one (`--- Source: {name} ({label}) ---`) in the actual text sent to the LLM, and the default system prompt for `generate_content` explicitly instructs the model to "Prioritise information from Official Rules sources". `chat/service.py` and `chat.proto`'s `ContextDocumentInfo.authority` surface the computed weight to API clients.
- `ingestion/service.py` contains an if/elif block that maps the uploaded PDF's declared type string to a `source_type` (CORE for "rulebook"/"core", SUPPLEMENT for "supplement"/"expansion"/"adventure"/"bestiary"/"monster", CORE as fallback). After `document-type-as-tag`, this block's `doc_type` branch is already gone — only the `source_type` assignment remains per branch.
- Several test files construct documents with a hardcoded `source_type` (`GM_NOTES`): `conftest.py`, `test_document.py`, `test_graph_db.py`, `test_graph_service.py`. `test_proto_converters.py` also asserts on `source_type`/`SourceType` conversions directly.
- No migration tooling exists in this project; schema changes are made by editing the `CREATE TABLE IF NOT EXISTS` scripts in place (see `document-type-as-tag`'s design.md for the same observation).
- Unlike `document_type`, `source_type` has no generic-tag replacement — the tag system isn't involved in this change at all. This change only removes; it introduces nothing.

## Goals / Non-Goals

**Goals:**
- Remove `source_type`/authority weighting end-to-end: proto (`document.proto`, `chat.proto`), DB, ingestion, `chat/llm_access.py`, `chat/service.py`, UI. All documents are equal inputs to LLM context — no field, sort order, or prompt label distinguishes them by authority.

**Non-Goals:**
- Do not design what a future authority/trust system looks like. This change only removes the current one; how (or whether) authority weighting comes back later is explicitly out of scope, per the user's own framing ("when it is actually needed").
- Do not replace authority-based context sorting with some other sort order (e.g. recency, alphabetical). Context documents are presented in whatever order they're supplied/retrieved in — no new ordering scheme is introduced.
- Do not touch `document_type`, tags, or the tag storage path — handled entirely by the prerequisite `document-type-as-tag` change.
- Do not introduce a migration framework. Schema edits follow existing project convention (edit the `CREATE TABLE` script in place).

## Decisions

### Sequence after `document-type-as-tag`
This change assumes `document-type-as-tag` has already been applied. Reason: both changes touch `ingestion/service.py`'s classification if/elif and `chat/llm_access.py`'s `DocumentContext`. Doing `document_type` first means this change only has to deal with `source_type`'s half of each, rather than two changes racing to edit the same lines. If `document-type-as-tag` hasn't landed yet when this change is implemented, do that one first.

### Delete the remaining ingestion classification block outright, don't leave a partial inference
Once `document_type` inference is already gone (prior change), the if/elif in `ingestion/service.py` only computes `source_type`. This change deletes the whole block rather than leaving a vestigial single-purpose classifier — there's no `document_type` sibling to justify keeping the branching structure around, and the string-matching logic has no purpose once nothing reads its output. `request.pdf.type` itself is untouched where it's used for `Metadata.publication_type` (out of scope).

### Remove authority weighting from context assembly rather than hardcode a neutral weight
Rather than keep `AUTHORITY_WEIGHTS`/sorting/labeling machinery and just make every source type map to the same weight, the mechanism itself is deleted: `_build_context_prompt` drops its `sort_by_authority` parameter and sorting step entirely (documents are formatted in whatever order the caller passes them), and the per-document label changes from `--- Source: {name} ({authority_label}) ---` to `--- Source: {name} ---`. `AUTHORITY_WEIGHTS`, `AUTHORITY_LABELS`, `DocumentContext.authority_weight`, `DocumentContext.source_type`, and `_get_authority_label` are all deleted rather than left as unused dead code. The default system prompt in `generate_content` drops its "Prioritise information from Official Rules sources over other sources" line, since there's no longer any label in the context for the model to key off of. `ContextDocumentInfo.authority` is removed from `chat.proto` and its construction site in `chat/service.py`'s `_build_metadata_chunk`; `query_with_context`'s returned metadata drops the `"authority": doc.authority_weight` entry.

**Alternative considered**: keep the fields/plumbing in place but hardcode a single neutral weight (e.g. always `1.0`) so "authority" still exists as a concept but has no effect. Rejected — that's dead weight with extra steps; deleting the mechanism is more honest about the current state and is easier to reintroduce cleanly later (per the user's "put it back when needed" framing) than to unwind a fake-neutral shim.

### No data migration for existing `source_type` column values
Same reasoning as `document_type` in the prerequisite change: no migration tooling exists, schema changes are edit-in-place by convention, and no environment currently has data worth preserving.

## Risks / Trade-offs

- **[Risk] Removing authority weighting changes actual LLM output** — today, "Official Rules" content is deliberately boosted (weight 1.0-1.2) and generated/community content down-weighted (0.3-0.4); after this change, a low-quality or GM-scratch-note document has exactly as much influence on generated content as an official rulebook. This is a real behavior change users may notice, not just internal bookkeeping → Mitigation: this is the explicit intent of the change ("treat all documents the same... put that back when actually needed"), not an accidental side effect — flagged here so it's a known, deliberate trade-off rather than a surprise.
- **[Risk] Removing `ContextDocumentInfo.authority` from `chat.proto` is a breaking wire-format change** for any client reading chat streaming metadata → Mitigation: the only consumer is the bundled web UI, updated in the same change (this project doesn't maintain external API consumers across versions yet).
- **[Risk] Dropping `source_type` without migration loses existing classification data on any environment with real data** → Mitigation: same call already made and confirmed for `document_type`; no migration tooling exists to do otherwise without introducing new machinery.

## Migration Plan

1. Update proto (`document.proto`: drop `SourceType`, `.source_type`; `chat.proto`: drop `ContextDocumentInfo.authority`), regenerate Python + TS bindings.
2. Update `documents.sql` (drop `source_type` column).
3. Update `store_document` / `update_document` in `postgres_db.py` to drop the `source_type` parameter/column reference; update `row_to_proto_document` in `proto_converters.py` to drop the `source_type` conversion.
4. Update `ingestion/service.py` to delete the remaining PDF-type classification if/elif block entirely; stop passing `source_type` to `store_document`.
5. Update `chat/llm_access.py` (drop `AUTHORITY_WEIGHTS`, `AUTHORITY_LABELS`, `DocumentContext.source_type`/`.authority_weight`, `_get_authority_label`, authority sorting/labeling in `_build_context_prompt`, the "Prioritise Official Rules" prompt line) and `chat/service.py` (`_fetch_context_documents`, `_build_metadata_chunk`, `query_with_context` metadata).
6. Update `documents/service.py` to drop `SourceType` enum conversions.
7. Update web UI: `GlobalEditorWindows.vue` (drop `SourceType.GM_NOTES` default).
8. Update tests: `test_proto_converters.py`, `test_document.py`, `test_graph_db.py`, `test_graph_service.py`, `conftest.py`.
Rollback: revert the commit(s); no external data dependency is introduced since no migration is performed.
