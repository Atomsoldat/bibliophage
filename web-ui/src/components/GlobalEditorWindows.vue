<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppConsole } from '../composables/useAppConsole'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useEditorWindows } from '../composables/useEditorWindows'
import { useJournalRefresh } from '../composables/useJournalRefresh'
import TextEditorWindow from './TextEditorWindow.vue'

const {
  windows,
  closeWindow,
  toggleMinimize,
  updatePosition,
  updateDocument,
  bringToFront,
  getWindow,
} = useEditorWindows()

const api = useDocumentApi()
const { log } = useAppConsole()
const { triggerRefresh } = useJournalRefresh()

// Initialize API on component mount
onMounted(async () => {
  try {
    await api.initialise()
    console.log('[GlobalEditorWindows] API initialized successfully')
  }
  catch (error) {
    log(`Failed to initialize API: ${(error as Error).message}`, 'error')
  }
})

async function handleSave(windowId: string) {
  const window = getWindow(windowId)
  if (!window) {
    log('Window not found', 'error')
    return
  }

  try {
    if (window.isNew) {
      const response = await api.storeDocument({
        name: window.title,
        content: window.content,
      })
      if (response?.success && response.document) {
        updateDocument(windowId, {
          documentId: response.document.id,
          isNew: false,
        })
        log(`Document created: ${response.document.id}`, 'success')
        // Trigger journal list refresh to fetch new document from backend
        triggerRefresh()
      }
    }
    else {
      const response = await api.updateDocument({
        id: window.documentId,
        name: window.title,
        content: window.content,
      })
      if (response?.success) {
        log('Document updated', 'success')
        // Trigger journal list refresh to fetch updated document from backend
        triggerRefresh()
      }
    }
  }
  catch (error) {
    log(`Error while saving document: ${(error as Error).message}`, 'error')
  }
}

function handleDiscard(windowId: string) {
  // TODO: Add confirmation dialog for unsaved changes
  closeWindow(windowId)
  log('Document discarded', 'info')
}
</script>

<template>
  <div class="global-editor-windows">
    <TextEditorWindow
      v-for="window in windows"
      v-bind:key="window.id"
      v-bind:window="window"
      @close="closeWindow"
      @minimize="toggleMinimize"
      @position-change="updatePosition"
      @document-update="updateDocument"
      @bring-to-front="bringToFront"
      @save="handleSave"
      @discard="handleDiscard"
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
