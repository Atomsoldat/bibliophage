<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useDocumentTableRefresh } from '../composables/useDocumentTableRefresh.ts'
import { useEditorWindows } from '../composables/useEditorWindows'
import { useLogger } from '../composables/useLogger'
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
const logger = useLogger()
const { triggerRefresh } = useDocumentTableRefresh()

// Store refs to editor window components
const editorWindowRefs = ref<Map<string, InstanceType<typeof TextEditorWindow>>>(new Map())

function setEditorWindowRef(windowId: string, el: any) {
  if (el) {
    editorWindowRefs.value.set(windowId, el)
  }
  else {
    editorWindowRefs.value.delete(windowId)
  }
}

// Initialize API on component mount
onMounted(async () => {
  try {
    await api.initialise()
    console.log('[GlobalEditorWindows] API initialized successfully')
  }
  catch (error) {
    logger.error(`Failed to initialize API: ${(error as Error).message}`)
  }
})

async function handleSave(windowId: string) {
  const window = getWindow(windowId)
  if (!window) {
    logger.error('Window not found')
    return
  }

  try {
    if (window.isNew) {
      // Import necessary types for creating new documents
      const { DocumentType, SourceType } = await import('../bibliophage/v1alpha3/document_pb.ts')

      const response = await api.storeDocument({
        name: window.title,
        content: window.content,
        // Provide required fields with sensible defaults
        systems: ['General'], // Default system - user can change via bulk edit later
        type: DocumentType.NOTE, // Default to NOTE for journal entries
        sourceType: SourceType.GM_NOTES, // Default source type
        tags: [], // Empty tags array
      })
      if (response?.success && response.document) {
        updateDocument(windowId, {
          documentId: response.document.id,
          isNew: false,
        })
        logger.success(`Document created: ${response.document.id}`)
        // Trigger journal list refresh to fetch new document from backend
        triggerRefresh()
        // Switch to preview mode after successful save
        editorWindowRefs.value.get(windowId)?.switchToPreview()
      }
      else {
        // Handle save failure
        logger.error(`Failed to create document: ${response?.message || 'Unknown error'}`)
      }
    }
    else {
      const response = await api.updateDocument({
        id: window.documentId,
        name: window.title,
        content: window.content,
      })
      if (response?.success) {
        logger.success('Document updated')
        // Trigger journal list refresh to fetch updated document from backend
        triggerRefresh()
        // Switch to preview mode after successful save
        editorWindowRefs.value.get(windowId)?.switchToPreview()
      }
      else {
        // Handle update failure
        logger.error(`Failed to update document: ${response?.message || 'Unknown error'}`)
      }
    }
  }
  catch (error) {
    logger.error(`Error while saving document: ${(error as Error).message}`)
  }
}

function handleDiscard(windowId: string) {
  // TODO: Add confirmation dialog for unsaved changes
  closeWindow(windowId)
  logger.info('Document discarded')
}
</script>

<template>
  <div class="global-editor-windows">
    <TextEditorWindow
      v-for="window in windows"
      v-bind:key="window.id"
      v-bind:ref="(el) => setEditorWindowRef(window.id, el)"
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
