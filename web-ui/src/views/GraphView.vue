<script setup lang="ts">
import type { DocumentListItem } from '../utils/protoHelpers'
import { Icon } from '@iconify/vue'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import { storeToRefs } from 'pinia'
import Sigma from 'sigma'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import GraphSearchPanel from '../components/GraphSearchPanel.vue'
import { useGraphStore } from '../stores/graph'
import { useLogger } from '../composables/useLogger'

const store = useGraphStore()
const {
  pinnedDoc, selectedNodeId, expandedNodeIds, lastError, showAllNodes,
  hopDepth, isExpandingDepth, trail, anchoredNodeIds,
} = storeToRefs(store)
const {
  graph, pinNode, pinNodeById, expand, collapse, setSelection,
  addEdge, toggleShowAll, setHopDepth, toggleAnchor, isAnchored,
} = store

const logger = useLogger()
const containerRef = ref<HTMLDivElement | null>(null)
const rootRef = ref<HTMLDivElement | null>(null)

let sigma: Sigma | null = null
let layoutTimer: number | null = null

// Layout settings — these worked well for small graphs (≤ a few hundred
// nodes); revisit if/when scale grows. Reference:
// https://graphology.github.io/standard-library/layout-forceatlas2.html
const LAYOUT_ITERATIONS = 100
const LAYOUT_SETTINGS = { gravity: 1, scalingRatio: 10 }

function scheduleLayout(): void {
  if (layoutTimer !== null) {
    window.clearTimeout(layoutTimer)
  }
  // Debounce: structural changes often arrive in bursts (a full neighbourhood
  // arrives as N nodeAdded + M edgeAdded events). One layout pass per burst
  // is enough.
  layoutTimer = window.setTimeout(() => {
    if (graph.order > 0) {
      forceAtlas2.assign(graph, {
        iterations: LAYOUT_ITERATIONS,
        settings: LAYOUT_SETTINGS,
      })
    }
    layoutTimer = null
  }, 50)
}

// Double-Tab on a selected node triggers expansion. Single Tab is consumed
// so the browser doesn't shift focus out of the canvas mid-exploration.
let lastTabTime = 0
const DOUBLE_TAB_WINDOW_MS = 400

// Connect mode: when active, the next two node clicks form an edge.
// `connectFirstEndpoint` holds the first picked node id, if any.
const connectMode = ref(false)
const connectFirstEndpoint = ref<string | null>(null)

const connectBannerText = computed(() => {
  if (!connectMode.value) {
    return ''
  }
  return connectFirstEndpoint.value
    ? 'Click a second node to connect — or Esc to cancel.'
    : 'Click the first node to connect — or Esc to cancel.'
})

function toggleConnectMode(): void {
  connectMode.value = !connectMode.value
  connectFirstEndpoint.value = null
}

function cancelConnectMode(): void {
  connectMode.value = false
  connectFirstEndpoint.value = null
}

// Right-click context menu state.
const contextMenu = ref<{ x: number, y: number, nodeId: string } | null>(null)

function closeContextMenu(): void {
  contextMenu.value = null
}

function handleContextAction(action: 'pin' | 'anchor' | 'expand' | 'collapse', nodeId: string): void {
  closeContextMenu()
  switch (action) {
    case 'pin': void pinNodeById(nodeId); break
    case 'anchor': void toggleAnchor(nodeId); break
    case 'expand': void expand(nodeId); break
    case 'collapse': collapse(nodeId); break
  }
}

function handleKeyDown(event: KeyboardEvent): void {
  // Dismiss context menu on any key.
  if (contextMenu.value) {
    closeContextMenu()
  }

  if (event.key === 'Escape' && connectMode.value) {
    event.preventDefault()
    cancelConnectMode()
    return
  }

  // `A` toggles anchor on the selected node.
  if (event.key === 'a' || event.key === 'A') {
    if (selectedNodeId.value) {
      void toggleAnchor(selectedNodeId.value)
    }
    return
  }

  if (event.key !== 'Tab') {
    return
  }
  event.preventDefault()
  if (!selectedNodeId.value) {
    return
  }
  const now = Date.now()
  if (now - lastTabTime < DOUBLE_TAB_WINDOW_MS) {
    void pinNodeById(selectedNodeId.value)
    lastTabTime = 0
  }
  else {
    lastTabTime = now
  }
}

