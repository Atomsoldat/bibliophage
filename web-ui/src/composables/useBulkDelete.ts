import { computed, ref } from 'vue'
import { useDocumentApi } from './useDocumentApi.ts'
import { useDocumentStore } from '../stores/documents'
import { useLogger } from './useLogger.ts'

/**
 * Composable for single and bulk deletion of documents.
 * Reads selected IDs from DocumentStore.
 */
export function useBulkDelete() {
  const logger = useLogger()
  const api = useDocumentApi()
  const documentStore = useDocumentStore()

  const showModal = ref(false)
  const loading = ref(false)

  const selectedCount = computed(() => documentStore.selectedIds.size)

  const selectedDocumentNames = computed(() => {
    return documentStore.documents
      .filter(doc => documentStore.selectedIds.has(doc.id))
      .map(doc => doc.name)
  })

  function openModal() {
    if (documentStore.selectedIds.size === 0) {
      logger.warn('No documents selected for deletion')
      return
    }
    showModal.value = true
  }

  function closeModal() {
    showModal.value = false
  }

  async function handleDelete(): Promise<void> {
    loading.value = true

    let successCount = 0
    let failureCount = 0
    const errors: string[] = []

    try {
      await api.initialise()

      for (const id of documentStore.selectedIds) {
        try {
          const response = await api.deleteDocument(id)
          if (response.success) {
            successCount++
          }
          else {
            errors.push(`${id}: ${response.message}`)
            failureCount++
          }
        }
        catch (error) {
          errors.push(`${id}: ${(error as Error).message}`)
          failureCount++
        }
      }

      if (successCount > 0) {
        logger.success(`Deleted ${successCount} document${successCount > 1 ? 's' : ''}`)
      }
      if (failureCount > 0) {
        logger.error(`Failed to delete ${failureCount} document${failureCount > 1 ? 's' : ''}`)
        for (const err of errors) {
          logger.error(err)
        }
      }

      if (successCount > 0) {
        showModal.value = false
        documentStore.selectedIds.clear()
        await documentStore.reload()
      }
    }
    finally {
      loading.value = false
    }
  }

  return {
    showModal,
    loading,
    selectedCount,
    selectedDocumentNames,
    openModal,
    closeModal,
    handleDelete,
  }
}

export type BulkDeleteComposable = ReturnType<typeof useBulkDelete>
