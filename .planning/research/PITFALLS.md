# Pitfalls Research

**Domain:** Graph layout animation + note-taking UX + Python service restructuring (brownfield)
**Researched:** 2026-06-07
**Confidence:** HIGH (code read directly; library behaviour confirmed against official docs and GitHub issues)

---

## Critical Pitfalls

### Pitfall 1: ForceAtlas2 Resets Node Positions on Every Reconcile

**What goes wrong:**
The current `scheduleLayout()` calls `forceAtlas2.assign(graph, { iterations: 100 })` on
every structural change (`nodeAdded`, `nodeDropped`, `edgeAdded`, `edgeDropped`). ForceAtlas2
does not preserve previous positions as a warm start — it treats each call as a fresh run.
When reconcile drops and re-adds nodes (which it does), the new nodes are initialized with
`Math.random()` for x/y, so the whole graph jumps to a new random configuration after each
reconcile call. This is the root cause of the "jumpy repositioning" noted in `PROJECT.md`.

**Why it happens:**
`reconcile()` diffs the graphology graph and calls `graph.dropNode()` / `graph.addNode()`.
Each `addNode` emits `nodeAdded`, which debounces into `scheduleLayout()`. Nodes added after
drop start at new random positions, so even preserving the x/y attributes on remaining nodes
is not enough — newly re-added nodes pull the force simulation to a different equilibrium.

**How to avoid:**
Two-part fix:
1. When adding a node that was previously visible, carry its last x/y forward. The graph store
   already stores `knownDocs` — extend it to also store last known positions per node ID.
2. For the constrained trail layout: set `fixed: true` on the graphology node attribute for
   trail/pinned nodes before calling ForceAtlas2. ForceAtlas2 respects a `fixed` attribute and
   will not move those nodes. The project constraint says "stay with ForceAtlas2" — this is the
   correct path, not replacing the algorithm.

**Warning signs:**
- Graph nodes visibly jump to random positions when pinning a new node.
- Trail/pinned node appears in a different X position after each pin action.
- Console logs show rapid `nodeAdded` / `edgeAdded` bursts followed by a layout call.

**Phase to address:** Phase covering "Constrained graph layout / trail pinned to left."

---

### Pitfall 2: All-Zero Node Positions Cause ForceAtlas2 Layout Collapse

**What goes wrong:**
ForceAtlas2 has a documented edge case: if all nodes start with `x=0, y=0`, the algorithm
cannot compute repulsive forces and the layout collapses (all nodes stay at the origin or
produce NaN positions). Sigma renders nothing useful. This can happen any time new nodes are
added without initializing their positions.

**Why it happens:**
If `ensureNode` is called without a prior `Math.random()` on x/y (e.g., during a refactor
that changes the add-node path), or if position restoration logic fails silently, all fresh
nodes get x=0, y=0 from the graphology default.

**How to avoid:**
Always initialize x/y to a random or deterministic non-zero value before `forceAtlas2.assign`
is called. Use `graphology-layout/random` as a pre-pass for any node whose position is not
already set. Add a guard before `scheduleLayout`: if any node has `x === 0 && y === 0`, run
a random layout pass first.

**Warning signs:**
- After adding new nodes, the graph canvas goes blank or shows a single dot at center.
- Sigma shows nodes but they are all overlapping at one point.
- ForceAtlas2 returns NaN in node attribute inspection.

**Phase to address:** Phase covering "Constrained graph layout / animated transitions."

---

### Pitfall 3: animateNodes Import Path Differs in Sigma 3.x

**What goes wrong:**
`animateNodes` is imported from `"sigma/utils/animate"`. Sigma 3.0 restructured its exports
as part of a multi-package rewrite. Code written against Sigma 2.x examples may import from
a path that no longer exists or may use a different function signature. The project is on
`sigma 3.0.0` — any examples found online that reference older Sigma versions are unreliable.

**Why it happens:**
Sigma 3.0 broke the programs API, renamed renderers, and moved utilities. Documentation
examples from blog posts and Stack Overflow often target 2.x. The npm package name is still
`sigma` but the internal module structure changed substantially.

**How to avoid:**
Before using `animateNodes`, verify the exact export path by reading `node_modules/sigma/`
directly or checking the sigma 3.x changelog. The confirmed path is `"sigma/utils/animate"`.
Verify the function signature: `animateNodes(graph, positions, { duration })` where `positions`
is a `{ [nodeId]: { x, y } }` map. Do not copy-paste examples without checking the sigma
version they target.

