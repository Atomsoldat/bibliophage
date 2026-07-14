# Architecture Research

**Domain:** Brownfield graph-canvas UX + Python service restructuring
**Researched:** 2026-06-07
**Confidence:** HIGH (all three areas verified against library source and existing codebase)

---

## Standard Architecture

### System Overview (after this milestone)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         GraphView.vue (Vue 3)                            │
│                                                                          │
│  ┌─────────────────────────────────────┐  ┌──────────────────────────┐  │
│  │  Trail panel (left sidebar strip)   │  │  Sigma canvas (right)    │  │
│  │  Fixed x-positions via fixed attr   │  │  Force-directed interior │  │
│  └─────────────────────────────────────┘  └──────────┬───────────────┘  │
│                                                       │ sigma.afterRender│
│  ┌────────────────────────────────────────────────────▼───────────────┐  │
│  │       FreshNotesBubble.vue (Teleport → body, absolute/fixed)       │  │
│  │       position = sigma.graphToViewport(pinnedNode) + offset        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                          │ Pinia stores/graph.ts
         ┌────────────────┼────────────────────────┐
         │                │                        │
┌────────▼──────┐ ┌───────▼──────┐ ┌──────────────▼──────────────────────┐
│ useGraphApi   │ │ useDocument  │ │  stores/graph.ts (Pinia)             │
│ composable    │ │ Api           │ │  reconcile() · pinNode() · trail     │
└────────┬──────┘ └───────┬──────┘ │  neighbourCache · anchoredNodeIds    │
         │                │        └─────────────────────────────────────-┘
         └────────────────┘
                 │ Connect RPC / HTTP
┌────────────────▼──────────────────────────────────────────────────────┐
│                  python-server/src/  (domain packages)                 │
│                                                                        │
│  documents/          ingestion/        embeddings/                     │
│  ├── service.py      ├── service.py    └── service.py                  │
│  ├── converters.py   ├── pipeline.py                                   │
│  └── queries.py      └── outline.py   chat/                            │
│                                       └── service.py                  │
│  graph/              db/              (server.py stays at root)        │
│  └── service.py      ├── postgres.py                                   │
│                      └── schema/                                       │
└────────────────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────────────────────┐
│              PostgreSQL (pgvector + graph_edges)                        │
│  documents · document_chunks · graph_edges · systems · tags             │
└────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `GraphView.vue` | Sigma lifecycle, keyboard/mouse events, layout scheduling | `stores/graph.ts`, `FreshNotesBubble.vue` |
| `stores/graph.ts` (Pinia) | Role-priority reconcile, neighbourhood cache, trail/anchor/pin state | `useGraphApi`, `useDocumentApi` |
| `FreshNotesBubble.vue` | Floating panel listing recent unconnected notes near active node | `stores/graph.ts`, `stores/documents.ts`, `useGraphApi` |
| `useGraphApi` composable | Connect RPC calls: getNeighbours, createEdge, deleteEdge | Python GraphService |
| `documents/service.py` | Document CRUD, `update_document` (now implemented) | `db/postgres.py`, `documents/converters.py` |
| `ingestion/service.py` | PDF upload via Docling pipeline | `db/postgres.py`, `ingestion/pipeline.py` |
| `embeddings/service.py` | Chunk generation + pgvector storage | `db/postgres.py`, model singleton |
| `chat/service.py` | RAG orchestration, streaming LLM responses | `db/postgres.py`, Ollama |
| `graph/service.py` | Neighbourhood queries, edge CRUD | `db/postgres.py` |
| `db/postgres.py` | PostgreSQL/pgvector singleton client | PostgreSQL |

---

## Recommended Project Structure

### Frontend — no structural change needed

The existing structure (`views/`, `stores/`, `components/`, `composables/`) is correct. New work is additive:

```
web-ui/src/
├── stores/
│   └── graph.ts            # Add: freshNotes state, layout region constants
├── components/
│   └── FreshNotesBubble.vue   # NEW: floating notes panel
├── views/
│   └── GraphView.vue       # Modify: constrained layout, bubble integration
└── composables/
    └── useGraphApi.ts      # No change needed
```

### Python Backend — domain package restructuring

Move from flat files to domain packages. `server.py` stays at the root and imports stay
backward-compatible through `__init__.py` re-exports.

