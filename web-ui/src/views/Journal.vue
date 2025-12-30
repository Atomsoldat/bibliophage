<script setup lang="ts">
import type { Client } from '@connectrpc/connect'
import type { Document, DocumentListItem } from '../bibliophage/v1alpha3/document_pb.ts'
import type { TableColumn } from '../components/DataTable.vue'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'
import { Icon } from '@iconify/vue'
import { computed, onBeforeMount, ref } from 'vue'

import DataTable from '../components/DataTable.vue'
import { DocumentService } from '../bibliophage/v1alpha3/document_connect.ts'
import { DocumentType, SearchDocumentsRequest, GetDocumentRequest, GetDocumentResponse, DeleteDocumentRequest } from '../bibliophage/v1alpha3/document_pb.ts'
import { useAppConsole } from '../composables/useAppConsole'
import { useConfig } from '../composables/useConfig'
import { useEditorWindows } from '../composables/useEditorWindows'
import { useJournalRefresh } from '../composables/useJournalRefresh'

const { config, loadConfig } = useConfig()
const { log } = useAppConsole()
const { openWindow } = useEditorWindows()
const { onRefreshTriggered } = useJournalRefresh()

// Client will be initialized after config loads
const client = ref<Client<typeof DocumentService> | null>(null)

const entries = ref<DocumentListItem[]>([])
const loading = ref(false)
const selectedIds = ref<Set<string>>(new Set())

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
    formatter: (value) => formatDate(value),
  },
  {
    key: 'updatedAt',
    label: 'Updated',
    formatter: (value) => formatDate(value),
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
  // Create the request to search for NOTE type documents
  const req = new SearchDocumentsRequest({
    typeFilter: DocumentType.NOTE,
  })

  return req
}

async function handleSearchSubmit() {
  if (!client.value) {
    log('Error: Client not initialized. Configuration may not be loaded yet.', 'error')
    return
  }

  loading.value = true

  try {
    const request = buildSearchDocumentsRequest()
    log('Searching for journal entries...', 'info')

    const response = await client.value.searchDocuments(request)

    // Store the results
    entries.value = response.matches
    log(`Success! Found ${response.matches.length} journal entries`, 'success')
  }
  catch (error) {
    log(`Error during document search: ${(error as Error).message}`, 'error')
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
  log('Opened new journal entry', 'info')
}

async function fetchDocument(id: string): Promise<Document> {
  if (!client.value) {
    throw new Error('Client not initialized. Configuration may not be loaded yet.')
  }

  const request = new GetDocumentRequest({
    id: id,
  })
  const response = await client.value.getDocument(request)

  if (!response.document) {
    throw new Error('API returned empty document response')
  }

  return response.document
}

async function handleEditEntry(entry: DocumentListItem) {
  try {
    log(`Opening: ${entry.name}`, 'info')
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

    log(`Opened editor for: ${entry.name}`, 'success')
  }
  catch (error) {
    log(`Error opening document: ${(error as Error).message}`, 'error')
  }
}

async function handleBulkDelete() {
  if (!client.value) {
    log('Error: Client not initialized.', 'error')
    return
  }

  if (selectedIds.value.size === 0) {
    log('No entries selected for deletion', 'warning')
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

    log(`Successfully deleted ${count} ${count === 1 ? 'entry' : 'entries'}`, 'success')

    // Clear selections
    selectedIds.value.clear()

    // Refresh the list
    await handleSearchSubmit()
  }
  catch (error) {
    log(`Error deleting entries: ${(error as Error).message}`, 'error')
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
        @click="handleBulkDelete"
        v-bind:disabled="loading"
      >
        <Icon icon="heroicons:trash" class="text-xl" />
        Delete ({{ selectedIds.size }})
      </button>
    </div>

    <!-- Journal entries table -->
    <DataTable
      v-model="selectedIds"
      :data="entries"
      :columns="columns"
      :loading="loading"
      :selectable="true"
      :select-on-row-click="true"
      :enable-column-visibility="true"
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
