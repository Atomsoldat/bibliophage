# Stack Research

**Domain:** Graph-based knowledge tool — constrained layout animation, note-taking UX, Python domain restructuring
**Researched:** 2026-06-07
**Confidence:** MEDIUM (frontend patterns verified via official docs/changelogs; Python restructuring is well-established; some implementation details confirmed via community sources only)

---

## Recommended Stack

### Core Technologies — Already in Place (Do Not Replace)

| Technology | Version (current) | Purpose | Why |
|------------|-------------------|---------|-----|
| graphology | 0.26.0 | Graph data model | The Sigma.js official companion; provides the mutable graph object Sigma subscribes to |
| graphology-layout-forceatlas2 | 0.10.1 | Force-directed layout | Already used; has worker mode and `fixed` attribute for node pinning |
| sigma | 3.0.0 | WebGL graph renderer | Stable v3 release (March 2024); `animateNodes` is built in as `sigma/utils/animate` |
| Vue 3 + Pinia | 3.5.x / 2.3.x | UI + state | Already migrated; no change needed |
| FastAPI + psycopg3 | 0.128 / 3.2.x | Backend | Already in place |

### New Libraries Needed

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| (none — no new npm packages needed) | — | See patterns below | All required animation and layout APIs are already in graphology + sigma |

### No New Python Packages Needed

The domain restructuring is purely a code reorganisation — moving files and updating imports. No new dependencies are required.

---

## Layout Animation — API Reference

### Animating Node Transitions: `animateNodes`

**Import:** `import { animateNodes } from "sigma/utils/animate"`

**Signature:**
```typescript
animateNodes(
  graph: Graph,
  targets: { [nodeId: string]: { x: number; y: number } },
  options?: { duration?: number; easing?: string; onComplete?: () => void }
): void
```

**Easing options available in sigma v3:** `linear`, `quadraticIn`, `quadraticOut`, `quadraticInOut`, `cubicIn`, `cubicOut`, `cubicInOut`

**Confidence:** MEDIUM — confirmed via React-Sigma docs and sigma.js GitHub issues; exact import path verified via multiple community sources pointing to `sigma/utils/animate`

**Why use it:** Uses `requestAnimationFrame` internally, interpolates from current positions to target positions. Sigma re-renders each frame automatically because it listens to the graphology graph. You compute new positions, call `animateNodes`, and the canvas animates smoothly.

### Constraining Trail Nodes: ForceAtlas2 `fixed` Attribute

**API:** Set `graph.setNodeAttribute(nodeId, 'fixed', true)` before calling `forceAtlas2.assign()`.

**Behaviour:** Nodes with `fixed: true` are excluded from force calculations. Their positions are held constant while surrounding nodes settle around them. Forces from fixed nodes still affect their neighbours.

**Confidence:** MEDIUM — confirmed via graphology GitHub Discussion #375 and maintainer comment in source; the attribute is implemented in `helpers.js` but not formally documented (maintainer noted it may be renamed for harmonisation). Unlikely to break at 0.10.x; treat as stable internal API.

**Why use it:** This is the correct approach for the "trail pinned to the left" requirement. Pin trail nodes at fixed x-coordinates, mark them `fixed`, then let ForceAtlas2 settle the neighbourhood around them. No need to replace the layout algorithm.

### Worker-Based Continuous Layout

**Import:** `import FA2Layout from "graphology-layout-forceatlas2/worker"`

**API:**
```typescript
const layout = new FA2Layout(graph, {
  settings: { gravity: 1, scalingRatio: 10 }
})
layout.start()   // runs continuously in a Web Worker
layout.stop()    // pauses
layout.kill()    // releases memory
layout.isRunning(): boolean
```

**Confidence:** HIGH — fully documented in the official graphology-layout-forceatlas2 README

**Why use it for animation:** The worker runs FA2 iterations continuously and updates `x`/`y` attributes on the graphology graph. Sigma detects these changes through its graphology subscription and re-renders each frame. This produces the smooth "settling" animation the project needs on reconcile, without blocking the main thread. Start the worker on structural change, stop after positions stabilise (or after a timeout).

**Trade-off:** The synchronous `forceAtlas2.assign(graph, { iterations: 100 })` currently used is instant — it teleports nodes. The worker approach produces visible animation but requires a `start()`/`stop()` lifecycle. For the "no abrupt repositioning" requirement, the worker is the correct tool.

---

## Note-Taking UX — Patterns to Follow