```
python-server/src/
├── server.py                   # Unchanged — imports from domain packages
├── config.py                   # Unchanged
├── documents/
│   ├── __init__.py             # re-export DocumentServiceImplementation
│   ├── service.py              # was document_service_implementation.py
│   ├── converters.py           # was proto_converters.py (document-specific parts)
│   └── queries.py              # SQL helpers for document CRUD
├── ingestion/
│   ├── __init__.py
│   ├── service.py              # was loading_service_implementation.py
│   ├── pipeline.py             # was docling_pipeline.py
│   └── outline.py              # was pdf_outline_inspector.py
├── embeddings/
│   ├── __init__.py
│   ├── service.py              # was embedding_service_implementation.py
│   ├── chunking.py             # was chunking_strategies.py
│   ├── batch.py                # was batch_size_calculator.py
│   └── model.py                # was embeddings.py (singleton)
├── chat/
│   ├── __init__.py
│   └── service.py              # was chat_service_implementation.py
├── graph/
│   ├── __init__.py
│   └── service.py              # was graph_service_implementation.py
├── db/
│   ├── __init__.py
│   ├── postgres.py             # was postgres_db.py
│   └── schema/                 # was db_schema/ (rename only)
├── llm/
│   ├── __init__.py
│   └── client.py               # was llm_access.py
└── bibliophage/                # Generated protobuf — do not touch
```

**Backward-compatibility pattern for each domain `__init__.py`:**

```python
# documents/__init__.py
from documents.service import DocumentServiceImplementation

__all__ = ["DocumentServiceImplementation"]
```

`server.py` import line changes from:
```python
from document_service_implementation import DocumentServiceImplementation
```
to:
```python
from documents import DocumentServiceImplementation
```

All other cross-module imports update similarly. Tests update their imports once; no
internal logic changes are required.

**`proto_converters.py` split strategy:** The current file has helpers used by multiple
services (datetime, metadata, row_to_proto). Split by moving shared utilities to
`db/converters.py` and domain-specific converters into their respective packages.

---

## Architectural Patterns

### Pattern 1: Constrained ForceAtlas2 — Fixed Left Region for Trail

**What:** Trail nodes (breadcrumb history) occupy a fixed left column. Their `x` coordinate
is frozen by setting the graphology `fixed: true` node attribute before running ForceAtlas2.
Neighbourhood nodes on the right have no `fixed` attribute and are laid out freely.

**When to use:** Any time a subset of nodes has semantic spatial meaning (trail = history =
left) and must not drift under force-directed pressure.

**Trade-offs:** Fixed nodes still participate in repulsion calculations — they push
neighbourhood nodes away but do not move themselves. This is exactly the desired behaviour.
The ForceAtlas2 documentation confirms `fixed: true` suppresses position updates for that
node while keeping it as a repulsor.

**Implementation in `stores/graph.ts` reconcile:**

```typescript
// After ensureNode(), before running forceAtlas2.assign():
for (const trailDoc of trail) {
  if (graph.hasNode(trailDoc.id)) {
    // Assign a stable left-column x based on trail index.
    const slotX = -5 - (trail.indexOf(trailDoc) * 2)
    graph.setNodeAttribute(trailDoc.id, 'x', slotX)
    graph.setNodeAttribute(trailDoc.id, 'y', 0)
    graph.setNodeAttribute(trailDoc.id, 'fixed', true)
  }
}
// Pinned node: fixed centre of the right region.
if (pinnedDoc.value && graph.hasNode(pinnedDoc.value.id)) {
  graph.setNodeAttribute(pinnedDoc.value.id, 'x', 0)
  graph.setNodeAttribute(pinnedDoc.value.id, 'y', 0)
  graph.setNodeAttribute(pinnedDoc.value.id, 'fixed', true)
}
// Anchored nodes: fixed in place wherever they settled.
for (const nodeId of anchoredNodeIds) {
  if (graph.hasNode(nodeId)) {
    graph.setNodeAttribute(nodeId, 'fixed', true)
  }
}
```

**Layout call — reduce iterations for less jump:**

```typescript
// In GraphView.vue scheduleLayout():
forceAtlas2.assign(graph, {
  iterations: 50,          // was 100 — fewer needed when most nodes are fixed
  settings: {
    gravity: 1,
    scalingRatio: 10,
    adjustSizes: false,
  },
})
```

**Why 50 not 100:** With trail + pinned nodes fixed, the free nodes (neighbours) need
fewer iterations to converge around a stable anchor. Fewer iterations means less
position change per reconcile = less visual jump.

**Alternative for animated transitions:** Use ForceAtlas2's WebWorker (`FA2Layout`) with
incremental ticking instead of a one-shot `assign()`. The worker exposes `start()` /
`stop()` and emits position updates continuously. This enables smooth animation but adds
complexity. Recommend starting with reduced-iteration `assign()` and only switching to
the worker if the reduced-iteration approach still feels jumpy.