**Warning signs:**
- TypeScript compile error: "Module 'sigma/utils/animate' has no exported member animateNodes."
- Runtime error: "animateNodes is not a function."
- Vite/rollup tree-shaking silently drops the import.

**Phase to address:** Phase covering "Animated layout transitions."

---

### Pitfall 4: Vue Reactive Proxy Breaks Sigma's Internal Event Wiring

**What goes wrong:**
If a `Graph` instance (from graphology) is stored in Pinia state *without* `markRaw`, Vue
will wrap it in a Proxy. Sigma subscribes to graphology's own internal event bus via object
identity. When Sigma receives the proxied version of the graph and graphology events are
fired on the raw version (or vice versa), listener registration fails silently — click events,
node addition events, and render triggers stop working.

**Why it happens:**
Vue 3's `reactive()` and `ref()` auto-wrap objects in Proxy. Pinia uses `reactive()` for
setup stores. The current code already uses `markRaw(new Graph(...))` in `graph.ts`, which
is correct. The risk is regression: any future refactor that moves the graph initialization
or passes the graph through a reactive context without re-applying `markRaw` will reintroduce
the bug silently (no error, just broken events).

**How to avoid:**
Keep `markRaw` on the `Graph` instance. Add a comment explaining why — the current store
already has one. When adding new sigma-related state (e.g., the Sigma renderer instance
itself), wrap it with `markRaw` too. The `Sigma` constructor object must also not be proxied.

**Warning signs:**
- Graph renders initially but clicking nodes does nothing.
- `sigma.on('clickNode', ...)` handler never fires.
- `graph.on('nodeAdded', ...)` fires but Sigma does not re-render.
- Introducing a new reactive wrapper in the store causes the above.

**Phase to address:** Any phase touching the graph store or adding new Sigma state.

---

### Pitfall 5: Sigma Instance Leaks When GraphView Unmounts Without Cleanup

**What goes wrong:**
If `sigma.kill()` and `graph.off(...)` are not called before the component unmounts — or if
they are called in the wrong order — the Sigma WebGL context is not released. On re-navigation
(e.g., the user leaves /graph and returns), a second Sigma instance is created on the same DOM
element. The result is two renderers fighting over the canvas, doubled event listeners, and
memory leaks.

**Why it happens:**
The current code handles this in `onBeforeUnmount`, which is correct. The risk is during
feature work that adds new event listeners (e.g., for a "fresh notes bubble" overlay) without
adding corresponding cleanup.

**How to avoid:**
Every `graph.on(event, handler)` call added in `onMounted` must have a matching `graph.off`
in `onBeforeUnmount`. Treat the cleanup block as a checklist — add the removal before adding
the registration. If adding animation timers (for node position tweens), clear them in cleanup.

**Warning signs:**
- `graph.listenerCount('nodeAdded')` increases by N on each navigation cycle.
- Memory profiler shows WebGL context count growing.
- After re-visiting /graph, node clicks trigger handlers twice.

**Phase to address:** Phase adding animated transitions or the fresh-notes overlay to GraphView.

---

### Pitfall 6: Junction Table Wiring Without a Transaction Causes Partial Writes

**What goes wrong:**
When `update_document` inserts systems and tags via junction tables
(`map_documents_to_systems`, `map_documents_to_tags`), doing this as three separate database
calls — UPDATE documents, DELETE FROM map_documents_to_systems, INSERT INTO map_documents_to_systems —
without wrapping them in a transaction means a server crash or exception between calls leaves
the document row updated but its systems/tags deleted (or vice versa). The DB ends up in an
inconsistent state: a document with no system association, which violates the application
invariant that every document belongs to at least one system.

**Why it happens:**
The `postgres_db.py` `execute()` and `fetchone()` methods each acquire a connection from the
pool for a single statement. There is no implicit multi-statement transaction. The project's
pool is opened with `autocommit=True` in `psycopg_pool`, so each standalone statement commits
immediately. The existing `db.transaction()` context manager exists precisely for this case
but the `store_document` method has TODOs that skip junction table inserts entirely — the
pattern to follow for `update_document` is: `async with db.transaction() as conn:` covering
all three statements.