No new libraries required. These are interaction patterns implemented in existing Vue components.

### Create Note from Canvas: Context Menu Pattern

**Pattern:** Extend the existing right-click context menu (already in GraphView.vue) with a "New note here" action.

**Why context menu, not double-click:** The canvas already uses click for pin and double-tab for expand. Adding double-click risks interference. Right-click is unused on the stage (currently only on nodes), and users of Obsidian, Zenkit Hypernotes, and RemNote all rely on right-click for node-creation flows.

**UX sequence:**
1. Right-click on empty canvas area → context menu appears at cursor
2. "New note here" → opens a minimal modal with a text field (name only)
3. On submit → calls `store_document` → new node appears in graph centred near click coordinates
4. The new node is auto-pinned so the editor opens immediately

**Confidence:** MEDIUM — derived from UX patterns in Zenkit Hypernotes, Obsidian Canvas, and RemNote; fits within existing connect-mode + context-menu code architecture

### "Fresh Notes Bubble": Proximity Cluster Pattern

**Pattern:** When a node is pinned, query for the N most recently created unconnected notes and assign them positions in a cluster near the pinned node, offset to a configurable region (e.g. bottom-right quadrant relative to pinned).

**Implementation approach:**
- Add a `fresh_notes` role to the existing `ROLE_PRIORITY` map (priority between `unconnected` and `neighbour`)
- Assign positions in a small circle around an offset from the pinned node before calling ForceAtlas2
- Mark these nodes as NOT `fixed` — they will drift slightly as the layout settles, which is acceptable

**Why not a separate panel:** The requirement says "near the active node", not in a sidebar list. Keeping them in the canvas maintains spatial context, which is the core value of the graph view.

---

## Python Domain Restructuring — Module Structure

### Target Structure

```
src/
  documents/
    __init__.py
    router.py          # connect-rpc service class (was document_service_implementation.py)
    repository.py      # DB queries for documents (extracted from postgres_db.py)
    converters.py      # proto <-> dict conversions for documents (from proto_converters.py)
  ingestion/
    __init__.py
    router.py          # connect-rpc service class (was loading_service_implementation.py)
    pipeline.py        # docling pipeline (was docling_pipeline.py)
    pdf_inspector.py   # (was pdf_outline_inspector.py)
  embeddings/
    __init__.py
    router.py          # connect-rpc service class (was embedding_service_implementation.py)
    chunking.py        # (was chunking_strategies.py)
    model.py           # HuggingFace embedding model wrapper (was embeddings.py)
    batch.py           # (was batch_size_calculator.py)
  chat/
    __init__.py
    router.py          # connect-rpc service class (was chat_service_implementation.py)
    llm.py             # Ollama client (was llm_access.py)
  graph/
    __init__.py
    router.py          # connect-rpc service class (was graph_service_implementation.py)
  db/
    __init__.py
    postgres.py        # connection pool + schema init (was postgres_db.py)
    schema/            # (was db_schema/)
  config.py            # unchanged
  server.py            # mounts all routers, unchanged structurally
```

**Why domain-based, not layer-based:** The codebase already has one file per service. The real problem is that related logic is split across files without a grouping mechanism. A layer-based approach (all `repositories/` in one folder, all `services/` in another) would add indirection without cohesion — you'd still need to jump between four folders to understand one feature. Domain grouping means all the code for "embeddings" lives in `embeddings/`.

**Confidence:** HIGH — this pattern is the consensus recommendation across FastAPI community guides and the fastapi-best-practices reference (zhanymkanov). It matches how the project's own KEY DECISIONS section describes the goal ("related code should be co-located").

### Migration Strategy: File-by-File, No Flag Days

1. Create the domain directories with empty `__init__.py` files.
2. Move one domain at a time (start with the smallest — `graph/`).
3. Keep the old file as a shim that re-exports from the new location (one-line `from graph.router import GraphServiceImplementation`) until all callers are updated.
4. Update imports in `server.py` after each domain is moved.
5. Run `just tests` after each domain move to confirm nothing broke.
6. Delete shim files once `server.py` imports are updated.

