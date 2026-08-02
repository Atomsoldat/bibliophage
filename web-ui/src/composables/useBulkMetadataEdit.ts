import type { Tag } from '../bibliophage/v1alpha3/tag_pb.ts'
import { computed, ref } from 'vue'

import { useDocumentStore } from '../stores/documents'
import { useDocumentApi } from './useDocumentApi.ts'
import { useLogger } from './useLogger.ts'

export interface MetadataEditFormData {
  tagsToAdd: Tag[]
  tagsToRemove: Tag[]
}

/**
 * Composable for bulk metadata editing of documents.
 * Reads selected IDs from DocumentStore, applies each added/removed tag to
 * every selected document in a single AssignTagValues/DeleteTagValues call.
 */
export function useBulkMetadataEdit() {
  const logger = useLogger()
  const api = useDocumentApi()
  const documentStore = useDocumentStore()

  const showModal = ref(false)
  const loading = ref(false)

  const selectedCount = computed(() => documentStore.selectedIds.size)

  function openModal() {
    if (documentStore.selectedIds.size === 0) {
      logger.warn('No documents selected for bulk edit')
      return
    }
    showModal.value = true
  }

  function closeModal() {
    showModal.value = false
  }

  async function handleUpdate(formData: MetadataEditFormData): Promise<void> {
    if (formData.tagsToAdd.length === 0 && formData.tagsToRemove.length === 0) {
      logger.warn('No tag changes to apply')
      return
    }

    loading.value = true
    const documentIds = Array.from(documentStore.selectedIds)
    let successCount = 0
    let failureCount = 0
    const errors: string[] = []

    try {
      await api.initialise()

      for (const tag of formData.tagsToAdd) {
        const response = await api.assignTagValue(documentIds, tag.id, tag.values.map(v => v.value))
        if (response.success) {
          successCount++
        }
        else {
          failureCount++
          errors.push(`${tag.name}: ${response.message}`)
        }
      }

      for (const tag of formData.tagsToRemove) {
        const response = await api.removeTagValue(documentIds, tag.id, tag.values.map(v => v.value))
        if (response.success) {
          successCount++
        }
        else {
          failureCount++
          errors.push(`${tag.name}: ${response.message}`)
        }
      }

      if (successCount > 0) {
        logger.success(`Updated tags on ${documentIds.length} document${documentIds.length > 1 ? 's' : ''}`)
      }
      if (failureCount > 0) {
        logger.error(`Failed to apply ${failureCount} tag change${failureCount > 1 ? 's' : ''}`)
        for (const err of errors) {
          logger.error(err)
        }
      }

      if (successCount > 0 && failureCount === 0) {
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
    openModal,
    closeModal,
    handleUpdate,
  }
}

export type BulkMetadataEditComposable = ReturnType<typeof useBulkMetadataEdit>
