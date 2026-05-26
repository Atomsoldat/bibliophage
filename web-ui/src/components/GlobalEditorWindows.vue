<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useLogger } from '../composables/useLogger'
import { useEditorWindowStore } from '../stores/editorWindows'
import { useDocumentStore } from '../stores/documents'
import TextEditorWindow from './TextEditorWindow.vue'

const editorWindows = useEditorWindowStore()
const documentStore = useDocumentStore()
const api = useDocumentApi()
const logger = useLogger()

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
  const window = editorWindows.getWindow(windowId)
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
        editorWindows.updateDocument(windowId, {
          documentId: response.document.id,
          isNew: false,
        })
        logger.success(`Document created: ${response.document.id}`)
        await documentStore.reload()
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
        await documentStore.reload()
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
  editorWindows.closeWindow(windowId)
  logger.info('Document discarded')
}
</script>

<template>
  <div class="global-editor-windows">
    <TextEditorWindow
      v-for="window in editorWindows.windows"
      v-bind:key="window.id"
      v-bind:ref="(el) => setEditorWindowRef(window.id, el)"
      v-bind:window="window"
      @close="editorWindows.closeWindow"
      @minimize="editorWindows.toggleMinimize"
      @position-change="editorWindows.updatePosition"
      @document-update="editorWindows.updateDocument"
      @bring-to-front="editorWindows.bringToFront"
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
