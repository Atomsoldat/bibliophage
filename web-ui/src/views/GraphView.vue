<script setup lang="ts">
import type { DocumentListItem } from '../utils/protoHelpers'
import { Icon } from '@iconify/vue'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import Sigma from 'sigma'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import GraphSearchPanel from '../components/GraphSearchPanel.vue'
import { useGraphStore } from '../composables/useGraphStore'
import { useLogger } from '../composables/useLogger'

const {
  graph,
  pinnedDoc,
  selectedNodeId,
  expandedNodeIds,
  lastError,
  pinNode,
  expand,
  collapse,
  setSelection,
  addEdge,
} = useGraphStore()

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

function handleKeyDown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && connectMode.value) {
    event.preventDefault()
    cancelConnectMode()
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
    void expand(selectedNodeId.value)
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
    setSelection(node)
  })

  sigma.on('clickStage', () => setSelection(null))

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
          <template v-else>
            No node pinned — search and click a result to start.
          </template>
        </div>
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

    <div class="flex-1 flex gap-3 min-h-0">
      <aside class="w-80 shrink-0 overflow-hidden">
        <GraphSearchPanel @pick="handlePick" />
      </aside>

      <div
        ref="containerRef"
        class="flex-1 bg-base-200 rounded border border-base-300 min-h-[400px]"
      />
    </div>

    <div class="text-xs opacity-60 mt-2 flex gap-3 flex-wrap">
      <span><kbd class="kbd kbd-xs">click</kbd> select</span>
      <span><kbd class="kbd kbd-xs">double Tab</kbd> expand selected</span>
      <span><kbd class="kbd kbd-xs">Shift+click</kbd> collapse</span>
      <span><kbd class="kbd kbd-xs">drag</kbd> pan</span>
      <span><kbd class="kbd kbd-xs">wheel</kbd> zoom</span>
    </div>
  </div>
</template>
