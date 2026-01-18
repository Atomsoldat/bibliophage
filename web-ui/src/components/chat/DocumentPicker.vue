<script setup lang="ts">
import type { DocumentListItem } from '../../bibliophage/v1alpha3/document_pb'
import type { ContextDocument, RetrievedChunk } from '../../composables/useChatState'
import { Icon } from '@iconify/vue'
import { ref } from 'vue'
import { useDocumentApi } from '../../composables/useDocumentApi'

const props = defineProps<{
  selectedDocuments: readonly ContextDocument[]
  autoRetrievalEnabled: boolean
  retrievedChunks: readonly RetrievedChunk[]
}>()

const emit = defineEmits<{
  toggle: [doc: ContextDocument]
  'update:autoRetrievalEnabled': [enabled: boolean]
}>()

const documentApi = useDocumentApi()
const searchQuery = ref('')
const searchResults = ref<DocumentListItem[]>([])
const isSearching = ref(false)

// Search documents when query changes
async function handleSearch() {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }

  isSearching.value = true
  try {
    await documentApi.initialise()
    const response = await documentApi.searchDocuments({
      filter: {
        nameQuery: searchQuery.value,
      },
      pageSize: 20,
    })
    searchResults.value = response.matches
  }
  catch (error) {
    console.error('Document search failed:', error)
  }
  finally {
    isSearching.value = false
  }
}

function isSelected(docId: string): boolean {
  return props.selectedDocuments.some(d => d.id === docId)
}

function handleToggle(doc: DocumentListItem) {
  emit('toggle', {
    id: doc.id,
    name: doc.name,
    snippet: doc.contentSnippet,
  })
}

function formatSimilarity(similarity: number): string {
  return `${Math.round(similarity * 100)}%`
}

function toggleAutoRetrieval() {
  emit('update:autoRetrievalEnabled', !props.autoRetrievalEnabled)
}
</script>

<template>
  <div class="border border-base-300 rounded-lg p-4">
    <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
      <Icon icon="heroicons:document-text" />
      Context Documents
      <span v-if="selectedDocuments.length > 0" class="badge badge-primary">
        {{ selectedDocuments.length }}
      </span>
    </h3>

    <!-- Auto-retrieval toggle -->
    <div class="form-control mb-3">
      <label class="label cursor-pointer justify-start gap-3">
        <input
          type="checkbox"
          class="toggle toggle-sm toggle-primary"
          :checked="autoRetrievalEnabled"
          @change="toggleAutoRetrieval"
        >
        <span class="label-text flex items-center gap-1">
          <Icon icon="heroicons:sparkles" class="text-primary" />
          Auto-retrieve context
        </span>
      </label>
    </div>

    <!-- Search input -->
    <div class="form-control mb-3">
      <div class="input-group">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search documents..."
          class="input input-bordered w-full"
          @keyup.enter="handleSearch"
        >
        <button class="btn btn-square" @click="handleSearch">
          <Icon icon="heroicons:magnifying-glass" />
        </button>
      </div>
    </div>

    <!-- Selected documents -->
    <div v-if="selectedDocuments.length > 0" class="mb-3">
      <div class="text-xs font-semibold text-base-content/60 mb-2">
        Selected:
      </div>
      <div class="flex flex-wrap gap-2">
        <div
          v-for="doc in selectedDocuments"
          v-bind:key="doc.id"
          class="badge badge-primary gap-1"
        >
          {{ doc.name }}
          <button class="btn btn-ghost btn-xs btn-circle" @click="$emit('toggle', doc)">
            <Icon icon="heroicons:x-mark" class="text-xs" />
          </button>
        </div>
      </div>
    </div>

    <!-- Auto-retrieved chunks -->
    <div v-if="retrievedChunks.length > 0" class="mb-3">
      <div class="text-xs font-semibold text-base-content/60 mb-2 flex items-center gap-1">
        <Icon icon="heroicons:sparkles" class="text-xs" />
        Auto-Retrieved
        <span class="badge badge-ghost badge-xs">{{ retrievedChunks.length }}</span>
      </div>
      <div class="space-y-2 max-h-[200px] overflow-y-auto">
        <div
          v-for="chunk in retrievedChunks"
          v-bind:key="chunk.chunkId"
          class="p-2 border border-base-200 rounded bg-base-100"
        >
          <div class="flex items-center justify-between mb-1">
            <span class="font-semibold text-xs truncate flex-1">
              {{ chunk.documentName }}
            </span>
            <span class="badge badge-sm badge-ghost ml-2">
              {{ formatSimilarity(chunk.similarity) }}
            </span>
          </div>
          <div class="text-xs text-base-content/70 line-clamp-2">
            {{ chunk.content }}
          </div>
        </div>
      </div>
    </div>

    <!-- Search results -->
    <div v-if="isSearching" class="flex justify-center p-4">
      <span class="loading loading-spinner" />
    </div>
    <div
      v-else-if="searchResults.length > 0"
      class="space-y-2 max-h-[300px] overflow-y-auto"
    >
      <div
        v-for="doc in searchResults"
        v-bind:key="doc.id"
        class="p-2 border border-base-300 rounded hover:bg-base-200 cursor-pointer flex items-start gap-2"
        @click="handleToggle(doc)"
      >
        <input
          type="checkbox"
          class="checkbox checkbox-sm mt-1"
          v-bind:checked="isSelected(doc.id)"
          @click.stop
        >
        <div class="flex-1">
          <div class="font-semibold text-sm">
            {{ doc.name }}
          </div>
          <div class="text-xs text-base-content/60 line-clamp-2">
            {{ doc.contentSnippet }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
