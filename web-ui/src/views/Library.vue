<script setup lang="ts">
import type { DocumentBasicFilterValue } from '../components/DocumentBasicFilter.vue'

import type { DocumentListItem, DocumentType } from '../utils/protoHelpers.ts'
import { Icon } from '@iconify/vue'
import { storeToRefs } from 'pinia'
import { onBeforeMount, ref } from 'vue'
import ChunkEditorModal from '../components/ChunkEditorModal.vue'
import DocumentBasicFilter from '../components/DocumentBasicFilter.vue'
import DocumentDeleteButton from '../components/DocumentDeleteButton.vue'
import DocumentEditMetadataButton from '../components/DocumentEditMetadataButton.vue'
import DocumentNewEntryButton from '../components/DocumentNewEntryButton.vue'
import DocumentTable from '../components/DocumentTable.vue'
import DocumentTypeFilter from '../components/DocumentTypeFilter.vue'
import { useBulkDelete } from '../composables/useBulkDelete.ts'
import { useBulkMetadataEdit } from '../composables/useBulkMetadataEdit.ts'
import { useDocumentApi } from '../composables/useDocumentApi.ts'
import { useLogger } from '../composables/useLogger.ts'
import { useDocumentStore } from '../stores/documents'
import { useEditorWindowStore } from '../stores/editorWindows'
import { getAllDocumentTypes, SortOrder } from '../utils/protoHelpers.ts'

const logger = useLogger()
const { openWindow } = useEditorWindowStore()
const documentStore = useDocumentStore()
const { documents, loading, selectedIds } = storeToRefs(documentStore)
const api = useDocumentApi()

// Bulk actions (composables handle modal state and logic)
const bulkMetadataEdit = useBulkMetadataEdit()
const bulkDelete = useBulkDelete()

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

// Document type filter - initialise with all types enabled
const enabledDocumentTypes = ref<DocumentType[]>(getAllDocumentTypes())

onBeforeMount(async () => {
  handleSearchSubmit()
})

async function handleSearchSubmit() {
  await documentStore.search({
    nameQuery: basicFilters.value.nameQuery,
    systemFilters: basicFilters.value.systemFilters,
    typeFilters: enabledDocumentTypes.value,
    pageSize: pageSize.value,
    pageNumber: pageNumber.value,
    sortOrder: SortOrder.NAME_ASC,
  })
}

// Open a global editor window for the selected document
async function handleEditDocument(target: DocumentListItem) {
  try {
    logger.info(`Fetching content for: ${target.name}`)

    await api.initialise()
    const response = await api.getDocument(target.id)

    if (!response.success || !response.document) {
      logger.error(`Failed to fetch document: ${response.message}`)
      return
    }

    openWindow({
      title: response.document.name,
      content: response.document.content || '',
      documentId: response.document.id,
      isNew: false,
    })

    logger.success(`Opened editor for: ${response.document.name} (${response.document.content?.length || 0} characters)`)
  }
  catch (error) {
    logger.error(`Error fetching document: ${(error as Error).message}`)
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
      <DocumentEditMetadataButton v-bind:bulk-edit="bulkMetadataEdit" />
      <DocumentDeleteButton v-bind:bulk-delete="bulkDelete" />
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

  <!-- Chunk Editor Modal -->
  <ChunkEditorModal
    v-if="embedDocumentId"
    v-bind:show="showEmbedModal"
    v-bind:document-id="embedDocumentId"
    @close="closeEmbedModal"
  />
</template>
