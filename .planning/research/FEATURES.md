# Feature Research

**Domain:** Graph-based note-taking and knowledge management (embedded in RAG app for RPG rulebooks)
**Researched:** 2026-06-07
**Confidence:** HIGH (core graph UX patterns well-established across multiple mature tools)

---

## Context: Bibliophage-Specific Framing

Bibliophage is not a general-purpose PKM tool — it is an RPG rulebook RAG app that gains a note-taking layer. The user population is a single user (GM or player) building a knowledge graph over rulebook content. This narrows scope significantly:

- No multi-user collaboration required
- No daily notes / journaling workflow expected
- Graph nodes are documents (rulebook chunks + personal notes), not arbitrary block outlines
- Edges are explicit and meaningful (manual linking), not generated from link syntax parsing
- The graph already exists and works; this milestone enhances the UX around creating and navigating within it

Reference tools analyzed: Obsidian, Logseq, Roam Research, Kanka, World Anvil, LegendKeeper, Tana.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any graph-based note tool. Missing these makes the product feel broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Create note from graph canvas | Any graph tool lets you add nodes inline; switching to another view to create a note breaks spatial flow | MEDIUM | PROJECT.md lists this as active requirement; node created at click position or near active node |
| Edit note content in place | A note you can't edit is a dead artifact | LOW | Already exists via CodeMirror 6 editor; `update_document` NotImplementedError must be fixed first |
| Bidirectional edge visibility | If A links to B, selecting B should reveal A as a backlink; users rely on this to understand context | LOW | Existing connect mode creates edges; backlink panel or graph highlight is the UX expression of this |
| Node navigation by click | Click a node, open that note — the canonical graph UX interaction | LOW | Already present via Sigma.js click handler |
| Pan and zoom | Navigate large graphs without losing orientation | LOW | Already present via Sigma.js defaults |
| Search / quick-switch to a node | In any knowledge tool with 50+ notes, search is the primary navigation method; the graph becomes secondary | MEDIUM | Fuzzy full-text search over document titles and content; keyboard-invoked (Cmd+K / Ctrl+K pattern) |
| Visual distinction between node types | Rulebook chunks vs personal notes look different so users know what they're looking at | LOW | Color or shape differentiation by document type (RULEBOOK, GM_NOTES, etc.) |
| Local graph view (neighbourhood) | Users want to see connections around a specific node without the full-vault noise | MEDIUM | Obsidian local graph pattern; depth slider (1–3 hops); already relevant given trail/anchor pattern in project |
| Delete a node with confirmation | Creating notes that can never be removed is a trust-breaker | LOW | Soft-delete or hard-delete; confirm dialog required |
| Tag / label filtering on graph | Users categorize content with tags; they need to isolate those subsets in the graph | MEDIUM | Junction tables already in schema but not wired; PROJECT.md lists this as active TODO |

### Differentiators (Competitive Advantage)

Features that would make Bibliophage's graph UX distinctive for its RPG rulebook domain.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Fresh notes bubble near active node | Surfaces recent unconnected notes contextually without modal interruption; keeps hands on keyboard and eyes on graph | MEDIUM | PROJECT.md active requirement; pluggable selection strategy (most recent, tag-filtered, etc.) |
| Constrained layout: trail pinned left, neighbourhood force-directed right | Prevents spatial disorientation from ForceAtlas2 jumps; the trail becomes a stable "breadcrumb spine" | MEDIUM | PROJECT.md active requirement; requires overriding ForceAtlas2 with layout constraints |
| Animated/gradual layout transitions | Users track where nodes moved; abrupt repositioning causes "lost in the graph" feeling | MEDIUM | Sigma.js supports position interpolation; prevents cognitive reset on each reconcile |
| Authority-weighted node sizing or edge weight display | Rulebook nodes carry more semantic authority than community notes (GM_NOTES 1.2x, RULEBOOK 1.0x, etc.); surfacing this helps users assess information quality at a glance | LOW | Authority weights already in backend; visual encoding is purely frontend |
| RAG-context indicator on nodes | Show which nodes were retrieved in the last chat query; bridges the gap between graph browsing and LLM chat | MEDIUM | Requires passing retrieved chunk IDs back to the graph view |
| Inline note creation with auto-link to active node | Creating a note and immediately linking it to the currently-selected node eliminates a two-step workflow | LOW | Enhancement to the "create from canvas" feature; pre-populate edge from new note to context node |
| System / campaign grouping visible on graph | RPG users think in systems (D&D 5e, Pathfinder) and campaigns; grouping nodes by system on the graph matches their mental model | MEDIUM | Systems junction table exists but not wired; colored convex hull or cluster shading around system groups |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-linking via content analysis (NLP) | Seems like it would discover hidden connections automatically | Creates spurious edges that pollute the graph; destroys the semantic meaning of a manually curated edge; PROJECT.md explicitly scopes this out | Keep edges manual; offer "similar documents" suggestions in a side panel without creating actual edges |
| Real-time collaborative editing | "It would be great to share with my players" | Single-user constraint is a load-bearing architectural decision (no conflict resolution, no presence, no auth layers); scope creep that delays core value | Share-by-export (PDF, markdown) or read-only view link if sharing is needed later |
| Block-level linking (Roam-style transclusion) | Obsidian/Roam power users expect paragraph-level references | Bibliophage's data model uses documents as atomic nodes; block-level links would require a chunk-level identity system and a new graph layer; massive complexity | Link to the document that contains the relevant chunk; use RAG chat to retrieve the specific content |
| Daily notes / journaling workflow | PKM users are accustomed to daily capture pages | Irrelevant to RPG rulebook research workflows; adds UI surface area with no domain value | Session log document type serves the same intent in a domain-appropriate way |
| Full Zettelkasten / evergreen note methodology enforcement | Some users want the app to enforce linking discipline | Tool-imposed workflow friction causes abandonment; Bibliophage's value is navigation of existing content, not methodology enforcement | Provide structural affordances (backlinks, orphan detection) without mandating a workflow |
| 3D graph visualization | Visually impressive, seen in research tools | Navigability collapses in 3D; users lose spatial memory of node positions; interaction cost (rotate, depth perception) is high | Strong 2D layout with depth conveyed by filtering and local graphs |
| Global real-time graph recompute on every edit | Naive implementation recomputes layout after every document save | Causes the "jumpy repositioning" problem already identified in PROJECT.md; every edit destroys spatial memory | Incremental layout: only reposition new nodes; anchor existing nodes in place |
| Automatic tag extraction from content | Reduces manual tagging burden | Tags extracted from rulebook PDF text are noisy (every mechanical term becomes a tag); overwhelms the filtering UI | Manual tagging with autocomplete from existing tag vocabulary |

