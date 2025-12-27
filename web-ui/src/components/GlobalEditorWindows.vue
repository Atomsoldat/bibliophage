<script setup lang="ts">
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
</script>

<template>
  <div class="global-editor-windows">
    <TextEditorWindow
      v-for="window in windows"
      :key="window.id"
      :window="window"
      @close="closeWindow"
      @minimize="toggleMinimize"
      @position-change="updatePosition"
      @document-update="updateDocument"
      @bring-to-front="bringToFront"
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
