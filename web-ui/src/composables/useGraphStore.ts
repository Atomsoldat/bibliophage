/**
 * In-memory view-model for the graph editor.
 *
 * Holds a graphology Graph instance (rendered by sigma in GraphView.vue) plus
 * meta-state (pinned node, which nodes have had their neighbourhoods fetched,
 * the currently selected node, and the most recent error).
 *
 * Mental model:
 *   - Pinning a node clears the view and shows that node plus its one-hop
 *     neighbourhood (the "inner circle").
 *   - Expanding a node (e.g. double-Tab in the view) fetches its neighbours
 *     and folds them into the visible graph.
 *   - Collapsing a node removes nodes/edges that are only reachable through
 *     that expansion. Implementation-wise we keep a cache of every fetched
 *     neighbourhood and recompute the visible set on every state change.
 *
 * Why module-level singletons: the view-model is a single shared state for
 * the whole /graph route; mounting and unmounting the view shouldn't reset
 * exploration progress, but switching routes and coming back should. The
 * `clear()` method resets when needed.
 */

import type { DocumentListItem } from '../bibliophage/v1alpha3/document_pb'
import type { Edge } from '../bibliophage/v1alpha3/graph_pb'
import Graph from 'graphology'
import { reactive, ref } from 'vue'
import { useGraphApi } from './useGraphApi'

// Sigma listens to graphology events directly — we deliberately do NOT wrap
// the graph in a Vue ref. Vue tracks the meta-state below; sigma tracks the
// graph contents.
const graph = new Graph({ type: 'mixed', multi: false })

const pinnedDoc = ref<DocumentListItem | null>(null)
const expandedNodeIds = reactive(new Set<string>())
const selectedNodeId = ref<string | null>(null)
const lastError = ref<string | null>(null)

interface NeighbourhoodCacheEntry {
  neighbours: DocumentListItem[]
  edges: Edge[]
}

const neighbourCache = new Map<string, NeighbourhoodCacheEntry>()

// Edges that were just created via addEdge() and haven't yet appeared in
// any neighbourhood cache. Reconcile includes them as long as both
// endpoints are visible. They get superseded the next time we refetch
// either endpoint's neighbourhood.
const manualEdges = new Map<string, Edge>()

// Visual constants — kept here so the view stays declarative.
const NODE_BASE_SIZE = 10
const PINNED_NODE_SIZE = 16
const PINNED_NODE_COLOR = '#f59e0b'
const NEIGHBOUR_NODE_COLOR = '#3b82f6'
const EDGE_COLOR = '#9ca3af'

