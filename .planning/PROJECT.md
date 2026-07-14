# Bibliophage — Notes & Graph UX Overhaul

## What This Is

A quality-of-life milestone for Bibliophage's note-taking and graph exploration workflows. The project adds first-class note creation from the graph canvas, stabilizes the graph layout so users don't get disoriented, and resolves accumulated TODO debt — particularly the broken `update_document` path that prevents saving edits.

## Core Value

Users can create, edit, and connect notes fluidly inside the graph view without losing spatial context.

## Requirements

### Validated

- ✓ Document storage in PostgreSQL — existing
- ✓ Graph edges between documents (undirected/directed) — existing
- ✓ Sigma.js + Graphology graph visualization — existing
- ✓ Markdown note editor (CodeMirror 6) — existing
- ✓ Pin/anchor/trail navigation in graph — existing
- ✓ Connect mode for creating edges — existing

### Active

- [ ] Create notes directly from the graph canvas
- [ ] "Fresh notes bubble" showing recent unconnected notes near the active node
- [ ] Configurable bubble size (default: 10 most recent notes)
- [ ] Constrained graph layout: trail pinned horizontally to the left
- [ ] Gradual/animated layout transitions (no abrupt repositioning)
- [ ] Implement `update_document` (currently raises NotImplementedError)
- [ ] Wire systems/tags junction tables (store and read back)
- [ ] Python server domain-based restructuring (documents/, ingestion/, embeddings/, chat/, graph/, db/)
- [ ] Resolve remaining TODO comments across codebase

### Out of Scope

- Real-time collaborative editing — single-user tool
- Auto-linking notes to documents via content analysis — edges are manual
- Mobile/touch UI — desktop-first
- Changing the protobuf API version (staying on v1alpha3)

## Context

- This is a brownfield project; existing codebase map at `.planning/codebase/`
- `update_document` has full pseudocode in the implementation file but raises `NotImplementedError`
- Systems/tags junction tables exist in the schema but aren't read/written by `proto_converters.py`
- Graph layout currently uses ForceAtlas2 with 100 iterations on every reconcile — causes jumpy repositioning
- 24 TODOs in python-server, 13 in web-ui/src — clustered around document updates, embedding staleness, and tag filtering
- Documents table is the single source of truth for graph nodes (no separate node table)

## Constraints

- **Stack**: Python/FastAPI backend, Vue 3 + Sigma.js frontend, PostgreSQL — no new databases
- **Layout library**: Stay with Graphology + Sigma.js — constrain ForceAtlas2, don't replace it
- **Protobuf**: Generated code is committed; regenerate via `tilt trigger api` after .proto changes
- **Compatibility**: Existing documents and edges must not be affected by restructuring

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Domain-based server restructuring (not layer-based) | Related code should be co-located; navigating one feature shouldn't require jumping across 3 directories | — Pending |
| Constrained trail layout (not iterative ForceAtlas2) | Rock-solid trail stability; trail pinned to left, neighbourhood force-directed on right | — Pending |
| Fresh notes bubble positioned near active node | Keeps notes contextually close to what you're working on; selection strategy made pluggable for future changes | — Pending |
| TODO classification: "do now" (note workflow) vs "do next" (everything else) | Prioritizes unblocking the core value before general cleanup | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-07 after initialization*
