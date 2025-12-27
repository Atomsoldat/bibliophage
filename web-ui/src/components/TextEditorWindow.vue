<script setup lang="ts">
import { useDraggable } from '@vueuse/core'
import { useTemplateRef, computed, watch } from 'vue'
import TextEditorCard from '../components/TextEditorCard.vue'
import type { EditorWindowConfig } from '../composables/useEditorWindows'

// Props from global state
const props = defineProps<{
  window: EditorWindowConfig
}>()

// Events to update global state
const emit = defineEmits<{
  close: [windowId: string]
  minimize: [windowId: string]
  positionChange: [windowId: string, x: number, y: number]
  documentUpdate: [windowId: string, updates: { documentId?: string; title?: string; content?: string; isNew?: boolean }]
  bringToFront: [windowId: string]
}>()

const floatingEditorWindow = useTemplateRef('floatingEditorWindow')

// Initialize draggable with position from global state
const { x, y } = useDraggable(floatingEditorWindow, {
  initialValue: { x: props.window.x, y: props.window.y },
})

// Watch for drag position changes and emit to global state
watch([x, y], ([newX, newY]) => {
  emit('positionChange', props.window.id, newX, newY)
})

// Computed style with z-index from global state
const windowStyle = computed(() => ({
  position: 'fixed',
  left: `${x.value}px`,
  top: `${y.value}px`,
  zIndex: props.window.zIndex,
}))

function handleClose() {
  emit('close', props.window.id)
}

function handleMinimize() {
  emit('minimize', props.window.id)
}

function handleBringToFront() {
  emit('bringToFront', props.window.id)
}

// Handle document changes from the editor card
function handleDocumentUpdate(field: 'title' | 'content' | 'documentId' | 'isNew', value: string | boolean) {
  emit('documentUpdate', props.window.id, { [field]: value })
}

</script>

<template>
  <div
    ref="floatingEditorWindow"
    :style="windowStyle"
    class="w-[800px] max-w-[90vw]"
    @mousedown="handleBringToFront"
  >
    <!-- Menu Bar (draggable handle) -->
    <div class="flex items-center justify-between gap-4 p-2 bg-base-200 border border-base-300 rounded-t-lg cursor-move select-none">
      <!-- Document Title (Left) -->
      <div class="flex-1 font-semibold truncate">
        {{ window.title }}
      </div>

      <!-- Buttons (Right) -->
      <div class="flex gap-2 flex-shrink-0">
        <button
          class="btn btn-sm"
          @click.stop="handleMinimize"
          :title="window.isMinimized ? 'Restore' : 'Minimize'"
        >
          {{ window.isMinimized ? 'Restore' : 'Minimize' }}
        </button>
        <button
          class="btn btn-sm btn-error"
          @click.stop="handleClose"
          title="Close"
        >
          Close
        </button>
      </div>
    </div>

    <!-- Editor Content -->
    <div v-if="!window.isMinimized" class="w-full bg-base-100 border border-base-300 rounded-b-lg shadow-xl">
      <TextEditorCard
        :content="window.content"
        :title="window.title"
        :is-new="window.isNew"
        :document-id="window.documentId"
        @update:content="(val) => handleDocumentUpdate('content', val)"
        @update:title="(val) => handleDocumentUpdate('title', val)"
        @update:is-new="(val) => handleDocumentUpdate('isNew', val)"
        @update:document-id="(val) => handleDocumentUpdate('documentId', val)"
        icon="heroicons:document-text"
      />
    </div>
  </div>
</template>