---

## Feature Dependencies

```
[Edit/Update document]
    └──required-by──> [Create note from canvas]
    └──required-by──> [Fresh notes bubble]
    └──required-by──> [Inline note with auto-link]

[Fix update_document NotImplementedError]
    └──required-by──> [Edit/Update document]

[Tag/system junction table wiring]
    └──required-by──> [Tag filtering on graph]
    └──required-by──> [System grouping on graph]

[Create note from canvas]
    └──enhances──> [Inline note creation with auto-link to active node]
    └──enhances──> [Fresh notes bubble]

[Local graph view]
    └──enhances──> [Fresh notes bubble]  (bubble is a constrained local view)

[Constrained layout: trail pinned]
    └──required-by──> [Animated layout transitions]  (transitions need stable anchor positions)

[Authority-weighted node sizing]
    └──requires──> [Visual distinction between node types]  (same visual encoding layer)

[RAG-context indicator]
    └──requires──> [Chat system returns retrieved node IDs]  (backend API change)

[Search / quick-switch]
    ──conflicts-with──> [Navigation purely via graph]
    (search is the escape hatch when graph navigation fails; both must coexist)
```

### Dependency Notes

- **`update_document` must be fixed before anything else:** Creating notes from the canvas is meaningless if you cannot then edit them. This is the critical path blocker for all note-creation features.
- **Tag junction table wiring unlocks two features:** Both tag filtering and system grouping on the graph share the same backend prerequisite. Wire once, enable both.
- **Constrained layout is a prerequisite for animated transitions:** You cannot animate to stable positions if positions are not deterministic. ForceAtlas2 randomness must be eliminated first.
- **Fresh notes bubble is a specialised local graph view:** It shares the "show nodes within N hops of active node" logic. Implementing local graph view first means the bubble is a configuration of existing code.

---

## MVP Definition

### Launch With (v1 — this milestone)

Minimum needed to deliver the core value: "users can create, edit, and connect notes fluidly inside the graph view without losing spatial context."

- [ ] Fix `update_document` — prerequisite for all editing; nothing else ships without it
- [ ] Create note from graph canvas — the central new UX capability
- [ ] Constrained layout (trail pinned left) — prevents spatial disorientation; ForceAtlas2 runs only on neighbourhood, not full graph
- [ ] Animated layout transitions — makes repositioning legible rather than jarring
- [ ] Tag/system junction table wiring — completes existing incomplete data model; enables filtering
- [ ] Fresh notes bubble (top-10 recent unconnected notes near active node) — contextual discovery without modal interruption
- [ ] Visual distinction between node types by color — makes the graph readable once notes are mixed with rulebook chunks

### Add After Validation (v1.x)

Features to add once core note workflow is working and stable.

- [ ] Search / quick-switch (Cmd+K) — essential at scale; add when note count makes graph navigation impractical (expected: 30–50 notes)
- [ ] Tag filtering on graph — useful once tags are actually populated via junction tables
- [ ] Inline auto-link to active node on creation — low complexity enhancement to canvas creation
- [ ] Local graph view with depth control — natural evolution of the neighbourhood layout already implemented

