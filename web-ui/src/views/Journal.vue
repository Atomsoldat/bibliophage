<script setup lang="ts">
import type { Document } from '../bibliophage/v1alpha2/document_pb.ts'

import { Icon } from '@iconify/vue'
import { onBeforeMount, ref } from 'vue'

import { DocumentType } from '../bibliophage/v1alpha2/document_pb.ts'
import { useAppConsole } from '../composables/useAppConsole'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useEditorWindows } from '../composables/useEditorWindows'

const { log } = useAppConsole()
const api = useDocumentApi()
const { openWindow } = useEditorWindows()

const documents = ref<Document[]>([])
const loading = ref(false)

onBeforeMount(async () => {
  try {
    await api.initialise()
    // Load journal entries on mount
    await loadJournalEntries()
  } catch (error) {
    log(`Failed to initialize: ${(error as Error).message}`, 'error')
  }
})

async function loadJournalEntries() {
  loading.value = true

  try {
    log('Loading journal entries...', 'info')
    const response = await api.searchDocuments({
      typeFilter: DocumentType.NOTE
    })

    if (response?.success && response.documents) {
      documents.value = response.documents
      log(`Found ${documents.value.length} journal entries`, 'success')
    }
  } catch (error) {
    log(`Error loading journal entries: ${(error as Error).message}`, 'error')
  } finally {
    loading.value = false
  }
}

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
  } catch (error) {
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

    <!-- Loading indicator -->
    <div v-if="loading" class="flex justify-center items-center p-8">
      <span class="loading loading-spinner loading-lg" />
    </div>

    <!-- Journal entries list -->
    <div v-else-if="documents.length > 0" class="space-y-4">
      <div
        v-for="document in documents"
        :key="document.id"
        class="card bg-base-100 border border-base-300 hover:shadow-lg transition-shadow"
      >
        <div class="card-body">
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <h2 class="card-title">{{ document.name }}</h2>
              <p class="text-sm text-base-content/70 mt-1">
                {{ document.content?.substring(0, 150) }}{{ document.content && document.content.length > 150 ? '...' : '' }}
              </p>
              <div class="flex gap-2 mt-2">
                <span v-for="tag in document.tags" :key="tag" class="badge badge-sm">{{ tag }}</span>
              </div>
            </div>
            <button
              type="button"
              class="btn btn-sm btn-primary gap-1"
              @click="handleEditEntry(document)"
            >
              <Icon icon="heroicons:pencil" />
              Edit
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center p-12">
      <Icon icon="heroicons:document-text" class="text-6xl text-base-content/30 mx-auto mb-4" />
      <p class="text-lg text-base-content/70">No journal entries yet</p>
      <p class="text-sm text-base-content/50 mt-2">Click "New Entry" to create your first journal entry</p>
    </div>
  </div>
</template>