**How to avoid:**
Wrap the document UPDATE + junction table DELETE/INSERT in a single `async with db.transaction()
as conn` block. Pass `conn` directly to each statement using `conn.execute(...)` rather than
the convenience methods (`fetchone`, `execute`) which each acquire their own connection.
Additionally, use DELETE + INSERT (not UPSERT) for junction tables within the transaction —
this is simpler and avoids the ON CONFLICT complexity; atomicity from the transaction means
partial state is not observable.

**Warning signs:**
- A document exists in the `documents` table with no rows in `map_documents_to_systems`.
- Restarting the server after a network timeout leaves orphaned documents.
- `search_documents` system_filters produce zero results even though systems were set at
  upload time (because the junction table insert was silently skipped).

**Phase to address:** Phase implementing `update_document` and wiring systems/tags junction tables.

---

### Pitfall 7: Python Import Paths Break When Moving Files to Domain Subdirectories

**What goes wrong:**
The current Python server runs with `python-server/src/` on `sys.path`. All files there
are top-level modules: `from postgres_db import get_postgres_db` works because `postgres_db`
is a top-level name. Moving `postgres_db.py` to `python-server/src/db/postgres_db.py` makes
that import fail at runtime — and at the server startup line where the singleton is created,
not at import time, so the failure may only surface after several services initialize.

**Why it happens:**
Python resolves imports relative to `sys.path`. The server entry point is launched with the
current directory as the path root. Moving a module to a subdirectory changes its qualified
name. Every `from postgres_db import ...` across all service implementations, `server.py`,
and `proto_converters.py` must be updated. Missing even one causes an `ImportError` that
only fires when that module is first loaded.

**How to avoid:**
Move one domain at a time and run `just tests` after each move before moving the next.
Use absolute import paths from the new root (e.g., `from db.postgres_db import get_postgres_db`)
consistently — do not mix relative and absolute. Add `__init__.py` to each new subdirectory.
Verify that pytest's `pythonpath` configuration in `pyproject.toml` still points to
`python-server/src/` (or the new package root) so test discovery does not break.

**Warning signs:**
- `ImportError: No module named 'postgres_db'` on server startup.
- Tests pass but server fails to start (tests mock the import; server does not).
- `vulture` reports no dead code but `deptry` reports missing imports — indicates a module
  was moved but not all callers updated.

**Phase to address:** Phase covering "Python server domain-based restructuring."

---

### Pitfall 8: Singleton Global State Becomes Stale After Module Renames

**What goes wrong:**
The singleton pattern uses module-level `_instance` variables:
`_db: BibliophageDatabase | None = None`. If the module is renamed or moved and some callers
still import from the old path (e.g., via a stale `__init__.py` re-export), two separate
module objects exist in `sys.modules` — each with its own `_db = None`. The second caller
gets a fresh None and creates a second connection pool. The result is two pools, doubled
connections, and the database being initialized twice.

**Why it happens:**
Python's module identity is its path in `sys.modules`. A module at `postgres_db` and the same
file re-imported as `db.postgres_db` are different module objects. This is a well-known
Python gotcha with the singleton-via-global pattern.

**How to avoid:**
After each module move, search all import sites with `grep` / Grep for both the old name and
the new name to confirm no mixed imports remain. Remove or empty any `__init__.py` re-exports
that would create alias paths. Run the server locally and check startup logs — the log line
`"BibliophageDatabase instance created"` should appear exactly once.

**Warning signs:**
- `"BibliophageDatabase instance created"` appears more than once in startup logs.
- Two sets of "PostgreSQL connection pool initialised" log lines.
- Connection pool exhaustion under light load.
- Tests pass in isolation but fail when run together (each test imports from a different path).

**Phase to address:** Phase covering "Python server domain-based restructuring."

---

### Pitfall 9: NotImplementedError in a Connect RPC Handler Produces an Opaque 500 Error

**What goes wrong:**
`update_document` currently raises `NotImplementedError`. When the frontend calls this
endpoint, Connect RPC catches the unhandled exception and returns a generic `internal` error
status with no meaningful message exposed to the client. The frontend composable gets a failed
response, the user sees no feedback, and the editor silently discards the save. There is no
breadcrumb indicating the method is not implemented rather than having a data error.

**Why it happens:**
Connect RPC maps unhandled Python exceptions to the `INTERNAL` status code. The message is
the Python exception string, but it is not surfaced to the browser in development mode unless
the Connect RPC interceptor is configured to expose internal errors. By default it is not.

