<script setup lang="ts">
import type { Client } from '@connectrpc/connect'
import type { Document, DocumentListItem } from '../bibliophage/v1alpha3/document_pb.ts'
import type { TableColumn } from '../components/DataTable.vue'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'
import { Icon } from '@iconify/vue'
import { computed, onBeforeMount, ref } from 'vue'

import { DocumentService } from '../bibliophage/v1alpha3/document_connect.ts'
import { DeleteDocumentRequest, DocumentType, GetDocumentRequest, SearchDocumentsRequest, DocumentFilter } from '../bibliophage/v1alpha3/document_pb.ts'
import DataTable from '../components/DataTable.vue'
import { useConfig } from '../composables/useConfig'
import { useEditorWindows } from '../composables/useEditorWindows'
import { useDocumentTableRefresh } from '../composables/useDocumentTableRefresh.ts'
import { useLogger } from '../composables/useLogger'

const { config, loadConfig } = useConfig()
const logger = useLogger()
const { openWindow } = useEditorWindows()
const { onRefreshTriggered } = useDocumentTableRefresh()

// Client will be initialized after config loads
const client = ref<Client<typeof DocumentService> | null>(null)

const entries = ref<DocumentListItem[]>([])
const loading = ref(false)
const selectedIds = ref<Set<string>>(new Set())

// DocumentType filter state
// Journal-specific types (excluding PDF-sourced types like RULEBOOK, EXPANSION, etc.)
const journalDocumentTypes = [
  { value: DocumentType.DOCUMENT_TYPE_UNSPECIFIED, label: 'Unspecified', enabled: ref(true) },
  { value: DocumentType.NOTE, label: 'Note', enabled: ref(true) },
  { value: DocumentType.LORE_FRAGMENT, label: 'Lore Fragment', enabled: ref(true) },
  { value: DocumentType.CHARACTER, label: 'Character', enabled: ref(true) },
  { value: DocumentType.LOCATION, label: 'Location', enabled: ref(true) },
  { value: DocumentType.OBJECT, label: 'Object', enabled: ref(true) },
  { value: DocumentType.QUEST, label: 'Quest', enabled: ref(true) },
  { value: DocumentType.SESSION_LOG, label: 'Session Log', enabled: ref(true) },
  { value: DocumentType.RULEBOOK, label: 'Rulebook', enabled: ref(true) },
  { value: DocumentType.EXPANSION, label: 'Expansion', enabled: ref(true) },
  { value: DocumentType.ADVENTURE, label: 'Adventure', enabled: ref(true) },
  { value: DocumentType.BESTIARY, label: 'Bestiary', enabled: ref(true) },
]

// Track dropdown state
const isTypeFilterOpen = ref(false)

/**
 * Toggle type filter dropdown
 */
function toggleTypeFilter() {
  isTypeFilterOpen.value = !isTypeFilterOpen.value
}

/**
 * Get count of enabled document types
 */
const enabledTypeCount = computed(() => {
  return journalDocumentTypes.filter(t => t.enabled.value).length
})

/**
 * Toggle all document types on/off
 */
function toggleAllTypes() {
  const allEnabled = journalDocumentTypes.every(t => t.enabled.value)
  journalDocumentTypes.forEach(t => t.enabled.value = !allEnabled)
}

/**
 * Convert DocumentType enum value to human-readable label
 */
function formatDocumentType(type: DocumentType): string {
  const typeEntry = journalDocumentTypes.find(t => t.value === type)
  return typeEntry?.label || 'Unknown'
}

/**
 * Define table columns for journal entries
 */
const columns = computed<TableColumn<DocumentListItem>[]>(() => [
  {
    key: 'index',
    label: 'Index',
    formatter: (_value, _row, index) => index,
    required: true,
  },
  {
    key: 'name',
    label: 'Name',
    required: true,
  },
  {
    key: 'systems',
    label: 'System',
  },
  {
    key: 'type',
    label: 'Document Type',
    formatter: value => formatDocumentType(value),
  },
  {
    key: 'id',
    label: 'ID',
    cellClass: 'text-xs font-mono',
  },
  {
    key: 'tags',
    label: 'Tags',
  },
  {
    key: 'createdAt',
    label: 'Created',
    formatter: value => formatDate(value),
  },
  {
    key: 'updatedAt',
    label: 'Updated',
    formatter: value => formatDate(value),
  },
  {
    key: 'actions',
    label: 'Actions',
    required: true,
  },
])

