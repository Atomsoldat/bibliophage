# Project Research Summary

**Project:** Bibliophage — Notes & Graph UX Overhaul
**Domain:** Brownfield graph-canvas UX + Python service restructuring
**Researched:** 2026-06-07
**Confidence:** HIGH

## Executive Summary

Bibliophage is an RPG rulebook RAG application that is gaining a first-class note-taking layer. The graph view (Sigma.js + Graphology + ForceAtlas2) already exists and works; this milestone enhances the UX around creating notes from the canvas, making layout stable and animated, and surfacing recently-created unconnected notes near the active node. In parallel, the Python backend undergoes a domain-based module restructuring — a pure code reorganisation with no runtime behaviour changes. No new npm or Python packages are required; all needed APIs (animateNodes, FA2Layout worker, fixed node attribute, DB transaction helpers) are already in the dependency tree.

The recommended approach has three parallel work streams: (1) constrained graph layout using ForceAtlas2's `fixed` node attribute to pin trail nodes to a deterministic left column, (2) a Fresh Notes Bubble component anchored to the pinned node's screen position via `sigma.graphToViewport()` after each render, and (3) incremental Python domain restructuring (one domain at a time, with shims and test runs between each move). The `update_document` NotImplementedError is the single critical-path blocker: it must be resolved first because every note-creation and note-editing feature depends on it.

The key risks are spatial disorientation from ForceAtlas2 resetting node positions on every reconcile, Vue reactive proxies silently breaking Sigma event wiring, and partial database writes when junction table inserts are not wrapped in a transaction. All three are well-understood and have clear mitigations: `fixed` node attributes set before each layout pass, `markRaw` on graph and Sigma instances, and `async with db.transaction()` covering all junction table mutations. The Python restructuring risk (stale singleton from split import paths) is managed by moving one domain at a time and running `just tests` after each step.

## Key Findings

### Recommended Stack

No new packages are needed. The entire feature set is deliverable with existing dependencies. Sigma 3.0.0 ships `animateNodes` at `sigma/utils/animate`; graphology-layout-forceatlas2 0.10.1 ships a WebWorker mode at `/worker`; the `fixed` node attribute is implemented in ForceAtlas2's `helpers.js` and confirmed by the maintainer. On the Python side, the restructuring is import path changes only — Pydantic Settings, psycopg3, and FastAPI patterns already support the domain package layout.

**Core technologies:**
- `sigma@3.0.0` + `graphology@0.26.0`: WebGL graph renderer + mutable graph data model — official pairing, already installed
- `graphology-layout-forceatlas2@0.10.1` `/worker` import: non-blocking layout with frame-by-frame position updates for smooth animation — already installed
- `animateNodes` from `sigma/utils/animate`: built-in position interpolation with easing — no extra install, part of the sigma package
- ForceAtlas2 `fixed` node attribute: suppresses position updates on pinned nodes while keeping repulsion active — undocumented but confirmed stable at 0.10.x
- FastAPI domain packages + `__init__.py` re-exports: domain-grouped module structure — standard FastAPI community pattern, no new dependencies

### Expected Features

**Must have (table stakes for this milestone):**
- Fix `update_document` NotImplementedError — prerequisite; nothing else ships without it
- Create note from graph canvas — the central new UX capability; right-click context menu pattern
- Constrained layout: trail pinned left, neighbourhood force-directed — prevents spatial disorientation
- Animated layout transitions — makes node repositioning legible rather than jarring
- Tag and system junction table wiring — completes the incomplete data model; enables filtering
- Fresh notes bubble (top-10 recent unconnected notes near active node) — contextual discovery
- Visual distinction between node types by color — makes graph readable with mixed rulebook/note content

**Should have (add after core note workflow is validated):**
- Search / quick-switch (Cmd+K) — essential at scale; defer until note count makes graph navigation impractical
- Tag filtering on graph — only useful once tags are actually populated via junction tables
- Inline auto-link to active node on note creation — low-complexity enhancement to canvas creation
- Local graph view with depth control — natural evolution of the neighbourhood layout already implemented

**Defer to v2+:**
- Authority-weighted node sizing — purely cosmetic; defer until core UX is stable
- RAG-context indicator on nodes — requires backend API change; high value but medium implementation cost
- System/campaign cluster grouping (convex hull) — complex visual; defer until system data is populated
- Orphan node detection panel — not needed at low note counts

