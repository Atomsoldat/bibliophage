/**
 * Pinia store for the graph editor view-model.
 *
 * Holds a graphology Graph instance (rendered by Sigma in GraphView.vue) plus
 * meta-state for document graph traversal:
 *
 *   - **Pinned node**: the amber centre of the current view.
 *   - **Hop depth**: how many hops the inner circle extends (1–5).
 *   - **Trail**: a breadcrumb list of previously pinned nodes (purple).
 *   - **Anchored nodes**: user-locked nodes that persist across pin changes (teal).
 *   - **Show all**: toggle to display every document, even unconnected ones (gray).
 *
 * The graphology Graph is marked raw — Sigma subscribes to graphology's own
 * event system, so Vue must not proxy it. All visibility is computed in
 * reconcile() via a role-priority system, then diffed against the graph.
 */

import type { DocumentListItem } from '../bibliophage/v1alpha3/document_pb'
import type { Edge } from '../bibliophage/v1alpha3/graph_pb'
import Graph from 'graphology'
import { defineStore } from 'pinia'
import { markRaw, reactive, ref } from 'vue'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useGraphApi } from '../composables/useGraphApi'

// ── Node roles & visual constants ──────────────────────────────────────

type NodeRole
  = | 'pinned'
    | 'trail-center'
    | 'trail-neighbour'
    | 'anchored'
    | 'anchored-neighbour'
    | 'neighbour'
    | 'unconnected'

// Higher number = higher priority. When a node qualifies for multiple
// roles, the highest-priority role wins.
const ROLE_PRIORITY: Record<NodeRole, number> = {
  'pinned': 7,
  'trail-center': 6,
  'anchored': 5,
  'trail-neighbour': 4,
  'anchored-neighbour': 3,
  'neighbour': 2,
  'unconnected': 1,
}

const ROLE_APPEARANCE: Record<NodeRole, { size: number, color: string }> = {
  'pinned': { size: 16, color: '#f59e0b' },
  'trail-center': { size: 13, color: '#a855f7' },
  'trail-neighbour': { size: 8, color: '#c084fc' },
  'anchored': { size: 13, color: '#14b8a6' },
  'anchored-neighbour': { size: 8, color: '#5eead4' },
  'neighbour': { size: 10, color: '#3b82f6' },
  'unconnected': { size: 6, color: '#6b7280' },
}

const EDGE_COLOR = '#9ca3af'

interface NeighbourhoodCacheEntry {
  neighbours: DocumentListItem[]
  edges: Edge[]
}

