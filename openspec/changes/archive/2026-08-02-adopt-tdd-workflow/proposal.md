## Why

Bibliophage development so far has produced code with no accompanying tests written alongside it, which has let bugs ship silently (e.g. `LoadPdf` calling `db.store_document(systems=...)` against a method whose signature no longer has a `systems` param, or `UpdateDocument` silently wiping a document's tags on every content edit — both found only by manual code reading, not by any test). Establishing red/green test-driven development as the required workflow for new work catches these classes of bugs at write-time instead of leaving them for someone to stumble on later.

## What Changes

- Document red/green TDD as the required workflow for new development across the project: write a failing test first (red), then write the minimum implementation to make it pass (green), then refactor with tests green throughout.
- Encode this in `openspec/config.yaml`'s `context`, `rules`, and `operations.apply.guidance` fields rather than in an assistant-specific file like `CLAUDE.md`. `openspec instructions`/`openspec context` surface these to whichever LLM or human is driving a change, so the workflow travels with the OpenSpec tooling itself instead of depending on one assistant's config convention.
- Scope: applies to new feature work and bug fixes going forward. Not retroactive — existing untested code is not required to gain tests as a side effect of this change.
- No enforcement tooling (no pre-commit hook, no CI gate) is introduced by this change — it establishes the guideline via OpenSpec's own config and instruction pipeline, advisory rather than mechanically enforced.

## Capabilities

This is a process/config change with no system-level behavior change, so no capability specs apply.

## Impact

- Modified file: `openspec/config.yaml` — populates `context` (red/green TDD as project convention), `rules.tasks` (pair each implementation task with a preceding test-writing task), and `operations.apply.guidance` (red/green/refactor sequence to follow during `openspec apply`/implementation).
- No code, API, or dependency changes. No new `CLAUDE.md`.
