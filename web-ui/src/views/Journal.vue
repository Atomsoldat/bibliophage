<script setup lang="ts">
import type { Client } from '@connectrpc/connect'
import type { Document, DocumentListItem } from '../bibliophage/v1alpha2/document_pb.ts'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'
import { Icon } from '@iconify/vue'
import { onBeforeMount, ref } from 'vue'

import { DocumentService } from '../bibliophage/v1alpha2/document_connect.ts'
import { DocumentType, SearchDocumentsRequest, GetDocumentRequest, GetDocumentResponse, DeleteDocumentRequest } from '../bibliophage/v1alpha2/document_pb.ts'
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
    // Open editor window with the document's content
    openWindow({
      title: entry.name,
      content: document.content || '',
      documentId: entry.id,
      isNew: false,
    })

    log(`Opened editor for: ${entry.name}`, 'success')
  }
  catch (error) {
    log(`Error opening document: ${(error as Error).message}`, 'error')
  }
}

function toggleSelection(id: string) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  }
  else {
    selectedIds.value.add(id)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.size === entries.value.length) {
    // Deselect all
    selectedIds.value.clear()
  }
  else {
    // Select all
    selectedIds.value = new Set(entries.value.map(entry => entry.id))
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
  <div class="max-w-7xl mx-auto px-4">
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
          class="btn btn-accent btn-lg w-full gap-2"
          v-bind:disabled="loading"
        >
          <Icon v-if="!loading" icon="heroicons:arrow-path" class="text-xl" />
          <span v-if="loading" class="loading loading-spinner" />
          Refresh
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

    <!-- Loading indicator -->
    <div v-if="loading && entries.length === 0" class="flex justify-center items-center p-8">
      <span class="loading loading-spinner loading-lg" />
    </div>

    <!-- Journal entries table -->
    <div v-else-if="entries.length > 0" class="overflow-x-auto">
      <table class="table table-zebra">
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                class="checkbox"
                v-bind:checked="entries.length > 0 && selectedIds.size === entries.length"
                @change="toggleSelectAll"
              />
            </th>
            <th>Index</th>
            <th>Name</th>
            <th>ID</th>
            <th>Tags</th>
            <th>Created</th>
            <th>Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, index) in entries" v-bind:key="entry.id" class="hover">
            <td>
              <input
                type="checkbox"
                class="checkbox"
                v-bind:checked="selectedIds.has(entry.id)"
                @change="toggleSelection(entry.id)"
              />
            </td>
            <th>{{ index }}</th>
            <td>
              <div class="font-semibold">
                {{ entry.name }}
              </div>
              <div class="text-sm text-base-content/70 truncate max-w-md">
                {{ entry.content?.substring(0, 100) }}{{ entry.content && entry.content.length > 100 ? '...' : '' }}
              </div>
            </td>
            <td class="text-xs font-mono">
              {{ entry.id }}
            </td>
            <td>
              <div class="flex gap-1 flex-wrap">
                <span v-for="tag in entry.tags" v-bind:key="tag" class="badge badge-sm badge-outline">
                  {{ tag }}
                </span>
                <span v-if="entry.tags.length === 0" class="text-sm text-base-content/50">
                  -
                </span>
              </div>
            </td>
            <td>
              <span class="text-sm">{{ formatDate(entry.createdAt) }}</span>
            </td>
            <td>
              <span class="text-sm">{{ formatDate(entry.updatedAt) }}</span>
            </td>
            <td>
              <button
                type="button"
                class="btn btn-sm btn-primary gap-1"
                @click="handleEditEntry(entry)"
              >
                <Icon icon="heroicons:pencil" />
                Edit
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center p-12">
      <Icon icon="heroicons:document-text" class="text-6xl text-base-content/30 mx-auto mb-4" />
      <p class="text-lg text-base-content/70">
        No journal entries yet
      </p>
      <p class="text-sm text-base-content/50 mt-2">
        Click "New Entry" to create your first journal entry
      </p>
    </div>
  </div>
</template>