export const useGraphStore = defineStore('graph', () => {
  const graphApi = useGraphApi()
  const documentApi = useDocumentApi()

  // Sigma listens to graphology events directly — markRaw prevents Vue from
  // wrapping it in a reactive proxy, which would break sigma's event wiring.
  const graph = markRaw(new Graph({ type: 'mixed', multi: false }))

  // ── core state ───────────────────────────────────────────────────

  const pinnedDoc = ref<DocumentListItem | null>(null)
  const expandedNodeIds = reactive(new Set<string>())
  const selectedNodeId = ref<string | null>(null)
  const lastError = ref<string | null>(null)

  // Hop depth: how many hops the pinned node's inner circle extends.
  const hopDepth = ref(1)
  const isExpandingDepth = ref(false)

  // Breadcrumb trail of previously pinned nodes (FIFO).
  const trail = reactive<DocumentListItem[]>([])
  const trailMaxLength = ref(3)

  // Anchored nodes: always visible regardless of what's pinned.
  const anchoredNodeIds = reactive(new Set<string>())

  // "Show all" mode.
  const showAllNodes = ref(false)
  const allDocuments = ref<DocumentListItem[]>([])

  // Every document we've encountered — lets us pin by ID from canvas.
  const knownDocs = new Map<string, DocumentListItem>()

  const neighbourCache = new Map<string, NeighbourhoodCacheEntry>()
  const manualEdges = new Map<string, Edge>()

  // ── graph helpers ────────────────────────────────────────────────

  function ensureNode(doc: DocumentListItem, role: NodeRole): void {
    const { size, color } = ROLE_APPEARANCE[role]
    if (graph.hasNode(doc.id)) {
      graph.setNodeAttribute(doc.id, 'label', doc.name)
      graph.setNodeAttribute(doc.id, 'size', size)
      graph.setNodeAttribute(doc.id, 'color', color)
      return
    }
    graph.addNode(doc.id, {
      label: doc.name,
      x: Math.random(),
      y: Math.random(),
      size,
      color,
    })
  }

  function ensureEdge(edge: Edge): void {
    if (graph.hasEdge(edge.id)) {
      return
    }
    graph.addEdgeWithKey(edge.id, edge.nodeA, edge.nodeB, {
      size: 1,
      color: EDGE_COLOR,
    })
  }

  // ── reconcile ────────────────────────────────────────────────────

  /**
   * Recompute the visible subgraph. Uses a role-priority system to decide
   * which nodes are visible and how they look. Diffs against the current
   * graphology graph so node positions survive across state changes.
   */
  function reconcile(): void {
    const roleMap = new Map<string, NodeRole>()

    function assignRole(docId: string, role: NodeRole): void {
      const existing = roleMap.get(docId)
      if (!existing || ROLE_PRIORITY[role] > ROLE_PRIORITY[existing]) {
        roleMap.set(docId, role)
      }
    }

    // 1. Pinned node's inner circle (BFS to hopDepth).
    if (pinnedDoc.value) {
      assignRole(pinnedDoc.value.id, 'pinned')
      let frontier = new Set([pinnedDoc.value.id])
      for (let hop = 0; hop < hopDepth.value; hop++) {
        const nextFrontier = new Set<string>()
        for (const nodeId of frontier) {
          const cached = neighbourCache.get(nodeId)
          if (!cached)
            continue
          for (const neighbour of cached.neighbours) {
            assignRole(neighbour.id, 'neighbour')
            nextFrontier.add(neighbour.id)
          }
        }
        frontier = nextFrontier
      }
    }

    // 2. Trail breadcrumbs (each gets 1-hop neighbourhood).
    for (const trailDoc of trail) {
      assignRole(trailDoc.id, 'trail-center')
      const cached = neighbourCache.get(trailDoc.id)
      if (cached) {
        for (const n of cached.neighbours) {
          assignRole(n.id, 'trail-neighbour')
        }
      }
    }

    // 3. Anchored nodes (each gets 1-hop neighbourhood).
    for (const anchoredId of anchoredNodeIds) {
      const doc = knownDocs.get(anchoredId)
      if (doc)
        assignRole(doc.id, 'anchored')
      const cached = neighbourCache.get(anchoredId)
      if (cached) {
        for (const n of cached.neighbours) {
          assignRole(n.id, 'anchored-neighbour')
        }
      }
    }

    // 4. Show-all unconnected (lowest priority).
    if (showAllNodes.value) {
      for (const doc of allDocuments.value) {
        assignRole(doc.id, 'unconnected')
      }
    }

    // Build visible docs from roleMap.
    const visibleNodes = new Map<string, DocumentListItem>()
    for (const [id] of roleMap) {
      const doc = knownDocs.get(id)
      if (doc)
        visibleNodes.set(id, doc)
    }

    // Visible edges: collect from all sources whose nodes are visible.
    const visibleEdges = new Map<string, Edge>()
    function collectEdges(cacheKey: string): void {
      const cached = neighbourCache.get(cacheKey)
      if (!cached)
        return
      for (const edge of cached.edges) {
        if (visibleNodes.has(edge.nodeA) && visibleNodes.has(edge.nodeB)) {
          visibleEdges.set(edge.id, edge)
        }
      }
    }

    for (const expandedId of expandedNodeIds) collectEdges(expandedId)
    for (const trailDoc of trail) collectEdges(trailDoc.id)
    for (const anchoredId of anchoredNodeIds) collectEdges(anchoredId)
    for (const [id, edge] of manualEdges) {
      if (visibleNodes.has(edge.nodeA) && visibleNodes.has(edge.nodeB)) {
        visibleEdges.set(id, edge)
      }
    }

    // Diff against graphology.
    for (const nodeId of [...graph.nodes()]) {
      if (!visibleNodes.has(nodeId))
        graph.dropNode(nodeId)
    }
    for (const edgeKey of [...graph.edges()]) {
      if (!visibleEdges.has(edgeKey))
        graph.dropEdge(edgeKey)
    }
    for (const [id, doc] of visibleNodes) {
      ensureNode(doc, roleMap.get(id) ?? 'unconnected')
    }
    for (const [, edge] of visibleEdges) {
      ensureEdge(edge)
    }
  }

  // ── expand helpers ───────────────────────────────────────────────

  /**
   * Fetch a node's 1-hop neighbourhood into the cache. Does NOT call
   * reconcile — callers batch multiple fetches then reconcile once.
   */
  async function expandSingle(nodeId: string): Promise<void> {
    if (neighbourCache.has(nodeId))
      return
    const resp = await graphApi.getNeighbours(nodeId)
    if (!resp.success) {
      lastError.value = resp.message
      return
    }
    const neighbours = [...resp.neighbours]
    for (const n of neighbours) knownDocs.set(n.id, n)
    neighbourCache.set(nodeId, { neighbours, edges: [...resp.edges] })
    expandedNodeIds.add(nodeId)
  }

  /**
   * BFS expansion from a root node to the given depth. Fetches each
   * level's neighbourhoods in parallel, then reconciles once at the end.
   */
  async function expandToDepth(rootId: string, depth: number): Promise<void> {
    let frontier = [rootId]
    for (let hop = 0; hop < depth; hop++) {
      await Promise.all(frontier.map(id => expandSingle(id)))
      const nextFrontier = new Set<string>()
      for (const id of frontier) {
        const cached = neighbourCache.get(id)
        if (cached) {
          for (const n of cached.neighbours) nextFrontier.add(n.id)
        }
      }
      frontier = [...nextFrontier]
    }
    reconcile()
  }

  // ── public actions ───────────────────────────────────────────────

  /** Pin a document as the centre of the view. Maintains trail and anchors. */
  async function pinNode(doc: DocumentListItem): Promise<void> {
    await graphApi.initialise()
    knownDocs.set(doc.id, doc)

    // Push current pin onto trail (if there is one).
    if (pinnedDoc.value) {
      // Remove if already in trail (avoid duplicates when re-pinning).
      const idx = trail.findIndex(d => d.id === pinnedDoc.value!.id)
      if (idx !== -1)
        trail.splice(idx, 1)
      trail.push(pinnedDoc.value)
      while (trail.length > trailMaxLength.value) trail.shift()
    }

    // If the new doc is in the trail, pull it out.
    const trailIdx = trail.findIndex(d => d.id === doc.id)
    if (trailIdx !== -1)
      trail.splice(trailIdx, 1)

    // Preserve anchor caches; clear the rest.
    const preservedCacheKeys = new Set([
      ...anchoredNodeIds,
      ...trail.map(d => d.id),
    ])
    for (const key of [...neighbourCache.keys()]) {
      if (!preservedCacheKeys.has(key))
        neighbourCache.delete(key)
    }

    pinnedDoc.value = doc
    expandedNodeIds.clear()
    // Re-add anchored + trail nodes so their caches aren't orphaned.
    for (const id of anchoredNodeIds) expandedNodeIds.add(id)
    for (const d of trail) {
      if (neighbourCache.has(d.id))
        expandedNodeIds.add(d.id)
    }

    selectedNodeId.value = null
    lastError.value = null

    isExpandingDepth.value = true
    await expandToDepth(doc.id, hopDepth.value)
    isExpandingDepth.value = false
  }

  /** Pin a node by ID — looks up the doc from previously seen documents. */
  async function pinNodeById(nodeId: string): Promise<void> {
    const doc = knownDocs.get(nodeId)
    if (!doc) {
      lastError.value = `Unknown document ${nodeId}`
      return
    }
    await pinNode(doc)
  }

  /** Fetch a node's neighbourhood (if not cached) and fold it into the view. */
  async function expand(nodeId: string): Promise<void> {
    await expandSingle(nodeId)
    reconcile()
  }

  /** Hide a previously-expanded node's neighbourhood. */
  function collapse(nodeId: string): void {
    if (nodeId === pinnedDoc.value?.id)
      return
    if (!expandedNodeIds.has(nodeId))
      return
    expandedNodeIds.delete(nodeId)
    reconcile()
  }

  /** Change the inner circle depth. Auto-expands from pinned node. */
  async function setHopDepth(depth: number): Promise<void> {
    hopDepth.value = Math.max(1, Math.min(5, depth))
    if (pinnedDoc.value) {
      isExpandingDepth.value = true
      await expandToDepth(pinnedDoc.value.id, hopDepth.value)
      isExpandingDepth.value = false
    }
  }

  /** Toggle a node's anchored status. Anchored nodes stay visible across pins. */
  async function toggleAnchor(nodeId: string): Promise<void> {
    if (anchoredNodeIds.has(nodeId)) {
      anchoredNodeIds.delete(nodeId)
    }
    else {
      anchoredNodeIds.add(nodeId)
      await graphApi.initialise()
      await expandSingle(nodeId)
    }
    reconcile()
  }

  function isAnchored(nodeId: string): boolean {
    return anchoredNodeIds.has(nodeId)
  }

  async function addEdge(sourceId: string, targetId: string): Promise<void> {
    await graphApi.initialise()
    const resp = await graphApi.createEdge(sourceId, targetId)
    if (!resp.success || !resp.edge) {
      lastError.value = resp.message || 'createEdge failed'
      return
    }
    manualEdges.set(resp.edge.id, resp.edge)
    neighbourCache.delete(sourceId)
    neighbourCache.delete(targetId)
    reconcile()
  }

  async function removeEdge(edgeId: string): Promise<void> {
    await graphApi.initialise()
    const resp = await graphApi.deleteEdge(edgeId)
    if (!resp.success) {
      lastError.value = resp.message
      return
    }
    manualEdges.delete(edgeId)
    for (const cached of neighbourCache.values()) {
      const idx = cached.edges.findIndex(e => e.id === edgeId)
      if (idx !== -1)
        cached.edges.splice(idx, 1)
    }
    reconcile()
  }

  function setSelection(nodeId: string | null): void {
    selectedNodeId.value = nodeId
  }

  async function toggleShowAll(): Promise<void> {
    showAllNodes.value = !showAllNodes.value
    if (showAllNodes.value && allDocuments.value.length === 0) {
      await documentApi.initialise()
      const resp = await documentApi.searchDocuments({ pageSize: 10000 })
      allDocuments.value = resp.matches
      for (const doc of resp.matches) knownDocs.set(doc.id, doc)
    }
    reconcile()
  }

  function clear(): void {
    pinnedDoc.value = null
    expandedNodeIds.clear()
    neighbourCache.clear()
    manualEdges.clear()
    selectedNodeId.value = null
    lastError.value = null
    hopDepth.value = 1
    trail.length = 0
    anchoredNodeIds.clear()
    showAllNodes.value = false
    knownDocs.clear()
    graph.clear()
  }

  return {
    graph,
    // Reactive meta-state.
    pinnedDoc,
    expandedNodeIds,
    selectedNodeId,
    lastError,
    hopDepth,
    isExpandingDepth,
    trail,
    trailMaxLength,
    anchoredNodeIds,
    showAllNodes,
    // Actions.
    pinNode,
    pinNodeById,
    setHopDepth,
    toggleAnchor,
    isAnchored,
    toggleShowAll,
    expand,
    collapse,
    addEdge,
    removeEdge,
    setSelection,
    clear,
  }
})