---

### Pattern 2: Fresh Notes Bubble — DOM Overlay Anchored to Pinned Node

**What:** A floating panel component (Vue `<Teleport to="body">`) that tracks the pinned
node's screen position. The position is computed after each Sigma render by calling
`sigma.graphToViewport({ x, y })` on the pinned node's coordinates, then applying a
fixed pixel offset.

**Why not `@floating-ui/dom`:** Floating UI is designed for anchoring to DOM elements.
The pinned node is a canvas draw-call, not a DOM element. The anchor "element" would have
to be a 0×0 invisible div repositioned on every render — that works but adds unnecessary
indirection. Directly reading `sigma.graphToViewport()` after `afterRender` is simpler and
already available from the existing Sigma instance.

**Data flow:**

```
sigma emits 'afterRender'
  ↓
GraphView.vue handler reads pinnedDoc.value.id
  ↓
sigma.graphToViewport(graph.getNodeAttributes(id))
  → { x: screenX, y: screenY }
  ↓
bubblePosition ref = { x: screenX + OFFSET_X, y: screenY }
  ↓
FreshNotesBubble.vue renders with style="left: Xpx; top: Ypx"
```

**Component boundary:**

`GraphView.vue` owns Sigma and coordinates. It passes `bubblePosition` and `pinnedDoc`
as props to `FreshNotesBubble`. The bubble is responsible for fetching and displaying
recent notes — it owns that data concern via the `documents` Pinia store or a
`useDocumentApi` call filtered to `unconnected` documents.

**Bubble note selection strategy:**

The bubble shows the N most recently created notes that have no edges to any currently
visible node. The default N=10 is configurable via a prop (or store setting). The
"unconnected" filter runs in the store against `knownDocs` + visible edge set — no
new backend query is needed for small graphs. For "show all" mode where the visible set
is large, a backend query with `ORDER BY created_at DESC LIMIT N` filtered by
`NOT EXISTS (SELECT 1 FROM graph_edges WHERE ...)` is more appropriate.

**Bubble structure:**

```
FreshNotesBubble.vue
  props: position { x, y }, maxNotes: number
  reads: stores/documents.ts (recent docs) + stores/graph.ts (visible nodes/edges)
  emits: @pin(doc) → calls store.pinNode(doc)
         @connect(docId) → enters connect mode with this node pre-selected
```

---

### Pattern 3: Domain Package Restructuring — Move Without Breaking

**What:** Convert flat `src/*.py` files into `src/domain/*.py` packages. The critical
constraint is that `server.py` and the test suite must continue working with minimal
change, and the generated protobuf code (`bibliophage/`) is untouched.

**When to use:** When a flat module list exceeds ~10 files and navigation requires
knowing which file contains which feature rather than which domain.

**Migration order (safe sequence):**

1. Create target directories with `__init__.py` stubs.
2. Move one domain at a time (e.g., `graph/` first — smallest surface area).
3. Update `server.py` import for that domain.
4. Run the test suite. Fix any import errors.
5. Repeat for next domain.
6. In the final pass, split `proto_converters.py` — shared utilities go to `db/converters.py`,
   domain-specific go to `domain/converters.py`.

**`proto_converters.py` is the riskiest file** — it is imported by almost every service.
Move it last, after all service files have moved. Keep a compatibility shim
`proto_converters.py` at the root that re-exports everything from `db/converters.py`
during the transition, then delete it once all import sites are updated.