onBeforeMount(async () => {
  // Load configuration first
  await loadConfig()

  // Create client with loaded config
  const transport = createConnectTransport({
    baseUrl: config.value.backendHost,
  })
  client.value = createClient(DocumentService, transport)

  // Send initial search to populate table
  handleSearchSubmit()

  // Watch for refresh triggers from other components (e.g., after save in GlobalEditorWindows)
  onRefreshTriggered(() => {
    handleSearchSubmit()
  })
})

function buildSearchDocumentsRequest(): SearchDocumentsRequest {
  // Get enabled document types
  const enabledTypes = journalDocumentTypes
    .filter(t => t.enabled.value)
    .map(t => t.value)

  // Note: The API currently only supports a single typeFilter
  // For now, we'll filter client-side if multiple types are selected
  // TODO: Update API to support multiple type filters

  const filter = new DocumentFilter({
    typeFilters: enabledTypes,
  })

  const req = new SearchDocumentsRequest({
    filter,
  })

  return req
}


async function handleSearchSubmit() {
  if (!client.value) {
    logger.error('Error: Client not initialized. Configuration may not be loaded yet.')
    return
  }

  loading.value = true

  try {
    const request = buildSearchDocumentsRequest()
    logger.info('Searching for journal entries...')

    const response = await client.value.searchDocuments(request)

    // Store the results
    entries.value = response.matches
    logger.success(`Success! Found ${entries.value.length} documents entries`)
  }
  catch (error) {
    logger.error(`Error during document search: ${(error as Error).message}`)
  }
  finally {
    loading.value = false
  }
}

/**
 * Format timestamp for display
 */