**Why shim-first:** The protobuf-generated code is committed and imports `*_service_implementation` by name from `server.py`. Shim files let you move incrementally without breaking the running server between commits.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `animateNodes` from `sigma/utils/animate` | Manual `requestAnimationFrame` loop modifying x/y | `animateNodes` handles easing, cancellation, and frame timing; rolling your own is error-prone and adds ~50 lines of bookkeeping |
| ForceAtlas2 worker (`/worker` import) for animated settling | Running more sync iterations (200+) | Sync `assign()` always teleports nodes — no amount of iterations produces visible animation; the worker is the only way to get frame-by-frame rendering |
| `fixed` node attribute on FA2 | Switching to `graphology-layout-force` with `isNodeFixed` | FA2 is already in use and produces better results for organic layouts; `graphology-layout-force` is simpler but has lower visual quality |
| Domain-based module grouping | Layer-based grouping (routers/, services/, repos/) | Layer-based adds jumping across directories for a single feature change; inappropriate for a project with 5 tightly coupled domains |
| Domain-based module grouping | Full DDD with aggregates, value objects, bounded contexts | Overkill for a single-user CRUD+RAG tool; adds ceremony without payoff |
| Right-click context menu for "create note" | Double-click on canvas stage | Double-click conflicts with existing Tab/click interactions; context menu is already implemented for nodes |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `d3-force` or `vis.js` for layout | Would require replacing the entire graph rendering stack; incompatible with the Graphology event model Sigma depends on | ForceAtlas2 worker — already in the dependency tree |
| Cytoscape.js | Entirely different graph library with different data model; would invalidate all existing graph store code | Sigma.js + Graphology — already integrated |
| Replacing ForceAtlas2 with a hierarchical layout (dagre, ELK) | Changes the visual language of the app; users expect organic layout for knowledge graphs | Constrained ForceAtlas2 with `fixed` on trail nodes |
| `graphology-layout-noverlap` as primary layout | Anti-collision only — does not produce meaningful semantic clustering; meant to be run after a force layout | Use after ForceAtlas2 settles if node overlap is a problem (optional pass) |
| Full DDD layers (domain/application/infrastructure/presentation) in Python | The project has 5 service classes and one DB module; introducing 4 abstraction layers adds ~40 empty files and no real boundary value | Flat domain folders with router + repository + converters per domain |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| sigma@3.0.0 | graphology@0.26.0 | Official pairing; sigma v3 was released alongside graphology 0.26 |
| graphology-layout-forceatlas2@0.10.1 | graphology@0.26.0 | Same mono-repo; versions are coordinated |
| sigma@3.0.0 | `animateNodes` from `sigma/utils/animate` | `animateNodes` is part of the sigma package itself — no extra install |

---

## Installation

No new packages required. All needed APIs are already installed:

```bash
# Already available in web-ui — no changes
# sigma@3.0.0 includes sigma/utils/animate
# graphology-layout-forceatlas2@0.10.1 includes /worker sub-import

# Verify the worker import resolves:
# import FA2Layout from 'graphology-layout-forceatlas2/worker'
# import { animateNodes } from 'sigma/utils/animate'
```

For Python:

```bash
# No new dependencies — restructuring is import path changes only
# Confirm after restructuring:
cd python-server && just tests
```

---

## Sources

- [graphology-layout-forceatlas2 official docs](https://graphology.github.io/standard-library/layout-forceatlas2.html) — worker API, settings reference (HIGH confidence)
- [Fixed/Pinned nodes discussion #375](https://github.com/graphology/graphology/discussions/375) — `fixed` node attribute confirmed by maintainer (MEDIUM confidence — undocumented but implemented)
- [sigma.js v3 release announcement](https://www.ouestware.com/2024/03/21/sigma-js-3-0-en/) — v3 release date March 2024, features overview (HIGH confidence)
- [sigma.js CHANGELOG](https://github.com/jacomyal/sigma.js/blob/main/CHANGELOG.md) — animateNodes history (MEDIUM confidence)
- [animateNodes issue #1215](https://github.com/jacomyal/sigma.js/issues/1215) — animateNodes improvements in v3 (MEDIUM confidence)
- [React Sigma layouts docs](https://sim51.github.io/react-sigma/docs/example/layouts/) — animateNodes usage pattern (MEDIUM confidence — React wrapper but same underlying API)
- [fastapi-best-practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) — domain module structure (HIGH confidence — widely cited reference)
- [FastAPI official: Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — router splitting pattern (HIGH confidence)
- Zenkit Hypernotes help docs — right-click / drag-to-create UX patterns (MEDIUM confidence)
- Obsidian Canvas keyboard shortcut forum threads — canvas note creation UX research (MEDIUM confidence)

---

*Stack research for: Bibliophage Notes & Graph UX Overhaul milestone*
*Researched: 2026-06-07*