**Trade-offs:**
- Pro: navigability, logical cohesion, easier to add domain-level tests
- Con: ~20 import lines to update, risk of circular imports if converters import service
  code (they currently don't — keep it that way)

---

## Data Flow

### Graph Layout — Constrained Reconcile

```
pinNode(doc) called
  ↓
stores/graph.ts: trail.push(previous), expandToDepth(doc.id, hopDepth)
  ↓
graphology graph mutated (nodeAdded/edgeAdded events fire)
  ↓
GraphView.vue: scheduleLayout() debounce fires after 50ms
  ↓
reconcile() sets fixed=true on trail + pinned + anchored nodes
  ↓
forceAtlas2.assign(graph, { iterations: 50, settings })
  ↓
sigma re-renders → 'afterRender' event
  ↓
GraphView.vue: bubblePosition = sigma.graphToViewport(pinnedNodeCoords)
  ↓
FreshNotesBubble.vue re-positions via CSS left/top
```

### Fresh Notes Bubble — Data

```
User pins a node (pinNode called)
  ↓
GraphView.vue passes updated pinnedDoc to FreshNotesBubble as prop
  ↓
FreshNotesBubble watches pinnedDoc → triggers note refresh
  ↓
Option A (small graph): filter knownDocs against visible edges in stores/graph.ts
Option B (large/show-all): useDocumentApi.searchDocuments({ pageSize: N, sort: 'created_desc' })
  filtered by: no edge to any visible node
  ↓
Bubble renders list of N most recent unconnected notes
  ↓
User clicks a note → @pin emitted → GraphView calls store.pinNode(note)
  or @connect emitted → GraphView enters connectMode with note pre-filled
```

### Python Service Restructuring — Import Update Flow

```
Old: server.py imports from flat top-level modules
  from document_service_implementation import DocumentServiceImplementation

New: server.py imports from domain packages
  from documents import DocumentServiceImplementation

  documents/__init__.py re-exports from documents/service.py
  documents/service.py imports from db/postgres.py, documents/converters.py
```

No runtime behaviour changes — purely organizational.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (1 user, ~hundreds of docs) | Existing approach is fine; ForceAtlas2 sync on main thread is acceptable |
| Hundreds of nodes visible at once | Switch to ForceAtlas2 WebWorker (`FA2Layout`) for non-blocking layout |
| Thousands of nodes | Sigma's WebGL renderer handles this; layout computation is the bottleneck — worker is required |

**First bottleneck for layout:** The synchronous `forceAtlas2.assign()` call blocks the
main thread for ~20ms at 200 nodes. With fixed nodes limiting the free set to typically
≤20 nodes, this is negligible. Switch to the worker pattern only when profiling shows
frame drops.

**First bottleneck for the bubble:** Filtering `knownDocs` client-side is fine for
graphs up to ~1000 known nodes. Beyond that, push the `unconnected` filter to the
backend query.

---

## Anti-Patterns

### Anti-Pattern 1: Running ForceAtlas2 on Every Graphology Event

**What people do:** Subscribe to `nodeAdded`/`edgeAdded` and run a full `assign()` in each
handler — this is what the current code does via `scheduleLayout` (debounced).

**Why it's wrong:** During a `pinNode()` that adds 20 nodes, 20 `nodeAdded` events fire
in rapid succession. Without proper fixed-position logic, each iteration treats all
nodes as "new" starting positions, causing the whole graph to jump.

**Do this instead:** Keep the debounce but ensure fixed attributes are set inside
`reconcile()` before the `assign()` call. This way, the one layout pass per burst
starts with stable anchors and only moves the new free nodes.

---

### Anti-Pattern 2: Positioning the Bubble via `@floating-ui/dom` Against a Fake DOM Anchor

**What people do:** Create an invisible 0×0 `<div>` at the node's screen position and
pass it as the floating-ui reference element, calling `autoUpdate` to keep it in sync.

**Why it's wrong:** Requires two layers of position tracking (Sigma's coordinate transform
into the fake div's CSS, then floating-ui's positioning on top). Double source of truth
for a single coordinate.

**Do this instead:** Read `sigma.graphToViewport(nodeAttrs)` directly after `afterRender`
and apply the position as `position: fixed; left: Xpx; top: Ypx` on the Teleported bubble.
`@floating-ui/dom` remains available for other use cases where a real DOM reference
element exists (e.g. a right-click context menu anchored to a button).

---

### Anti-Pattern 3: Splitting `proto_converters.py` Before Moving Service Files

**What people do:** Start the restructuring with the shared utility file because it seems
cleanest to move first.

**Why it's wrong:** `proto_converters.py` is imported by every service implementation.
If it moves before its callers do, every service import breaks simultaneously — a large
noisy diff that is hard to review and easy to get wrong.

**Do this instead:** Move service files one at a time first, update their imports to still
reference the old `proto_converters.py` path. Move converters last. The compatibility
shim pattern (re-exporting from new location at old path) keeps each step independently
verifiable.

---

### Anti-Pattern 4: Storing Trail Nodes Only in the Pinia Store (No Canvas Columns)

**What people do:** Leave all position assignment to ForceAtlas2, assuming trail nodes
will naturally cluster to the left over multiple iterations.

**Why it's wrong:** Force-directed layouts are non-deterministic. Trail nodes end up
wherever repulsion math puts them, which changes every time a new node is pinned.
Users lose spatial orientation because the "left = history" metaphor is never enforced.