onMounted(() => {
  if (!containerRef.value) {
    return
  }

  sigma = new Sigma(graph, containerRef.value)

  sigma.on('clickNode', ({ node, event }) => {
    if (connectMode.value) {
      if (connectFirstEndpoint.value === null) {
        connectFirstEndpoint.value = node
        return
      }
      // Second click — only attempt the edge if it's a different node;
      // self-loops are rejected server-side anyway, but bailing here avoids
      // a wasted round-trip.
      if (node !== connectFirstEndpoint.value) {
        void addEdge(connectFirstEndpoint.value, node)
      }
      cancelConnectMode()
      return
    }
    // Shift+click collapses an expanded node — the pinned node ignores this
    // in the store, so no special-case here.
    if (event.original instanceof MouseEvent && event.original.shiftKey) {
      collapse(node)
      return
    }
    void pinNodeById(node)
  })

  sigma.on('rightClickNode', ({ node, event }) => {
    event.original.preventDefault()
    contextMenu.value = {
      x: (event.original as MouseEvent).clientX,
      y: (event.original as MouseEvent).clientY,
      nodeId: node,
    }
  })

  sigma.on('clickStage', () => {
    setSelection(null)
    closeContextMenu()
  })

  graph.on('nodeAdded', scheduleLayout)
  graph.on('nodeDropped', scheduleLayout)
  graph.on('edgeAdded', scheduleLayout)
  graph.on('edgeDropped', scheduleLayout)

  // Initial layout pass for any nodes already present (e.g. when navigating
  // away and back to /graph).
  scheduleLayout()

  // Focus the container so keyboard events land here without an extra click.
  rootRef.value?.focus()
})

onBeforeUnmount(() => {
  if (sigma) {
    sigma.kill()
    sigma = null
  }
  graph.off('nodeAdded', scheduleLayout)
  graph.off('nodeDropped', scheduleLayout)
  graph.off('edgeAdded', scheduleLayout)
  graph.off('edgeDropped', scheduleLayout)
  if (layoutTimer !== null) {
    window.clearTimeout(layoutTimer)
    layoutTimer = null
  }
})

watch(lastError, (err) => {
  if (err) {
    logger.error(`[GraphView] ${err}`)
  }
})

function handlePick(doc: DocumentListItem): void {
  void pinNode(doc)
}
</script>