**How to avoid:**
Before implementing `update_document` fully, add a stub that returns
`UpdateDocumentResponse(success=False, message="update_document not yet implemented")` rather
than raising. This makes the failure visible in the UI and does not mislead the user into
thinking their save succeeded. When implementing for real, test the full round-trip including
the frontend response handler before marking complete.

**Warning signs:**
- Frontend shows a generic "request failed" toast with no detail.
- Backend logs show `NotImplementedError` stacktrace.
- The document edit modal closes without saving but reports no error.

**Phase to address:** Phase implementing `update_document`.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip junction table inserts in `store_document` (current TODO) | Simpler initial implementation | Systems and tags are always empty; filtering breaks silently | Never — wire it as part of update_document phase |
| Run ForceAtlas2 with 100 iterations on every structural change | Simple, always runs | Graph jumps on every pin/expand; gets worse with more nodes | Never for constrained layout goal |
| Leave `_proto_to_update_params` logic inline in `update_document` | Faster to write | Violates the existing converter pattern; hard to test separately | Acceptable in MVP, extract when adding second update path |
| Move all Python files at once in a single large PR | Faster to do in one session | Any import miss causes a full-server crash; impossible to bisect | Never — move one domain at a time |
| Use `fixed=true` on all nodes during animation | Prevents thrashing during tween | Layout never runs after animation completes; graph is frozen | Only for the duration of the tween, then remove `fixed` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| ForceAtlas2 + fixed nodes | Setting `fixed: true` as a node attribute but passing it through graphology's `setNodeAttribute` after `forceAtlas2.assign` — too late | Set `fixed: true` on the node attribute *before* calling `forceAtlas2.assign`; the attribute is read at the start of each iteration |
| `animateNodes` + position-preserving reconcile | Calling `reconcile()` mid-animation drops and re-adds nodes, cancelling the tween | Defer reconcile until the animation promise resolves; hold a "pending reconcile" flag |
| psycopg3 `transaction()` + `execute()` helper | Using the module-level `db.execute()` inside a `db.transaction()` block acquires a second connection outside the transaction | Pass the `conn` from `async with db.transaction() as conn` directly to `conn.execute()` calls |
| Sigma 3.x + Pinia store | Storing `sigma` renderer instance in a `ref()` instead of a module-level variable causes Vue to proxy it, breaking WebGL renderer state | Store Sigma instance in a plain `let sigma: Sigma | null = null` at module scope in the Vue component, not in the store |
| Graphology `markRaw` + Pinia reactive | Accessing `graph` from the store via `storeToRefs` unwraps refs but graphology itself is not a ref — calling `storeToRefs(store).graph` is safe only if `graph` was stored with `markRaw`; ensure no intermediate assignment to a `ref()` | Access `store.graph` directly (not via `storeToRefs`) or verify `markRaw` is still applied |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| ForceAtlas2 at 100 iterations × every structural event | Graph stutters on every expand; worse with > 30 nodes | Reduce iterations for live updates (20–30 is enough for stability); use supervised layout worker for large graphs | Visible with > 20 nodes |
| `searchDocuments` with `pageSize: 10000` in "show all" mode | 10,000 document rows loaded into browser memory, all rendered as Sigma nodes | Add a hard cap in the UI (e.g., 500) and show a warning; or use a background-only representation for unconnected nodes | With > 200 documents loaded |
| Dropping and re-adding nodes in reconcile on every state change | Graph re-layout fires for every single document added; O(N) graphology events per reconcile | Batch graph mutations: collect all drops, then all adds, emit events only after both are done (graphology supports `graph.emit('batch')` pattern or disable/re-enable event listeners) | Visible immediately with deep BFS expansions |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Constrained trail nodes have `fixed: true` during layout but layout still runs repeatedly | Trail nodes stay fixed but neighbourhood nodes continue jumping on every pin change, disorienting the user | Run layout only once after pin settles (after `expandToDepth` completes), not on every intermediate structural change |
| Animated layout transitions run while the user is interacting | Dragging a node mid-animation causes it to snap back to the tween target | Pause layout animation when Sigma emits a `downNode` event; resume on `upNode` |
| "Fresh notes bubble" positions near active node using graph coordinates | After layout animation, the bubble position is stale (computed before tween completes) | Compute bubble position from final node coordinates only after `animateNodes` resolves |
| No confirmation when unsaved note changes exist (existing TODO) | User navigates away from an open note editor and loses changes silently | Wire Vue Router's `onBeforeRouteLeave` guard before implementing the note creation flow |

---

## "Looks Done But Isn't" Checklist