**Do this instead:** Explicitly set `x = -5 - (trailIndex * 2)` and `fixed = true` on
each trail node before every layout pass. The column assignment is deterministic and
survives across pin changes.

---

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `GraphView.vue` ↔ `stores/graph.ts` | Pinia reactive refs + actions | `graph` (Graphology instance) is `markRaw` — never proxied by Vue |
| `GraphView.vue` → `FreshNotesBubble.vue` | Props: `position`, `pinnedDoc`, `maxNotes` | Bubble emits `@pin`, `@connect` back up |
| `FreshNotesBubble.vue` ↔ `stores/documents.ts` | Pinia store read | Recent docs query; no new store needed |
| `stores/graph.ts` → `useGraphApi` | Composable async calls | Neighbour fetch, edge CRUD |
| `server.py` ↔ domain packages | Python imports | `__init__.py` re-exports maintain a stable surface |
| domain services ↔ `db/postgres.py` | Singleton import | `get_postgres_db()` pattern unchanged |
| `documents/converters.py` ↔ `db/converters.py` | Python import | Shared proto utilities live in `db/`; domain converters import from there |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| PostgreSQL/pgvector | Singleton async pool (`db/postgres.py`) | Schema init on startup in `server.py` lifespan |
| Ollama | HTTP REST via LangChain ChatOllama (`llm/client.py`) | Streaming tokens via server-sent events |
| Sigma.js | Direct JS object in `GraphView.vue` (`let sigma: Sigma`) | Not reactive; lifecycle tied to `onMounted`/`onBeforeUnmount` |
| Graphology | `markRaw(new Graph())` in Pinia store | Sigma subscribes to graphology events; Vue must not proxy |

---

## Build Order Implications

The three work areas have clear dependencies:

**Phase 1 — Constrained Layout (no new components, modifies existing)**
- Modify `stores/graph.ts`: add `fixed` attribute assignment in `reconcile()`
- Modify `GraphView.vue`: reduce iterations, extract layout constants
- No backend changes needed
- Unblocks: layout stability required before bubble UX is usable

**Phase 2 — Fresh Notes Bubble (new component, reads existing stores)**
- Depends on: stable layout from Phase 1 (bubble position must be predictable)
- Modify `GraphView.vue`: add `afterRender` listener, `bubblePosition` ref
- Create `FreshNotesBubble.vue`
- Modify `stores/graph.ts` if filtering unconnected notes client-side
- No backend changes needed for basic bubble; backend query optional for large graphs

**Phase 3 — Python Restructuring (backend only, no frontend changes)**
- Independent of Phases 1 and 2 — can run in parallel with front-end work
- One domain at a time, test suite validates each step
- `proto_converters.py` moved last
- `update_document` implementation fits naturally into `documents/service.py` during the move

**Phase 3 also resolves:** systems/tags junction table wiring naturally belongs in
`documents/service.py` and `documents/converters.py` — the move creates the right place
for it.

---

## Sources

- Graphology ForceAtlas2 `fixed` attribute: [graphology/graphology discussion #375](https://github.com/graphology/graphology/discussions/375) — confirms `fixed: true` node attribute prevents position updates while keeping repulsion active (MEDIUM confidence — source is community discussion referencing source code, not official docs page)
- Graphology layout-forceatlas2 README: [github.com/graphology/graphology](https://github.com/graphology/graphology/blob/master/src/layout-forceatlas2/README.md) — WebWorker `FA2Layout` API, `start()`/`stop()`/`kill()` methods (HIGH confidence — official source)
- Sigma.js coordinate systems: [sigmajs.org/docs/advanced/coordinate-systems/](https://www.sigmajs.org/docs/advanced/coordinate-systems/) — `graphToViewport()` / `viewportToGraph()` transforms (HIGH confidence — official docs)
- Sigma.js `afterRender` event: confirmed in Sigma v3 changelog and Core Library docs at [deepwiki.com/jacomyal/sigma.js](https://deepwiki.com/jacomyal/sigma.js/2-core-library)
- `@floating-ui/dom` already in `package.json` as `@floating-ui/dom 1.7.4` (HIGH confidence — verified in STACK.md)
- FastAPI domain structuring: [fastapi.tiangolo.com/tutorial/bigger-applications/](https://fastapi.tiangolo.com/tutorial/bigger-applications/) (HIGH confidence — official docs)
- Python `__init__.py` re-export compatibility: [Python import system docs](https://docs.python.org/3/reference/import.html) (HIGH confidence — official)

---

*Architecture research for: Bibliophage Notes & Graph UX Overhaul milestone*
*Researched: 2026-06-07*
