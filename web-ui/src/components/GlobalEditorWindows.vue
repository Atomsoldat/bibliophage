<script setup lang="ts">
import { watch } from 'vue'
import { useEditorWindows } from '../composables/useEditorWindows'
import TextEditorWindow from './TextEditorWindow.vue'

const {
  windows,
  closeWindow,
  toggleMinimize,
  updatePosition,
  updateDocument,
  bringToFront,
} = useEditorWindows()

// Debug: watch for window changes
watch(windows, (newWindows) => {
  console.log('[GlobalEditorWindows] Windows changed:', newWindows.length, newWindows)
}, { deep: true, immediate: true })

function handleClose(windowId: string) {
  closeWindow(windowId)
}

function handleMinimize(windowId: string) {
  toggleMinimize(windowId)
}

function handlePositionChange(windowId: string, x: number, y: number) {
  updatePosition(windowId, x, y)
}

function handleDocumentUpdate(windowId: string, updates: {
  documentId?: string
  title?: string
  content?: string
  isNew?: boolean
}) {
  updateDocument(windowId, updates)
}

function handleBringToFront(windowId: string) {
  bringToFront(windowId)
}
</script>

<template>
  <!-- Render all active editor windows -->
  <div class="global-editor-windows">
    <!-- Debug: Show window count -->
    <div v-if="windows.length > 0" class="fixed top-4 right-4 bg-red-500 text-white px-2 py-1 rounded text-xs z-[9999]">
      DEBUG: {{ windows.length }} windows
    </div>

    <TextEditorWindow
      v-for="window in windows"
      :key="window.id"
      :window="window"
      @close="handleClose"
      @minimize="handleMinimize"
      @position-change="handlePositionChange"
      @document-update="handleDocumentUpdate"
      @bring-to-front="handleBringToFront"
    />
  </div>
</template>

<style scoped>
.global-editor-windows {
  /* Container for all floating windows - doesn't interfere with layout */
  pointer-events: none;
}

.global-editor-windows > * {
  /* Re-enable pointer events for actual windows */
  pointer-events: auto;
}
</style>
