<script setup lang="ts">
import type { DocumentListItem } from '../bibliophage/v1alpha3/document_pb.ts'

import type { DocumentBasicFilterValue } from '../components/DocumentBasicFilter.vue'
import type { MetadataEditFormData } from '../components/MetadataEditModal.vue'

import { Icon } from '@iconify/vue'
import { onBeforeMount, ref } from 'vue'
import { SortOrder } from '../bibliophage/v1alpha3/common_pb.ts'
import { DocumentFilter, DocumentType, SearchDocumentsRequest } from '../bibliophage/v1alpha3/document_pb.ts'
import ChunkEditorModal from '../components/ChunkEditorModal.vue'
import DocumentBasicFilter from '../components/DocumentBasicFilter.vue'
import DocumentNewEntryButton from '../components/DocumentNewEntryButton.vue'
import DocumentTable from '../components/DocumentTable.vue'
import DocumentTypeFilter from '../components/DocumentTypeFilter.vue'
import MetadataEditModal from '../components/MetadataEditModal.vue'
import { useDocumentApi } from '../composables/useDocumentApi.ts'
import { useDocumentTableRefresh } from '../composables/useDocumentTableRefresh.ts'
import { useEditorWindows } from '../composables/useEditorWindows.ts'
import { useLogger } from '../composables/useLogger.ts'

const logger = useLogger()
const { openWindow } = useEditorWindows()
const { onRefreshTriggered } = useDocumentTableRefresh()

const api = useDocumentApi()

const documents = ref([] as DocumentListItem[])
const loading = ref(false)
const selectedIds = ref<Set<string | number>>(new Set())

// Bulk edit modal state
const showMetadataEditModal = ref(false)
const bulkEditLoading = ref(false)

// Embed modal state
const showEmbedModal = ref(false)
const embedDocumentId = ref<string | null>(null)

// Search filter parameters
const basicFilters = ref<DocumentBasicFilterValue>({
  nameQuery: '',
  systemFilters: [],
})
const pageSize = ref(20)
const pageNumber = ref(0)

// Document type filter - initialize with all types enabled
const enabledDocumentTypes = ref<DocumentType[]>(Object.values(DocumentType).filter(v => typeof v === 'number') as DocumentType[])

onBeforeMount(async () => {
  try {
    await api.initialise()
    logger.info('[Library] Document-API initialised successfully')
  }
  catch (error) {
    logger.error(`[Library] Failed to initialise API: ${(error as Error).message}`)
  }

  // Send initial search to populate table
  handleSearchSubmit()

  // Watch for refresh triggers from other components (e.g., after save in GlobalEditorWindows)
  onRefreshTriggered(() => {
    handleSearchSubmit()
  })
})

function buildSearchDocumentsRequest(): SearchDocumentsRequest {
  // Create the request using filter parameters
  const filter = new DocumentFilter({
    nameQuery: basicFilters.value.nameQuery,
    systemFilters: basicFilters.value.systemFilters,
    tagFilters: [], // TODO: Tag filtering not implemented yet
    typeFilters: enabledDocumentTypes.value,
  })

  const req = new SearchDocumentsRequest({
    filter,
    pageSize: pageSize.value,
    pageNumber: pageNumber.value,
    sortOrder: SortOrder.NAME_ASC,
  })

  return req
}

async function handleSearchSubmit() {
  if (!api) {
    logger.error('Error: Document  API client not yet initialised.')
    return
  }

  loading.value = true

  try {
    const request = buildSearchDocumentsRequest()
    logger.info('Searching for documents...')

    const response = await api.searchDocuments(request)

    // Store the results
    documents.value = response.matches
    logger.success(`Success! Found ${response.matches.length} PDF documents (${response.totalCount} total documents)`)
    logger.info(`Returned ${response.matches.length} PDF results on page ${response.pageNumber}`)
  }
  catch (error) {
    logger.error(`Error during document search: ${(error as Error).message}`)
  }
  finally {
    loading.value = false
  }
}

// Open a global editor window for the selected document
async function handleEditDocument(pdf: DocumentListItem) {
  if (!api) {
    logger.error('Error: Document API not initialised')
    return
  }

  try {
    logger.info(`Fetching content for: ${pdf.name}`)

    const response = await api.getDocument(pdf.id)

    if (!response.success || !response.document) {
      logger.error(`Failed to fetch document: ${response.message}`)
      return
    }

    // Open editor window with the fetched content
    openWindow({
      title: response.document.name,
      content: response.document.content || '',
      documentId: response.document.id,
      isNew: false,
    })

    logger.success(`Opened editor for: ${response.document.name} (${response.document.content?.length || 0} characters)`)
  }
  catch (error) {
    logger.error(`Error fetching PDF: ${(error as Error).message}`)
  }
}

// Open embed modal for a document
function handleEmbedDocument(pdf: DocumentListItem) {
  embedDocumentId.value = pdf.id
  showEmbedModal.value = true
  logger.info(`Opening chunk editor for: ${pdf.name}`)
}

// Close embed modal
function closeEmbedModal() {
  showEmbedModal.value = false
  embedDocumentId.value = null
}

