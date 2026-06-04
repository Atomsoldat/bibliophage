<script setup lang="ts">
import type { DocumentListItem, DocumentType } from '../utils/protoHelpers'
import type { DocumentBasicFilterValue } from './DocumentBasicFilter.vue'
import { Icon } from '@iconify/vue'
import { onBeforeMount, ref } from 'vue'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useLogger } from '../composables/useLogger'
import {
  buildSearchDocumentsRequest,

  getAllDocumentTypes,
  SortOrder,
} from '../utils/protoHelpers'
import DocumentBasicFilter from './DocumentBasicFilter.vue'
import DocumentTypeFilter from './DocumentTypeFilter.vue'

/**
 * Side panel for finding a document to pin onto the graph canvas.
 *
 * Reuses the existing document search primitives — filters and the search
 * RPC — so the UX is consistent with /library. Emits `pick` when the user
 * clicks a search result; the parent decides what to do with it (here:
 * graph store's pinNode).
 */

const emit = defineEmits<{ pick: [doc: DocumentListItem] }>()

const api = useDocumentApi()
const logger = useLogger()

const basicFilters = ref<DocumentBasicFilterValue>({
  nameQuery: '',
  systemFilters: [],
})
const enabledDocumentTypes = ref<DocumentType[]>(getAllDocumentTypes())

const results = ref<DocumentListItem[]>([])
const loading = ref(false)

onBeforeMount(async () => {
  try {
    await api.initialise()
  }
  catch (err) {
    logger.error(`[GraphSearch] Failed to initialise document API: ${(err as Error).message}`)
  }
})

async function handleSearch(): Promise<void> {
  loading.value = true
  try {
    const request = buildSearchDocumentsRequest({
      nameQuery: basicFilters.value.nameQuery,
      systemFilters: basicFilters.value.systemFilters,
      typeFilters: enabledDocumentTypes.value,
      pageSize: 20,
      pageNumber: 0,
      sortOrder: SortOrder.NAME_ASC,
    })
    const response = await api.searchDocuments(request)
    results.value = response.matches
    logger.info(`[GraphSearch] Found ${response.matches.length} document(s)`)
  }
  catch (err) {
    logger.error(`[GraphSearch] Search failed: ${(err as Error).message}`)
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-3 h-full">
    <h2 class="text-lg font-semibold">
      Search
    </h2>

    <DocumentBasicFilter v-model="basicFilters" />
    <DocumentTypeFilter v-model="enabledDocumentTypes" />

    <button
      type="button"
      class="btn btn-accent btn-sm gap-2"
      v-bind:disabled="loading"
      @click="handleSearch"
    >
      <Icon v-if="!loading" icon="game-icons:magnifying-glass" />
      <span v-if="loading" class="loading loading-spinner loading-xs" />
      Search
    </button>

    <div class="flex-1 overflow-y-auto border border-base-300 rounded">
      <ul v-if="results.length > 0" class="menu menu-sm bg-base-100 p-1">
        <li v-for="doc in results" v-bind:key="doc.id">
          <button
            type="button"
            class="flex flex-col items-start gap-0 py-1"
            @click="emit('pick', doc)"
          >
            <span class="font-medium truncate w-full">{{ doc.name }}</span>
            <span class="text-xs opacity-60 truncate w-full">
              {{ doc.contentSnippet || '(no snippet)' }}
            </span>
          </button>
        </li>
      </ul>
      <div v-else class="text-xs opacity-50 p-3">
        No results yet. Refine the filters and hit Search.
      </div>
    </div>
  </div>
</template>
