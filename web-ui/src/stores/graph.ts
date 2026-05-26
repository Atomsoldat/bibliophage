/**
 * Pinia store for the graph editor view-model.
 *
 * Holds a graphology Graph instance (rendered by Sigma in GraphView.vue) plus
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
 * The graphology Graph is marked raw — Sigma subscribes to graphology's own
 * event system, so Vue must not proxy it.
 */

import type { DocumentListItem } from '../bibliophage/v1alpha3/document_pb'
import type { Edge } from '../bibliophage/v1alpha3/graph_pb'
import Graph from 'graphology'
import { defineStore } from 'pinia'
import { markRaw, reactive, ref } from 'vue'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useGraphApi } from '../composables/useGraphApi'

// Visual constants — kept here so the view stays declarative.
const NODE_BASE_SIZE = 10
const PINNED_NODE_SIZE = 16
const UNCONNECTED_NODE_SIZE = 6
const PINNED_NODE_COLOR = '#f59e0b'
const NEIGHBOUR_NODE_COLOR = '#3b82f6'
const UNCONNECTED_NODE_COLOR = '#6b7280'
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

  const pinnedDoc = ref<DocumentListItem | null>(null)
  const expandedNodeIds = reactive(new Set<string>())
  const selectedNodeId = ref<string | null>(null)
  const lastError = ref<string | null>(null)

  // "Show all" mode — displays every document as a node, even those with
  // no edges. Useful for seeing the full picture and spotting unconnected
  // documents. Also a good canary for performance issues.
  const showAllNodes = ref(false)
  const allDocuments = ref<DocumentListItem[]>([])

  const neighbourCache = new Map<string, NeighbourhoodCacheEntry>()

  // Edges created via addEdge() that haven't yet appeared in any
  // neighbourhood cache. Reconcile includes them as long as both
  // endpoints are visible.
  const manualEdges = new Map<string, Edge>()

  // ── graph helpers ────────────────────────────────────────────────

  function nodeAppearance(doc: DocumentListItem, isConnected: boolean): { size: number, color: string } {
    if (doc.id === pinnedDoc.value?.id) {
      return { size: PINNED_NODE_SIZE, color: PINNED_NODE_COLOR }
    }
    if (isConnected) {
      return { size: NODE_BASE_SIZE, color: NEIGHBOUR_NODE_COLOR }
    }
    return { size: UNCONNECTED_NODE_SIZE, color: UNCONNECTED_NODE_COLOR }
  }

  function ensureNode(doc: DocumentListItem, isConnected = true): void {
    const { size, color } = nodeAppearance(doc, isConnected)
    if (graph.hasNode(doc.id)) {
      graph.setNodeAttribute(doc.id, 'label', doc.name)
      graph.setNodeAttribute(doc.id, 'size', size)
      graph.setNodeAttribute(doc.id, 'color', color)
      return
    }
    // Sigma requires x/y; the force-atlas2 pass in the view refines them.
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

  /**
   * Recompute the visible subgraph from pinnedDoc + expandedNodeIds + caches.
   *
   * Implemented as a diff against the current graphology graph rather than a
   * clear-and-rebuild, so node positions survive across expand/collapse.
   */
  function reconcile(): void {
    // Connected nodes: pinned doc + expanded neighbourhoods.
    const connectedNodes = new Map<string, DocumentListItem>()
    if (pinnedDoc.value) {
      connectedNodes.set(pinnedDoc.value.id, pinnedDoc.value)
    }
    for (const expandedId of expandedNodeIds) {
      const cached = neighbourCache.get(expandedId)
      if (!cached) {
        continue
      }
      for (const neighbour of cached.neighbours) {
        connectedNodes.set(neighbour.id, neighbour)
      }
    }

    // All visible nodes = connected nodes + (optionally) every document.
    const visibleNodes = new Map<string, DocumentListItem>(connectedNodes)
    if (showAllNodes.value) {
      for (const doc of allDocuments.value) {
        if (!visibleNodes.has(doc.id)) {
          visibleNodes.set(doc.id, doc)
        }
      }
    }

    // Edges: only between visible nodes.
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

    // Drop stale graph entries first.
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
      ensureNode(doc, connectedNodes.has(doc.id))
    }
    for (const [, edge] of visibleEdges) {
      ensureEdge(edge)
    }
  }

  // ── public actions ───────────────────────────────────────────────

  /** Pin a document as the centre of the view. Clears prior exploration. */
  async function pinNode(doc: DocumentListItem): Promise<void> {
    await graphApi.initialise()
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
      const resp = await graphApi.getNeighbours(nodeId)
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
    await graphApi.initialise()
    const resp = await graphApi.createEdge(sourceId, targetId)
    if (!resp.success || !resp.edge) {
      lastError.value = resp.message || 'createEdge failed'
      return
    }
    manualEdges.set(resp.edge.id, resp.edge)
    // Drop caches so the next expansion picks up the new edge from the server.
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

  async function toggleShowAll(): Promise<void> {
    showAllNodes.value = !showAllNodes.value
    if (showAllNodes.value && allDocuments.value.length === 0) {
      await documentApi.initialise()
      const resp = await documentApi.searchDocuments({ pageSize: 10000 })
      allDocuments.value = resp.matches
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
    showAllNodes.value = false
    graph.clear()
  }

  return {
    // Sigma reads this directly — not reactive, not proxied.
    graph,
    // Reactive meta-state.
    pinnedDoc,
    expandedNodeIds,
    selectedNodeId,
    lastError,
    showAllNodes,
    // Actions.
    pinNode,
    toggleShowAll,
    expand,
    collapse,
    addEdge,
    removeEdge,
    setSelection,
    clear,
  }
})