**Anti-features to avoid permanently:**
- Auto-linking via NLP content analysis — creates spurious edges that pollute the graph
- Real-time collaborative editing — load-bearing single-user architectural constraint
- Block-level linking (Roam-style transclusion) — requires chunk-level identity system and a new graph layer
- Global real-time graph recompute on every edit — root cause of the "jumpy repositioning" problem

### Architecture Approach

The architecture is additive on the frontend and reorganisational on the backend. `GraphView.vue` gains constrained layout logic and a `bubblePosition` ref computed from `sigma.graphToViewport()` after each `afterRender` event. A new `FreshNotesBubble.vue` component (Teleported to body, positioned with `position: fixed`) receives `bubblePosition` as a prop and reads recent unconnected documents from the existing Pinia stores. The Python backend moves from a flat `src/*.py` layout to domain packages (`documents/`, `ingestion/`, `embeddings/`, `chat/`, `graph/`, `db/`), with `server.py` unchanged in structure and each domain's `__init__.py` re-exporting its service class for backward compatibility.

**Major components:**
1. `stores/graph.ts` (Pinia) — add `fixed` attribute assignment in `reconcile()` before ForceAtlas2 runs; store last-known positions per node ID to survive re-add cycles
2. `GraphView.vue` — reduce FA2 iterations to 50; add `afterRender` listener for bubble positioning; extend right-click context menu with "New note here" on canvas stage
3. `FreshNotesBubble.vue` (new) — floating panel (Teleport → body) anchored to pinned node's viewport coordinates; emits `@pin` and `@connect` actions back to `GraphView`
4. `documents/service.py` — implement `update_document` with full transaction wrapping of document UPDATE + junction table DELETE/INSERT; wire systems/tags junction tables here during the domain move
5. `db/postgres.py` — singleton unchanged; imported via new path `from db.postgres import get_postgres_db` once restructuring is complete

### Critical Pitfalls

1. **ForceAtlas2 resets positions on every reconcile** — set `fixed: true` on trail, pinned, and anchored nodes *before* calling `forceAtlas2.assign()`; also carry last-known x/y forward when re-adding nodes that were previously visible; never rely on FA2 to naturally cluster trail nodes to the left
2. **Vue reactive proxy breaks Sigma event wiring** — always wrap `Graph` and `Sigma` instances with `markRaw`; never store Sigma in a `ref()` or in Pinia state; the current code already does this correctly — add a comment to prevent future regression
3. **Junction table partial write** — wrap document UPDATE + junction table DELETE/INSERT in a single `async with db.transaction() as conn` block; pass `conn` directly to each statement; the pool uses `autocommit=True` so each standalone statement commits immediately without a transaction wrapper
4. **Python singleton duplication after module rename** — after each domain move, verify startup logs show singleton init exactly once; use grep to confirm no mixed old/new import paths remain before moving the next domain
5. **animateNodes import path changed in Sigma 3.x** — confirmed path is `sigma/utils/animate`; do not copy examples targeting Sigma 2.x; verify the import resolves in `node_modules/sigma/` before building the animation phase

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Backend Foundation — update_document and Domain Restructuring

**Rationale:** `update_document` is the hard blocker for all note-creation features. Python restructuring is backend-only and can proceed in parallel with frontend layout work, making this a natural first phase. Junction table wiring fits here because `documents/service.py` is the right home for it and the domain move creates the opportunity to implement it correctly with the transaction wrapper in place.

**Delivers:** Working document edit round-trip; clean domain package layout; systems and tags wired to junction tables; `update_document` implemented with transaction-safe junction table writes.

**Addresses features:** Fix `update_document`; tag/system junction table wiring.

**Avoids pitfalls:** Junction table partial write (transaction wrapper); Python import paths breaking (one domain at a time with test runs); stale singleton (verify startup log once per move); NotImplementedError opaque error (stub response before full implementation).

**Migration order within phase:** `graph/` first (smallest surface area), then `chat/`, `embeddings/`, `ingestion/`, `documents/`, `db/`; `proto_converters.py` split absolute last.

### Phase 2: Constrained Graph Layout