<template>
  <div
    ref="rootRef"
    class="flex flex-col h-full focus:outline-none"
    tabindex="0"
    v-on:keydown="handleKeyDown"
  >
    <div class="flex justify-between items-baseline mb-2">
      <h1 class="text-2xl font-bold">
        Graph
      </h1>
      <div class="flex items-center gap-3">
        <div class="text-sm opacity-70">
          <template v-if="pinnedDoc">
            Pinned: <span class="font-mono">{{ pinnedDoc.name }}</span>
            <span class="ml-2">· {{ expandedNodeIds.size }} expanded</span>
          </template>
          <template v-else-if="showAllNodes">
            {{ graph.order }} node(s) loaded
          </template>
          <template v-else>
            No node pinned — search and click a result to start.
          </template>
        </div>

        <!-- Hop depth stepper -->
        <div class="join" v-bind:class="{ 'opacity-50 pointer-events-none': !pinnedDoc || isExpandingDepth }">
          <button class="btn btn-xs join-item" @click="setHopDepth(hopDepth - 1)" v-bind:disabled="hopDepth <= 1">
            −
          </button>
          <span class="btn btn-xs join-item no-animation cursor-default">{{ hopDepth }} hop{{ hopDepth > 1 ? 's' : '' }}</span>
          <button class="btn btn-xs join-item" @click="setHopDepth(hopDepth + 1)" v-bind:disabled="hopDepth >= 5">
            +
          </button>
        </div>

        <button
          type="button"
          class="btn btn-sm gap-1"
          v-bind:class="showAllNodes ? 'btn-accent' : 'btn-outline'"
          @click="toggleShowAll"
        >
          <Icon icon="mdi:dots-hexagon" />
          {{ showAllNodes ? 'Hide unconnected' : 'Show all' }}
        </button>
        <button
          type="button"
          class="btn btn-sm gap-1"
          v-bind:class="connectMode ? 'btn-warning' : 'btn-outline'"
          v-bind:disabled="!pinnedDoc"
          @click="toggleConnectMode"
        >
          <Icon icon="mdi:vector-polyline-plus" />
          {{ connectMode ? 'Cancel connect' : 'Connect' }}
        </button>
      </div>
    </div>

    <div
      v-if="connectMode"
      class="alert alert-info py-1 px-3 text-sm mb-2"
    >
      {{ connectBannerText }}
    </div>

    <!-- Trail breadcrumbs -->
    <div v-if="trail.length > 0" class="flex items-center gap-1 mb-1 flex-wrap">
      <span class="text-xs opacity-50 mr-1">Trail:</span>
      <button
        v-for="doc in trail"
        v-bind:key="doc.id"
        class="badge badge-sm badge-outline cursor-pointer gap-1"
        style="border-color: #a855f7; color: #a855f7;"
        @click="pinNode(doc)"
      >
        <Icon icon="mdi:map-marker-path" class="text-xs" />
        {{ doc.name }}
      </button>
    </div>

    <!-- Anchored nodes -->
    <div v-if="anchoredNodeIds.size > 0" class="flex items-center gap-1 mb-1 flex-wrap">
      <span class="text-xs opacity-50 mr-1">Anchored:</span>
      <span
        v-for="nodeId in anchoredNodeIds"
        v-bind:key="nodeId"
        class="badge badge-sm gap-1"
        style="background-color: #14b8a6; color: #fff; border: none;"
      >
        <Icon icon="mdi:anchor" class="text-xs" />
        {{ graph.hasNode(nodeId) ? graph.getNodeAttribute(nodeId, 'label') : nodeId }}
        <button class="ml-0.5 hover:opacity-70" @click="toggleAnchor(nodeId)">×</button>
      </span>
    </div>

    <div class="flex-1 flex gap-3 min-h-0">
      <aside class="w-80 shrink-0 overflow-hidden">
        <GraphSearchPanel @pick="handlePick" />
      </aside>

      <div
        ref="containerRef"
        class="flex-1 bg-base-200 rounded border border-base-300 min-h-[400px]"
      />
    </div>

    <!-- Right-click context menu -->
    <Teleport to="body">
      <div
        v-if="contextMenu"
        class="fixed z-[100] menu bg-base-200 rounded-box shadow-xl w-48 p-2"
        v-bind:style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      >
        <li>
          <button @click="handleContextAction('pin', contextMenu!.nodeId)">
            <Icon icon="mdi:pin" class="text-amber-500" />
            Pin
          </button>
        </li>
        <li>
          <button @click="handleContextAction('anchor', contextMenu!.nodeId)">
            <Icon
              v-bind:icon="isAnchored(contextMenu!.nodeId) ? 'mdi:anchor-off' : 'mdi:anchor'"
              class="text-teal-400"
            />
            {{ isAnchored(contextMenu!.nodeId) ? 'Unanchor' : 'Anchor' }}
          </button>
        </li>
        <li>
          <button @click="handleContextAction(expandedNodeIds.has(contextMenu!.nodeId) ? 'collapse' : 'expand', contextMenu!.nodeId)">
            <Icon
              v-bind:icon="expandedNodeIds.has(contextMenu!.nodeId) ? 'mdi:arrow-collapse-all' : 'mdi:arrow-expand-all'"
              class="text-blue-400"
            />
            {{ expandedNodeIds.has(contextMenu!.nodeId) ? 'Collapse' : 'Expand' }}
          </button>
        </li>
      </div>
    </Teleport>

    <div class="text-xs opacity-60 mt-2 flex gap-3 flex-wrap">
      <span><kbd class="kbd kbd-xs">click</kbd> pin</span>
      <span><kbd class="kbd kbd-xs">Shift+click</kbd> collapse</span>
      <span><kbd class="kbd kbd-xs">A</kbd> anchor/unanchor</span>
      <span><kbd class="kbd kbd-xs">right-click</kbd> context menu</span>
      <span><kbd class="kbd kbd-xs">drag</kbd> pan</span>
      <span><kbd class="kbd kbd-xs">wheel</kbd> zoom</span>
    </div>
  </div>
</template>