- [ ] **Junction table wiring:** Systems and tags appear in the protobuf response — verify they round-trip through `map_documents_to_systems` and `map_documents_to_tags`, not just JSONB metadata. Query the junction table directly to confirm rows exist.
- [ ] **update_document partial update:** Fields not included in the request should not be overwritten. Verify that sending only `name` does not null out `content`, `source_type`, or `systems`.
- [ ] **Constrained layout trail:** After pinning three different nodes, the trail's left-column nodes should have stable X positions across all three pin operations. If X drifts, the `fixed` attribute is not being set before ForceAtlas2 runs.
- [ ] **Animated transition:** The animation should be perceptible (nodes visibly move) but not jarring. Duration of 300–500ms is typically right. Verify the animation completes before a second pin action is allowed (disable pin button during tween or queue the action).
- [ ] **Python restructure:** After moving all modules, `just lint` must pass with zero errors, `just tests` must pass, and `uvicorn server:api_server` must start without ImportError. All three, not just tests.
- [ ] **Sigma cleanup on unmount:** Navigate to /graph, interact, navigate away, navigate back. Do this 5 times. Open browser devtools memory snapshot and verify `WebGLRenderingContext` count stays at 1.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| ForceAtlas2 position collapse (all nodes at origin) | LOW | Add random position pre-pass before layout call; no data loss |
| Junction table partial write | MEDIUM | Write a one-off SQL script to audit documents with no system row; re-insert missing junction rows manually |
| Stale singleton after module rename | MEDIUM | Restart server; fix all import sites; run `just tests` to confirm; double-check logs for duplicate init messages |
| Sigma instance leak after bad unmount | LOW | Hard refresh browser; fix the cleanup handler; add the missing `graph.off` call |
| NotImplementedError in production update_document call | LOW | Add a stub response immediately; implement fully in the same phase |
| Animation running during user drag | LOW | Add `sigma.on('downNode')` guard to cancel/pause the animation |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ForceAtlas2 resets positions on reconcile | Constrained layout phase | Pin three nodes sequentially; trail X positions must not drift |
| All-zero position collapse | Constrained layout phase | Add a node with no prior position; graph must not blank out |
| animateNodes import path (Sigma 3.x) | Animated transitions phase | `yarn build` produces no TypeScript errors for animate import |
| Vue proxy breaks Sigma event wiring | Any graph store change phase | Click events fire after store refactor; confirmed in browser |
| Sigma leak on unmount | Any phase adding graph event listeners | Browser heap snapshot after 5 navigate-cycles stays flat |
| Junction table partial write | update_document + tags/systems wiring phase | Manual SQL audit of junction tables after a failed mid-update simulation |
| Python import paths break after move | Python restructure phase | `just tests` + server startup both pass after each domain move |
| Stale singleton after rename | Python restructure phase | Startup log shows singleton init exactly once |
| NotImplementedError opaque error | update_document phase | Calling update from frontend before implementation shows a clear error message |

---

## Sources

- [graphology-layout-forceatlas2 official docs](https://graphology.github.io/standard-library/layout-forceatlas2.html) — zero-position edge case documented
- [graphology discussion: Fixed/Pinned nodes with a layout running (#375)](https://github.com/graphology/graphology/discussions/375) — `fixed` attribute behaviour confirmed
- [sigma.js issue: animateNodes improvements (#1215)](https://github.com/jacomyal/sigma.js/issues/1215) — import path and signature for Sigma 3.x
- [sigma.js CHANGELOG.md (main branch)](https://github.com/jacomyal/sigma.js/blob/main/CHANGELOG.md) — Sigma 3.0 breaking changes (programs API rewrite, multi-package repo)
- [sigma.js issue: nodes dancing in ForceAtlas2 (#691)](https://github.com/jacomyal/sigma.js/issues/691) — oscillation / instability behaviour
- [Vue 3 reactivity docs: markRaw](https://vuejs.org/api/reactivity-advanced.html) — identity hazard with proxied third-party objects
- [psycopg3 transactions docs](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) — `autocommit=True` + explicit `transaction()` pattern
- Codebase reading: `GraphView.vue`, `stores/graph.ts`, `document_service_implementation.py`, `postgres_db.py`, `proto_converters.py`, `db_schema/documents.sql` — direct observation of current patterns and TODOs

---
*Pitfalls research for: Bibliophage graph layout animation + note-taking UX + Python restructuring*
*Researched: 2026-06-07*
