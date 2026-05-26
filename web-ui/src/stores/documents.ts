import { defineStore } from 'pinia'
import { ref } from 'vue'
import { type DocumentListItem, type SearchDocumentsParams, buildSearchDocumentsRequest } from '../utils/protoHelpers.ts'
import { useDocumentApi } from '../composables/useDocumentApi.ts'
import { useLogger } from '../composables/useLogger.ts'

export const useDocumentStore = defineStore('documents', () => {
  const api = useDocumentApi()
  const logger = useLogger()

  const documents = ref<DocumentListItem[]>([])
  const loading = ref(false)
  const selectedIds = ref<Set<string>>(new Set())

  // Last search params retained so reload() can repeat them
  let lastSearchParams: SearchDocumentsParams | null = null

  async function search(params: SearchDocumentsParams): Promise<void> {
    lastSearchParams = params
    loading.value = true
    try {
      await api.initialise()
      const request = buildSearchDocumentsRequest(params)
      const response = await api.searchDocuments(request)
      documents.value = response.matches
      logger.success(`Found ${response.matches.length} documents (${response.totalCount} total)`)
    }
    catch (error) {
      logger.error(`Document search failed: ${(error as Error).message}`)
    }
    finally {
      loading.value = false
    }
  }

  async function reload(): Promise<void> {
    if (lastSearchParams) {
      await search(lastSearchParams)
    }
  }

  return { documents, loading, selectedIds, search, reload }
})
