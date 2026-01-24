import type { Ref } from 'vue'
import { DocumentListItem, DocumentType, Document } from '../bibliophage/v1alpha3/document_pb.ts'
import type { MetadataEditFormData } from '../components/MetadataEditModal.vue'
import type { useDocumentApi } from './useDocumentApi.ts'

import { computed, ref } from 'vue'
import { Tag } from '../bibliophage/v1alpha3/common_pb.ts'
import { useLogger } from './useLogger.ts'

/**
 * Composable for bulk metadata editing of documents.
 * Encapsulates modal state, loading state, and the update logic.
 *
 * @param selectedIds - Reactive set of selected document IDs
 * @param documents - Reactive array of document list items (for pre-population)
 * @param api - Document API instance
 */
export function useBulkMetadataEdit(
  selectedIds: Ref<Set<string>>,
  documents: Ref<DocumentListItem[]>,
  api: ReturnType<typeof useDocumentApi>,
  onUpdateComplete?: () => void,
) {
  const logger = useLogger()

  const showModal = ref(false)

  // Loading state during update operations
  const loading = ref(false)

  // Computed: Get the initial document for pre-population when a single item is selected
  const initialDocument = computed<DocumentListItem | null>(() => {
    if (selectedIds.value.size !== 1) {
      return null
    }
    const selectedId = Array.from(selectedIds.value)[0]
    return documents.value.find(doc => doc.id === selectedId) || null
  })

  // Computed: Number of selected documents (for modal display)
  const selectedCount = computed(() => selectedIds.value.size)

  function openModal() {
    if (selectedIds.value.size === 0) {
      logger.warn('No documents selected for bulk edit')
      return
    }
    showModal.value = true
  }

  function closeModal() {
    showModal.value = false
  }

  // TODO: There should also be a way to append e.g. tags
  // rather than overwriting all tags
  // TODO: I think we are fetching the entire document here
  // This can probably be done more efficiently
  // perhaps we can filter out the document content on the server side
  async function handleUpdate(formData: MetadataEditFormData): Promise<void> {
    loading.value = true

    // Track results
    let successCount = 0
    let failureCount = 0
    const errors: string[] = []

    try {
      for (const id of selectedIds.value) {
        const response = await api.getDocument(id)
        if (!response.success || !response.document) {
          logger.error(`Failed to fetch document ${id}: ${response.message}`)
          errors.push(`${id}: ${response.message}`)
          failureCount++
          continue
        }
        const updatedDocument = response.document

        if (formData.systems) {
          updatedDocument.systems = formData.systems
        }
        if (formData.tags) {
          const tags: Tag[] = []
          for (const tagData of formData.tags) {
            const tag = new Tag()
            tag.name = tagData.name
            tag.values = tagData.values
            tags.push(tag)
          }
          updatedDocument.tags = tags
        }
        if (formData.type) {
          const enumValue = DocumentType[formData.type as keyof typeof DocumentType]
          if (enumValue !== undefined) {
            updatedDocument.type = enumValue
          }
        }

        const updateResponse = await api.updateDocument(updatedDocument)
        if (updateResponse.success) {
          successCount++
        }
        else {
          errors.push(`${updatedDocument.name}: ${updateResponse.message}`)
          failureCount++
        }
      }

      // Log summary
      if (successCount > 0) {
        logger.success(`Successfully updated ${successCount} document${successCount > 1 ? 's' : ''}`)
      }
      if (failureCount > 0) {
        logger.error(`Failed to update ${failureCount} document${failureCount > 1 ? 's' : ''}`)
        for (const err of errors) {
          logger.error(err)
        }
      }

      // Close modal and clear selection on any success
      if (successCount > 0) {
        showModal.value = false
        selectedIds.value.clear()
        onUpdateComplete?.()
      }
    }
    finally {
      loading.value = false
    }
  }

  return {
    // State
    showModal,
    loading,

    // Computed
    initialDocument,
    selectedCount,

    // Methods
    openModal,
    closeModal,
    handleUpdate,
  }
}

export type BulkMetadataEditComposable = ReturnType<typeof useBulkMetadataEdit>