**Rationale:** Layout stability is a prerequisite for the Fresh Notes Bubble — the bubble's position is computed from node screen coordinates, which are meaningless if nodes are jumping to random positions after every reconcile. This phase has no backend dependencies and can begin as soon as Phase 1's `update_document` stub is in place (full implementation can follow in parallel).

**Delivers:** Trail nodes deterministically pinned to left column via `fixed: true` and explicit x-slot assignment; neighbourhood nodes force-directed around a stable pinned anchor; no abrupt repositioning on pin changes; FA2 iterations reduced to 50; last-known positions preserved across re-add cycles; node type color distinction added (same visual encoding layer, low extra effort).

**Addresses features:** Constrained layout; visual node type color distinction.

**Avoids pitfalls:** ForceAtlas2 position reset (fixed attributes set before assign); all-zero position collapse (random pre-pass guard for new nodes); layout running on every individual structural event (keep debounce, ensure fixed-attribute timing is correct).

### Phase 3: Animated Layout Transitions

**Rationale:** Depends on Phase 2 providing stable anchor positions. Animation to non-deterministic positions is pointless. Once positions are stable, `animateNodes` from `sigma/utils/animate` can interpolate from current to target positions cleanly.

**Delivers:** Smooth node position transitions on reconcile (300–500ms, cubicInOut easing); no jarring teleportation; animation paused during user drag; pin action queued until tween resolves.

**Uses stack:** `animateNodes` from `sigma/utils/animate`; ForceAtlas2 WebWorker (`FA2Layout`) as optional upgrade path if reduced-iteration sync assign still feels jumpy in practice.

**Avoids pitfalls:** Calling `reconcile()` mid-animation (hold pending-reconcile flag until `animateNodes` resolves); animation during drag (pause on `downNode` event, resume on `upNode`); Sigma instance leak (add matching cleanup for any new event listeners added in this phase).

### Phase 4: Create Note from Canvas

**Rationale:** Depends on `update_document` being fully implemented (Phase 1). Depends on stable layout (Phase 2) so the new node appears in a predictable position near the click point. The right-click context menu infrastructure already exists for nodes; this phase extends it to the canvas stage.

**Delivers:** "New note here" in right-click context menu on empty canvas area; new node appears near click coordinates; auto-pinned so editor opens immediately; optional inline auto-link to currently active node pre-populates the edge.

**Addresses features:** Create note from graph canvas; inline auto-link to active node on creation.

**Avoids pitfalls:** Double-click conflicts with existing Tab/click interactions (use right-click context menu, not double-click on stage).

### Phase 5: Fresh Notes Bubble

**Rationale:** Depends on stable layout (Phase 2) — bubble position computed from `sigma.graphToViewport()` must be predictable. Depends on note creation (Phase 4) being in place so there are fresh notes to surface. Is the most complex frontend component and should come last in the frontend sequence.

**Delivers:** `FreshNotesBubble.vue` (Teleport → body) anchored to pinned node's screen position after `afterRender`; shows top-10 recent unconnected notes; `@pin` and `@connect` actions; position computed only after `animateNodes` resolves to avoid stale coordinates.

**Addresses features:** Fresh notes bubble; bidirectional edge visibility via connect action.

**Avoids pitfalls:** Stale bubble position mid-animation (compute position only after animation resolves); `@floating-ui/dom` against a fake DOM anchor (use `sigma.graphToViewport()` directly instead); Sigma leak on unmount (add matching `sigma.off('afterRender')` in `onBeforeUnmount`).

### Phase Ordering Rationale

- `update_document` gates all note-creation and note-editing features; it is the critical path and must be unblocked in Phase 1.
- Python restructuring is backend-only with no frontend dependency; it belongs in Phase 1 alongside `update_document` because the domain move creates the right home for implementing it and the junction table wiring.
- Constrained layout (Phase 2) gates the bubble (Phase 5) via position predictability; it cannot be deferred.
- Animated transitions (Phase 3) gates nothing downstream but should precede note creation (Phase 4) so the "new node appears" experience is smooth from first use.
- Note creation (Phase 4) gates the bubble (Phase 5) because the bubble needs fresh notes to surface.
- Phases 1 and 2 can proceed in parallel: Phase 1 is backend-only, Phase 2 is frontend-only with no new backend API requirements.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 3 (Animated Transitions):** The ForceAtlas2 WebWorker path has not been prototyped in this codebase. Whether reduced-iteration sync `assign()` (50 iterations) feels acceptable in practice is a tactile judgement. Flag for a short spike at the start of Phase 3 before committing to one approach.