function formatDate(timestamp: any): string {
  if (!timestamp)
    return 'N/A'
  try {
    const date = timestamp.toDate()
    return new Intl.DateTimeFormat('de-DE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }
  catch {
    return 'N/A'
  }
}

// Expose handleSearchSubmit so it can be called by other components
defineExpose({
  refresh: handleSearchSubmit,
})

function handleNewEntry() {
  openWindow({
    title: 'New Journal Entry',
    content: '',
    documentId: '',
    isNew: true,
  })
  logger.info('Opened new journal entry')
}

async function fetchDocument(id: string): Promise<Document> {
  if (!client.value) {
    throw new Error('Client not initialized. Configuration may not be loaded yet.')
  }

  const request = new GetDocumentRequest({
    id,
  })
  const response = await client.value.getDocument(request)

  if (!response.document) {
    throw new Error('API returned empty document response')
  }

  return response.document
}

async function handleEditEntry(entry: DocumentListItem) {
  try {
    logger.info(`Opening: ${entry.name}`)
    const document = await fetchDocument(entry.id)
    if (!document.content) {
      throw new Error('API returned document with empty content, refusing to edit out of caution')
    }
    // Open editor window with the document's content
    openWindow({
      title: entry.name,
      content: document.content,
      documentId: entry.id,
      isNew: false,
    })

    logger.success(`Opened editor for: ${entry.name}`)
  }
  catch (error) {
    logger.error(`Error opening document: ${(error as Error).message}`)
  }
}

async function handleBulkDelete() {
  if (!client.value) {
    logger.error('Error: Client not initialized.')
    return
  }

  if (selectedIds.value.size === 0) {
    logger.warn('No entries selected for deletion')
    return
  }

  const count = selectedIds.value.size
  const confirmed = confirm(`Are you sure you want to delete ${count} selected ${count === 1 ? 'entry' : 'entries'}?`)

  if (!confirmed) {
    return
  }

  loading.value = true

  try {
    const deletePromises = Array.from(selectedIds.value).map(async (id) => {
      const request = new DeleteDocumentRequest({ id })
      return client.value!.deleteDocument(request)
    })

    await Promise.all(deletePromises)

    logger.success(`Successfully deleted ${count} ${count === 1 ? 'entry' : 'entries'}`)

    // Clear selections
    selectedIds.value.clear()

    // Refresh the list
    await handleSearchSubmit()
  }
  catch (error) {
    logger.error(`Error deleting entries: ${(error as Error).message}`)
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex justify-between items-center mb-8">
    <h1 class="text-4xl font-bold">
      Journal
    </h1>
    <button
      type="button"
      class="btn btn-primary btn-lg gap-2"
      @click="handleNewEntry"
    >
      <Icon icon="heroicons:plus" />
      New Entry
    </button>
  </div>

  <!-- Document Type Filter -->
  <div class="card bg-base-200 shadow-xl p-6 mb-6">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-4">
        <h3 class="font-semibold text-lg">
          Document Type Filter
        </h3>
        <span class="badge badge-primary">
          {{ enabledTypeCount }} / {{ journalDocumentTypes.length }} types shown
        </span>
      </div>
      <div class="relative">
        <button
          type="button"
          class="btn btn-sm btn-primary gap-2"
          @click="toggleTypeFilter"
        >
          <Icon icon="heroicons:funnel" />
          {{ isTypeFilterOpen ? 'Hide' : 'Show' }} Filters
        </button>
      </div>
    </div>

    <!-- Type filter checkboxes (collapsible) -->
    <div v-if="isTypeFilterOpen" class="mt-4 pt-4 border-t border-base-300">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <label
          v-for="docType in journalDocumentTypes"
          v-bind:key="docType.value"
          class="label cursor-pointer justify-start gap-2 hover:bg-base-300 rounded-lg px-2"
        >
          <input
            v-model="docType.enabled.value"
            type="checkbox"
            class="checkbox checkbox-sm checkbox-primary"
          >
          <span class="label-text">{{ docType.label }}</span>
        </label>
      </div>
      <div class="mt-4 flex justify-end">
        <button
          type="button"
          class="btn btn-ghost btn-xs"
          @click="toggleAllTypes"
        >
          Toggle All
        </button>
      </div>
    </div>
  </div>

  <!-- Action Buttons -->
  <div class="flex gap-4 mb-4">
    <form class="flex-1" @submit.prevent="handleSearchSubmit">
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

    <button
      v-if="selectedIds.size > 0"
      type="button"
      class="btn btn-error btn-lg gap-2"
      v-bind:disabled="loading"
      @click="handleBulkDelete"
    >
      <Icon icon="heroicons:trash" class="text-xl" />
      Delete ({{ selectedIds.size }})
    </button>
  </div>

  <!-- Journal entries table -->
  <DataTable
    v-model="selectedIds"
    v-bind:data="entries"
    v-bind:columns="columns"
    v-bind:loading="loading"
    v-bind:selectable="true"
    v-bind:select-on-row-click="true"
    v-bind:enable-column-visibility="true"
    table-id="journal"
    row-key="id"
    empty-message="No journal entries yet"
    empty-description="Click 'New Entry' to create your first journal entry"
  >
    <!-- Custom rendering for Name column with preview -->
    <template #cell-name="{ row }">
      <div class="font-semibold">
        {{ row.name }}
      </div>
      <div class="text-sm text-base-content/70 truncate max-w-md">
        {{ row.content?.substring(0, 100) }}{{ row.content && row.content.length > 100 ? '...' : '' }}
      </div>
    </template>

    <!-- Custom rendering for Systems column with badges -->
    <template #cell-systems="{ row }">
      <div class="flex gap-1 flex-wrap">
        <span v-for="system in row.systems" v-bind:key="system" class="badge badge-sm badge-primary">
          {{ system }}
        </span>
        <span v-if="row.systems.length === 0" class="text-sm text-base-content/50">
          -
        </span>
      </div>
    </template>

    <!-- Custom rendering for Tags column with badges -->
    <template #cell-tags="{ row }">
      <div class="flex gap-1 flex-wrap">
        <span v-for="tag in row.tags" v-bind:key="tag" class="badge badge-sm badge-outline">
          {{ tag }}
        </span>
        <span v-if="row.tags.length === 0" class="text-sm text-base-content/50">
          -
        </span>
      </div>
    </template>

    <!-- Custom rendering for Actions column with Edit button -->
    <template #cell-actions="{ row }">
      <button
        type="button"
        class="btn btn-sm btn-primary gap-1"
        @click.stop="handleEditEntry(row)"
      >
        <Icon icon="heroicons:pencil" />
        Edit
      </button>
    </template>
  </DataTable>
</template>