// Open bulk edit modal
function openMetadataEditModal() {
  if (selectedIds.value.size === 0) {
    logger.warn('No documents selected for bulk edit')
    return
  }
  showMetadataEditModal.value = true
}

// Get initial document for pre-population (when single item selected)
function getInitialDocumentForMetadataEdit(): DocumentListItem | null {
  if (selectedIds.value.size !== 1)
    return null
  const selectedId = Array.from(selectedIds.value)[0]
  return documents.value.find(doc => doc.id === selectedId) || null
}

async function handleBulkUpdate(formData: MetadataEditFormData) {
  if (!api) {
    logger.error('Error: Document API not initialised')
    return
  }

  bulkEditLoading.value = true

  try {
    logger.info(`Bulk updating ${selectedIds.value.size} documents...`)

    // Import necessary types
    const { Tag } = await import('../bibliophage/v1alpha3/common_pb.ts')

    const { systems: newSystems, type: newType, tags: newTags } = formData

    // Track results
    let successCount = 0
    let failureCount = 0
    const errors: string[] = []

    // Update each selected document
    for (const docId of selectedIds.value) {
      try {
        // Fetch the document
        const getResponse = await api.getDocument(String(docId))

        if (!getResponse.success || !getResponse.document) {
          errors.push(`${docId}: ${getResponse.message}`)
          failureCount++
          continue
        }

        const doc = getResponse.document

        // Update only non-empty fields
        if (newSystems !== null) {
          doc.systems = newSystems
        }

        if (newType !== null) {
          // Update publication_type in metadata if it exists
          if (doc.metadata) {
            doc.metadata.publicationType = newType
          }
        }

        if (newTags !== null) {
          doc.tags = newTags.map((tagData) => {
            const tag = new Tag()
            tag.name = tagData!.name
            tag.values = tagData!.values
            return tag
          })
        }

        // Send update request
        const updateResponse = await api.updateDocument(doc)

        if (updateResponse.success) {
          successCount++
        }
        else {
          errors.push(`${doc.name}: ${updateResponse.message}`)
          failureCount++
        }
      }
      catch (error) {
        errors.push(`${docId}: ${(error as Error).message}`)
        failureCount++
      }
    }

    // Report results
    if (successCount > 0) {
      logger.success(`Successfully updated ${successCount} document${successCount > 1 ? 's' : ''}`)
    }

    if (failureCount > 0) {
      logger.error(`Failed to update ${failureCount} document${failureCount > 1 ? 's' : ''}`)
      errors.forEach(err => logger.error(err))
    }

    // Close modal and refresh
    showMetadataEditModal.value = false
    selectedIds.value.clear()
    await handleSearchSubmit()
  }
  catch (error) {
    logger.error(`Error during bulk update: ${(error as Error).message}`)
  }
  finally {
    bulkEditLoading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">
      Library
    </h1>
  </div>

  <!-- Document Type Filter -->
  <DocumentTypeFilter
    v-model="enabledDocumentTypes"
    class="mb-6"
  />

  <!-- Basic Filters (Name, Systems) -->
  <DocumentBasicFilter
    v-model="basicFilters"
    class="mb-6"
  />

  <div class="flex justify-end">
    <!-- Search Button -->
    <form class="mb-6" @submit.prevent="handleSearchSubmit">
      <button
        type="submit"
        class="btn btn-accent btn-lg gap-2"
        v-bind:disabled="loading"
      >
        <Icon v-if="!loading" icon="game-icons:magnifying-glass" class="text-xl" />
        <span v-if="loading" class="loading loading-spinner" />
        Search
      </button>
    </form>

    <DocumentNewEntryButton />
  </div>

  <!-- Bulk actions toolbar (shown when items are selected) -->
  <div class="alert mb-4 flex justify-between items-center">
    <div class="flex items-center gap-2">
      <Icon icon="heroicons:information-circle" class="text-xl" />
      <span>{{ selectedIds.size }} document{{ selectedIds.size > 1 ? 's' : '' }} selected</span>
    </div>
    <div class="flex gap-2">
      <button type="button" class="btn btn-sm btn-primary gap-1" @click="openMetadataEditModal">
        <Icon icon="heroicons:pencil" />
        Edit Metadata
      </button>
      <button type="button" class="btn btn-sm btn-ghost gap-1" @click="selectedIds.clear()">
        <Icon icon="heroicons:x-mark" />
        Clear Selection
      </button>
    </div>
  </div>

  <DocumentTable
    v-model="selectedIds"
    v-bind:data="documents"
    v-bind:loading="loading"
    @edit="handleEditDocument"
    @embed="handleEmbedDocument"
  />

  <!-- Bulk Edit Modal -->
  <MetadataEditModal
    v-bind:show="showMetadataEditModal"
    v-bind:loading="bulkEditLoading"
    v-bind:selected-count="selectedIds.size"
    v-bind:initial-document="getInitialDocumentForMetadataEdit()"
    @close="showMetadataEditModal = false"
    @submit="handleBulkUpdate"
  />

  <!-- Chunk Editor Modal -->
  <ChunkEditorModal
    v-if="embedDocumentId"
    v-bind:show="showEmbedModal"
    v-bind:document-id="embedDocumentId"
    @close="closeEmbedModal"
  />
</template>
