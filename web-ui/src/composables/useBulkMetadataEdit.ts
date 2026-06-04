import type { MetadataEditFormData } from '../components/MetadataEditModal.vue'
import { computed, ref } from 'vue'

import { Tag } from '../bibliophage/v1alpha3/common_pb.ts'
import { DocumentType } from '../bibliophage/v1alpha3/document_pb.ts'
import { useDocumentStore } from '../stores/documents'
import { useDocumentApi } from './useDocumentApi.ts'
import { useLogger } from './useLogger.ts'

/**
 * Composable for bulk metadata editing of documents.
 * Reads selected IDs and document list from DocumentStore.
 */
export function useBulkMetadataEdit() {
  const logger = useLogger()
  const api = useDocumentApi()
  const documentStore = useDocumentStore()

  const showModal = ref(false)
  const loading = ref(false)

  const initialDocument = computed(() => {
    if (documentStore.selectedIds.size !== 1) {
      return null
    }
    const selectedId = Array.from(documentStore.selectedIds)[0]
    return documentStore.documents.find(doc => doc.id === selectedId) || null
  })

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

  // TODO: There should also be a way to append e.g. tags
  // rather than overwriting all tags
  // TODO: I think we are fetching the entire document here
  // This can probably be done more efficiently
  // perhaps we can filter out the document content on the server side
  async function handleUpdate(formData: MetadataEditFormData): Promise<void> {
    loading.value = true

    let successCount = 0
    let failureCount = 0
    const errors: string[] = []

    try {
      await api.initialise()
      for (const id of documentStore.selectedIds) {
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

      if (successCount > 0) {
        logger.success(`Successfully updated ${successCount} document${successCount > 1 ? 's' : ''}`)
      }
      if (failureCount > 0) {
        logger.error(`Failed to update ${failureCount} document${failureCount > 1 ? 's' : ''}`)
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
    initialDocument,
    selectedCount,
    openModal,
    closeModal,
    handleUpdate,
  }
}

export type BulkMetadataEditComposable = ReturnType<typeof useBulkMetadataEdit>
