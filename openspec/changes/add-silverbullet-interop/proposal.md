## Why

Bibliophage's own web-ui is currently the only way to read and edit a document's content. SilverBullet is a more capable, already-preferred markdown editor; presenting bibliophage as a SilverBullet-compatible space lets documents be authored there while still feeding bibliophage's tag, embedding, and graph pipeline — without duplicating storage and without requiring any changes to SilverBullet itself.

## What Changes

- New HTTP shim implementing SilverBullet's `/.fs` `SpacePrimitives` contract (list/get-meta/read/write/delete), backed by Postgres documents instead of disk.
- A document's SilverBullet page path is *derived*, not stored: from a new `sb_directory` column plus the document's `name`, re-derived on every read. `sb_directory` is a plain, user-filed folder location — decoupled from `document_type` and every tag, defaulting to `bpgInbox` until a user moves a page elsewhere in SilverBullet. `(sb_directory, title)` is enforced UNIQUE in the database, which is what makes wikilink resolution on write unambiguous; the rare same-directory name collision (only possible via bibliophage's own non-SilverBullet document creation, never via SilverBullet itself) is resolved with an adaptively-lengthened suffix taken from the tail of the document's UUIDv7 id.
- YAML frontmatter is server-generated fresh on every read and never persisted verbatim — most fields (`bpg_id` and the new `bpg_modified` below) are read-only and never accepted from a write. `tags` is the one exception: on write, it's validated against bibliophage's governed tag names (unknown name rejects the write; unknown value auto-creates) and reconciled by diffing against the document's currently-assigned tags — never freeform, never bypassing `TagService`-governed tag names. `document_type` is just another tag under this mechanism; it carries no special path/folder role.
- A reserved `bpg_modified` field (the document's `updated_at`, round-tripped the same way as `bpg_id`) guards both the tag reconciliation and the content write against lost updates — a `PUT` whose `bpg_modified` doesn't match the document's current state is rejected outright rather than silently applied against stale data.
- A SilverBullet-side lint check flags unknown tag names inline, before save, as a non-blocking complement to the write-time validation above.
- Document body round-trips through a canonical, UUID-based placeholder representation for cross-document links, instead of literal path text. Both `[[wikilink]]` and `[text](relative/path)` syntax are accepted as write-time input (classified the same way SilverBullet's own relation index already does — external URLs are left untouched); output always normalizes to `[[target|text]]`, since wikilinks get materially richer treatment in SilverBullet's own client (missing-link styling, click-to-create-stub, page decorations) that markdown-links don't. A document's derived path can change freely without any link anywhere ever needing to be rewritten.
- `[[wikilink]]`s and `[text](path)`-style links typed inside a document body both become a source of graph edges, alongside (future) user-authored, LLM-determined, vector-similarity, and keyword-derived edges — each edge records which of these produced it.
- Moving a document via SilverBullet's own "Rename Page" updates its `name` and/or `sb_directory` immediately and unambiguously — both are single-valued, so there's no ambiguity to resolve the way there would be for a multi-valued tag. A `[[wikilink]]` that doesn't resolve to any existing document creates one immediately, tagged `document_type: stub` and filed under the default `sb_directory = bpgInbox`; "promoting" it later is an ordinary tag edit through the frontmatter mechanism, not a move.
- **BREAKING (against an existing spec)**: `document-classification`'s current allowance for a document to have no `document_type` tag is reversed — every document always has one, assigned automatically (an avenue-of-ingress-appropriate guess where one reasonably exists, `"generic"` otherwise) when not set explicitly. `document_type` also changes from single-valued to multi-valued — documents can genuinely belong to more than one type at once. PDF ingestion's prior "never infer a type" restriction is lifted accordingly.

## Capabilities

### New Capabilities
- `silverbullet-space`: exposes bibliophage documents as a SilverBullet-compatible space — path derivation, server-generated frontmatter (read-only for identity/versioning fields, validated-and-reconciled bidirectionally for `tags`), and the `/.fs` protocol surface.
- `markdown-link-graph-sync`: extracts graph edges from `[[wikilink]]` and `[text](path)`-style markdown links found in document bodies, keeps them consistent with content via the placeholder scheme, and reconciles/garbage-collects them.

### Modified Capabilities
- `document-classification`: `document_type` changes from optional and single-valued (absent tag = untyped; PDF ingestion never infers it) to mandatory, multi-valued, and inferrable from avenue of ingress (falling back to `"generic"`). The prior "no tag" allowance was a migration-era artifact of the `publication_type`/`Pdf.type`-to-tag transition and is retired now that the migration is complete.

## Impact

- New: a shim HTTP surface in `python-server` (new handlers; does not modify `DocumentService`/`TagService`'s existing gRPC contracts).
- `documents.sql`: new `sb_directory TEXT NOT NULL DEFAULT 'bpgInbox'` column plus a `UNIQUE (sb_directory, title)` constraint.
- `graph.proto`: `Edge` gains a provenance/source field.
- `document-classification` spec: requirement change as above, plus a corresponding default-assignment change in the document write path (`store_document`) so `document_type` is always populated.
- No changes to `web-ui` planned by this change.
- External dependency: none — the shim only implements SilverBullet's already-documented HTTP contract; no SilverBullet source is modified.
- Depends on `AssignTagValues`/`DeleteTagValues` also bumping `documents.updated_at` on tag mutation — required for this change's write-conflict guard to be correct; not implemented by this change.
