<script setup lang="ts">
import type { EditorWindowConfig } from '../composables/useEditorWindows'
import { useDraggable } from '@vueuse/core'
import { computed, useTemplateRef, watch } from 'vue'
import TextEditorCard from '../components/TextEditorCard.vue'

const props = defineProps<{
  window: EditorWindowConfig
}>()

const emit = defineEmits<{
  close: [windowId: string]
  minimize: [windowId: string]
  positionChange: [windowId: string, x: number, y: number]
  documentUpdate: [windowId: string, updates: { documentId?: string, title?: string, content?: string, isNew?: boolean }]
  bringToFront: [windowId: string]
  save: [windowId: string]
  discard: [windowId: string]
}>()

// Draggable window setup
const floatingEditorWindow = useTemplateRef('floatingEditorWindow')
const { x, y } = useDraggable(floatingEditorWindow, {
  initialValue: { x: props.window.x, y: props.window.y },
})

// Sync drag position back to global state
watch([x, y], ([newX, newY]) => {
  emit('positionChange', props.window.id, newX, newY)
})

// Combine draggable position with z-index from global state
const windowStyle = computed(() => ({
  position: 'fixed',
  left: `${x.value}px`,
  top: `${y.value}px`,
  zIndex: props.window.zIndex,
}))

// Event handlers
function handleClose() {
  emit('close', props.window.id)
}

function handleMinimize() {
  emit('minimize', props.window.id)
}

function handleBringToFront() {
  emit('bringToFront', props.window.id)
}

function handleDocumentUpdate(field: 'title' | 'content' | 'documentId' | 'isNew', value: string | boolean) {
  emit('documentUpdate', props.window.id, { [field]: value })
}

function handleSave() {
  emit('save', props.window.id)
}

function handleDiscard() {
  emit('discard', props.window.id)
}
</script>

<template>
  <div
    ref="floatingEditorWindow"
    v-bind:style="windowStyle"
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
          v-bind:title="window.isMinimized ? 'Restore' : 'Minimize'"
          @click.stop="handleMinimize"
        >
          {{ window.isMinimized ? 'Restore' : 'Minimize' }}
        </button>
        <button
          class="btn btn-sm btn-error"
          title="Close"
          @click.stop="handleClose"
        >
          Close
        </button>
      </div>
    </div>

    <!-- Editor Content -->
    <div v-if="!window.isMinimized" class="w-full bg-base-100 border border-base-300 rounded-b-lg shadow-xl">
      <TextEditorCard
        v-bind:content="window.content"
        v-bind:title="window.title"
        v-bind:is-new="window.isNew"
        v-bind:document-id="window.documentId"
        icon="heroicons:document-text"
        @update:content="(val) => handleDocumentUpdate('content', val)"
        @update:title="(val) => handleDocumentUpdate('title', val)"
        @update:is-new="(val) => handleDocumentUpdate('isNew', val)"
        @update:document-id="(val) => handleDocumentUpdate('documentId', val)"
      />

      <!-- Action Buttons -->
      <div class="flex justify-between p-4 border-t border-base-300">
        <button
          type="button"
          class="btn btn-primary btn-lg w-fit gap-2"
          @click.stop="handleSave"
        >
          <p>Save</p>
        </button>
        <button
          type="button"
          class="btn btn-error btn-lg w-fit gap-2"
          @click.stop="handleDiscard"
        >
          <p>Discard</p>
        </button>
      </div>
    </div>
  </div>
</template>