### Future Consideration (v2+)

Defer until core value is validated and used regularly.

- [ ] Authority-weighted node sizing — valuable but purely cosmetic; defer until core UX is stable
- [ ] RAG-context indicator on nodes — requires backend API change; high value for power users; medium implementation cost
- [ ] System/campaign cluster grouping (convex hull) — complex visual feature; defer until system data is populated and users feel the need
- [ ] Orphan node detection / "disconnected notes" panel — helps users maintain graph health over time; not needed at low note counts

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Fix `update_document` | HIGH | LOW (pseudocode exists) | P1 |
| Create note from canvas | HIGH | MEDIUM | P1 |
| Constrained layout | HIGH | MEDIUM | P1 |
| Animated transitions | HIGH | MEDIUM | P1 |
| Tag junction table wiring | MEDIUM | LOW | P1 |
| Fresh notes bubble | HIGH | MEDIUM | P1 |
| Node type color distinction | MEDIUM | LOW | P1 |
| Search / quick-switch | HIGH | MEDIUM | P2 |
| Tag filtering on graph | MEDIUM | LOW (after wiring) | P2 |
| Inline auto-link on creation | MEDIUM | LOW | P2 |
| Local graph with depth control | MEDIUM | MEDIUM | P2 |
| Authority-weighted node sizing | LOW | LOW | P3 |
| RAG-context indicator | HIGH | HIGH | P3 |
| System cluster grouping | MEDIUM | HIGH | P3 |
| Orphan node detection | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for this milestone
- P2: Should have, add when note count or user friction demands it
- P3: Nice to have, future milestone

---

## Competitor Feature Analysis

This table maps how reference tools implement each table-stakes feature, and what Bibliophage's approach should be given its constraints (single-user, PostgreSQL-backed, Sigma.js graph, RPG domain).

| Feature | Obsidian | Logseq | Roam Research | Bibliophage Approach |
|---------|----------|--------|---------------|----------------------|
| Note creation from graph | Via "Create note" context menu on canvas; not from graph view itself | Not from graph view; outline-first | Not from graph view; daily notes first | Context menu or double-click on empty canvas area; position new node near click point |
| Bidirectional links | Implicit from `[[wikilink]]` syntax; backlinks panel in editor | Implicit from `[[wikilink]]`; backlinks panel | Implicit; backlinks appear as page mentions | Explicit via connect mode (already exists); backlink panel in note editor sidebar |
| Local/neighbourhood graph | Local graph command; configurable depth 1–5 | Page graph shows immediate neighbours only | Not available | Neighbourhood panel or depth-limited graph filter; constrained layout already achieves this for trail |
| Node type visual encoding | Color groups via query-based rules | Tag-based coloring | None | Color by `document_type` field (RULEBOOK, GM_NOTES, SUPPLEMENT, etc.) |
| Search / navigation | Cmd+O quick switcher; global search Cmd+Shift+F | Cmd+K command palette with search | Page search; no quick-switch | Cmd+K fuzzy search over title + content; navigates to node and selects it in graph |
| Tag filtering | Filter panel on graph; color groups by tag | Tag-based filtering on graph | Query-based filtering | Filter panel using tags from junction tables |
| Layout stability | Force-directed; no pinning; nodes jump on every open | Same as Obsidian | No graph layout | Constrained layout: trail pinned, neighbourhood force-directed; positions persisted |
| Domain-specific grouping | None (generic) | None (generic) | None (generic) | System/campaign groups visible via color convex hull — differentiator for RPG domain |

---

## Sources

- Obsidian graph view documentation: https://obsidian.md/help/plugins/graph
- Obsidian vs Logseq vs Roam comparison: https://thesweetsetup.com/obsidian-vs-roam/
- Graph view comparison across tools: https://alvistor.com/comparing-roamresearch-graph-view-with-logseq-obsidian-and-others/
- Bidirectional links and backlink UX: https://reflect.app/blog/what-are-backlinks-a-guide
- Logseq graph filtering discussion: https://discuss.logseq.com/t/option-to-ignore-certain-nodes-in-the-graph/1312
- Sigma.js interaction features: https://v4.sigmajs.org/
- RPG campaign management tools: https://kanka.io/ and https://www.worldanvil.com/
- Knowledge graph pitfalls and orphaned notes: https://forum.obsidian.md/t/orphan-notes/51808
- Personal knowledge graphs in Obsidian: https://volodymyrpavlyshyn.medium.com/personal-knowledge-graphs-in-obsidian-528a0f4584b9
- Roam Research block references and sidebar: https://aitoolscoop.com/tool/roam-research/

---

*Feature research for: Graph-based note-taking and knowledge management (Bibliophage milestone)*
*Researched: 2026-06-07*