function ensureNode(doc: DocumentListItem): void {
  const isPinned = doc.id === pinnedDoc.value?.id
  if (graph.hasNode(doc.id)) {
    graph.setNodeAttribute(doc.id, 'label', doc.name)
    graph.setNodeAttribute(doc.id, 'size', isPinned ? PINNED_NODE_SIZE : NODE_BASE_SIZE)
    graph.setNodeAttribute(doc.id, 'color', isPinned ? PINNED_NODE_COLOR : NEIGHBOUR_NODE_COLOR)
    return
  }
  // Sigma requires x/y; the force-atlas2 pass in the view refines them.
  graph.addNode(doc.id, {
    label: doc.name,
    x: Math.random(),
    y: Math.random(),
    size: isPinned ? PINNED_NODE_SIZE : NODE_BASE_SIZE,
    color: isPinned ? PINNED_NODE_COLOR : NEIGHBOUR_NODE_COLOR,
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

/**
 * Recompute the visible subgraph from pinnedDoc + expandedNodeIds + caches.
 *
 * Implemented as a diff against the current graphology graph rather than a
 * clear-and-rebuild, so node positions survive across expand/collapse.
 */
function reconcile(): void {
  if (!pinnedDoc.value) {
    graph.clear()
    return
  }

  const visibleNodes = new Map<string, DocumentListItem>()
  visibleNodes.set(pinnedDoc.value.id, pinnedDoc.value)
  for (const expandedId of expandedNodeIds) {
    const cached = neighbourCache.get(expandedId)
    if (!cached) {
      continue
    }
    for (const neighbour of cached.neighbours) {
      visibleNodes.set(neighbour.id, neighbour)
    }
  }

  const visibleEdges = new Map<string, Edge>()
  for (const expandedId of expandedNodeIds) {
    const cached = neighbourCache.get(expandedId)
    if (!cached) {
      continue
    }
    for (const edge of cached.edges) {
      if (visibleNodes.has(edge.nodeA) && visibleNodes.has(edge.nodeB)) {
        visibleEdges.set(edge.id, edge)
      }
    }
  }
  for (const [id, edge] of manualEdges) {
    if (visibleNodes.has(edge.nodeA) && visibleNodes.has(edge.nodeB)) {
      visibleEdges.set(id, edge)
    }
  }

  // Drop stale graph entries first (graphology cascades node→edge drops,
  // but we want explicit control over edge survival).
  for (const nodeId of [...graph.nodes()]) {
    if (!visibleNodes.has(nodeId)) {
      graph.dropNode(nodeId)
    }
  }
  for (const edgeKey of [...graph.edges()]) {
    if (!visibleEdges.has(edgeKey)) {
      graph.dropEdge(edgeKey)
    }
  }

  for (const [, doc] of visibleNodes) {
    ensureNode(doc)
  }
  for (const [, edge] of visibleEdges) {
    ensureEdge(edge)
  }
}

export function useGraphStore() {
  const api = useGraphApi()

  /** Pin a document as the centre of the view. Clears prior exploration. */
  async function pinNode(doc: DocumentListItem): Promise<void> {
    await api.initialise()
    pinnedDoc.value = doc
    expandedNodeIds.clear()
    neighbourCache.clear()
    manualEdges.clear()
    graph.clear()
    selectedNodeId.value = null
    lastError.value = null
    await expand(doc.id)
  }

  /** Fetch a node's neighbourhood (if not cached) and fold it into the view. */
  async function expand(nodeId: string): Promise<void> {
    if (expandedNodeIds.has(nodeId)) {
      return
    }
    if (!neighbourCache.has(nodeId)) {
      const resp = await api.getNeighbours(nodeId)
      if (!resp.success) {
        lastError.value = resp.message
        return
      }
      neighbourCache.set(nodeId, {
        neighbours: [...resp.neighbours],
        edges: [...resp.edges],
      })
    }
    expandedNodeIds.add(nodeId)
    reconcile()
  }

  /**
   * Hide a previously-expanded node's neighbourhood. The pinned node cannot
   * be collapsed — use pinNode() or clear() to leave the view.
   */
  function collapse(nodeId: string): void {
    if (nodeId === pinnedDoc.value?.id) {
      return
    }
    if (!expandedNodeIds.has(nodeId)) {
      return
    }
    expandedNodeIds.delete(nodeId)
    reconcile()
  }

  async function addEdge(sourceId: string, targetId: string): Promise<void> {
    await api.initialise()
    const resp = await api.createEdge(sourceId, targetId)
    if (!resp.success || !resp.edge) {
      lastError.value = resp.message || 'createEdge failed'
      return
    }
    manualEdges.set(resp.edge.id, resp.edge)
    // The next expansion of either endpoint should pick up the new edge
    // from the server. Drop their caches so the manual-edges fallback
    // isn't relied on indefinitely.
    neighbourCache.delete(sourceId)
    neighbourCache.delete(targetId)
    reconcile()
  }

  async function removeEdge(edgeId: string): Promise<void> {
    await api.initialise()
    const resp = await api.deleteEdge(edgeId)
    if (!resp.success) {
      lastError.value = resp.message
      return
    }
    manualEdges.delete(edgeId)
    for (const cached of neighbourCache.values()) {
      const idx = cached.edges.findIndex((edge) => edge.id === edgeId)
      if (idx !== -1) {
        cached.edges.splice(idx, 1)
      }
    }
    reconcile()
  }

  function setSelection(nodeId: string | null): void {
    selectedNodeId.value = nodeId
  }

  function clear(): void {
    pinnedDoc.value = null
    expandedNodeIds.clear()
    neighbourCache.clear()
    manualEdges.clear()
    selectedNodeId.value = null
    lastError.value = null
    graph.clear()
  }

  return {
    // Sigma reads this directly.
    graph,
    // Reactive meta-state.
    pinnedDoc,
    expandedNodeIds,
    selectedNodeId,
    lastError,
    // Operations.
    pinNode,
    expand,
    collapse,
    addEdge,
    removeEdge,
    setSelection,
    clear,
  }
}