Phases with standard patterns (skip research-phase):

- **Phase 1 (Backend Foundation):** FastAPI domain restructuring is a well-documented pattern with high-confidence sources. `update_document` follows the existing `store_document` pattern with a transaction wrapper added. No research needed.
- **Phase 2 (Constrained Layout):** ForceAtlas2 `fixed` attribute and reduced-iteration approach confirmed against maintainer sources. Implementation is mechanical once the pattern is understood.
- **Phase 4 (Create Note from Canvas):** Right-click context menu infrastructure already exists. Pattern is extend-not-replace; no novel integration.
- **Phase 5 (Fresh Notes Bubble):** `sigma.graphToViewport()` is documented in official Sigma coordinate system docs. Component architecture is a Teleport + props pattern with confirmed integration points.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | `animateNodes` import path and ForceAtlas2 `fixed` attribute confirmed via community/maintainer sources, not formal API documentation pages; all other stack elements HIGH |
| Features | HIGH | Core graph UX patterns verified across multiple mature tools; domain fit assessed against actual codebase; feature dependencies explicitly mapped |
| Architecture | HIGH | Component boundaries verified against existing codebase; all integration points (graphToViewport, markRaw, transaction pattern) confirmed against official docs |
| Pitfalls | HIGH | Derived from direct codebase reading and official library source/changelogs; not speculative |

**Overall confidence:** HIGH

### Gaps to Address

- **`animateNodes` exact signature in Sigma 3.0.0:** Confirmed via React-Sigma wrapper docs and GitHub issues, not the sigma.js official API reference. Verify `import { animateNodes } from "sigma/utils/animate"` resolves correctly in `node_modules/sigma/` before building Phase 3. Takes 5 minutes; do it first.
- **ForceAtlas2 worker vs sync `assign()` tactile feel:** Research confirms the worker produces visible animation and sync `assign()` produces teleportation. Whether 50-iteration sync feels acceptable is a judgement call. Plan a brief evaluation moment at the start of Phase 3 before choosing the implementation path.
- **`update_document` partial-update field semantics:** Proto3 field presence semantics (optional vs required) should be verified during Phase 1 implementation to confirm the partial-update guard approach does not accidentally null out unset fields.

## Sources

### Primary (HIGH confidence)
- [graphology-layout-forceatlas2 official docs](https://graphology.github.io/standard-library/layout-forceatlas2.html) — WebWorker API, settings reference, zero-position edge case
- [sigma.js coordinate systems docs](https://www.sigmajs.org/docs/advanced/coordinate-systems/) — `graphToViewport()` / `viewportToGraph()` transforms
- [FastAPI official: Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — router splitting pattern
- [fastapi-best-practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) — domain module structure consensus
- [psycopg3 transactions docs](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) — `autocommit=True` + explicit `transaction()` pattern
- [Vue 3 reactivity docs: markRaw](https://vuejs.org/api/reactivity-advanced.html) — identity hazard with proxied third-party objects
- Codebase direct reading: `GraphView.vue`, `stores/graph.ts`, `document_service_implementation.py`, `postgres_db.py`, `proto_converters.py`, `db_schema/documents.sql`

### Secondary (MEDIUM confidence)
- [graphology discussion #375](https://github.com/graphology/graphology/discussions/375) — `fixed: true` node attribute confirmed by maintainer; implemented in `helpers.js` but not formally documented
- [sigma.js issue #1215](https://github.com/jacomyal/sigma.js/issues/1215) — `animateNodes` import path and signature for Sigma 3.x
- [React Sigma layouts docs](https://sim51.github.io/react-sigma/docs/example/layouts/) — `animateNodes` usage pattern (React wrapper but same underlying sigma API)
- [sigma.js v3 release announcement](https://www.ouestware.com/2024/03/21/sigma-js-3-0-en/) — v3 features overview; confirmed March 2024 release
- Obsidian, Logseq, Roam Research feature analysis — UX pattern derivation for graph note-taking tools

### Tertiary (LOW confidence)
- Zenkit Hypernotes / Obsidian Canvas forum threads — right-click and drag-to-create UX patterns; used for pattern validation only, not implementation details

---
*Research completed: 2026-06-07*
*Ready for roadmap: yes*
