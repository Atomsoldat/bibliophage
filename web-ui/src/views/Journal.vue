<script setup lang="ts">
import type { Client } from '@connectrpc/connect'
import type { Document } from '../bibliophage/v1alpha2/document_pb.ts'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'
import { Icon } from '@iconify/vue'
import { onBeforeMount, ref } from 'vue'

import { DocumentService } from '../bibliophage/v1alpha2/document_connect.ts'
import { DocumentType, SearchDocumentsRequest } from '../bibliophage/v1alpha2/document_pb.ts'
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

const documents = ref<Document[]>([])
const loading = ref(false)

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
    documents.value = response.documents
    log(`Success! Found ${response.documents.length} journal entries`, 'success')
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

async function handleEditEntry(document: Document) {
  try {
    log(`Opening: ${document.name}`, 'info')

    // Open editor window with the document
    openWindow({
      title: document.name,
      content: document.content || '',
      documentId: document.id,
      isNew: false,
    })

    log(`Opened editor for: ${document.name}`, 'success')
  }
  catch (error) {
    log(`Error opening document: ${(error as Error).message}`, 'error')
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

    <!-- Refresh Button -->
    <form class="mb-4" @submit.prevent="handleSearchSubmit">
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

    <!-- Loading indicator -->
    <div v-if="loading && documents.length === 0" class="flex justify-center items-center p-8">
      <span class="loading loading-spinner loading-lg" />
    </div>

    <!-- Journal entries table -->
    <div v-else-if="documents.length > 0" class="overflow-x-auto">
      <table class="table table-zebra">
        <thead>
          <tr>
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
          <tr v-for="(document, index) in documents" v-bind:key="document.id" class="hover">
            <th>{{ index }}</th>
            <td>
              <div class="font-semibold">
                {{ document.name }}
              </div>
              <div class="text-sm text-base-content/70 truncate max-w-md">
                {{ document.content?.substring(0, 100) }}{{ document.content && document.content.length > 100 ? '...' : '' }}
              </div>
            </td>
            <td class="text-xs font-mono">
              {{ document.id }}
            </td>
            <td>
              <div class="flex gap-1 flex-wrap">
                <span v-for="tag in document.tags" v-bind:key="tag" class="badge badge-sm badge-outline">
                  {{ tag }}
                </span>
                <span v-if="document.tags.length === 0" class="text-sm text-base-content/50">
                  -
                </span>
              </div>
            </td>
            <td>
              <span class="text-sm">{{ formatDate(document.createdAt) }}</span>
            </td>
            <td>
              <span class="text-sm">{{ formatDate(document.updatedAt) }}</span>
            </td>
            <td>
              <button
                type="button"
                class="btn btn-sm btn-primary gap-1"
                @click="handleEditEntry(document)"
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
