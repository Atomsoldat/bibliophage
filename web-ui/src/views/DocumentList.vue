<script setup lang="ts">
import type { Client } from '@connectrpc/connect'
import type { PdfListItem } from '../bibliophage/v1alpha3/pdf_pb.ts'
import type { TableColumn } from '../components/DataTable.vue'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'
import { Icon } from '@iconify/vue'
import { computed, onBeforeMount, ref } from 'vue'

import DataTable from '../components/DataTable.vue'
import { SortOrder } from '../bibliophage/v1alpha3/common_pb.ts'
import { PdfService } from '../bibliophage/v1alpha3/pdf_connect.ts'
import { SearchPdfsRequest } from '../bibliophage/v1alpha3/pdf_pb.ts'
import { useAppConsole } from '../composables/useAppConsole'
import { useConfig } from '../composables/useConfig'
import { useEditorWindows } from '../composables/useEditorWindows'

const { config, loadConfig } = useConfig()
const { log } = useAppConsole()
const { openWindow } = useEditorWindows()

// Client will be initialized after config loads
// see https://connectrpc.com/docs/node/using-clients/#connect
const client = ref<Client<typeof PdfService> | null>(null)

const pdfs = ref<PdfListItem[]>([])
const loading = ref(false)

// Search filter parameters
// TODO: Make these selectable via the web UI (dropdowns, checkboxes, etc.)
const titleQuery = ref('')
const systemFilters = ref<string[]>(['PATHFINDER_1E']) // Filter by systems (ANY match)
const typeFilter = ref('')
const pageSize = ref(20)
const pageNumber = ref(0)

/**
 * Format file size in bytes to human-readable format (KB, MB, GB)
 */
function formatFileSize(bytes: number | bigint): string {
  if (bytes === 0 || bytes === 0n) return '0 B'

  const numBytes = typeof bytes === 'bigint' ? Number(bytes) : bytes
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  const kibibyte = 1024
  const magnitude = Math.floor(Math.log(numBytes) / Math.log(kibibyte))

  return `${(numBytes / Math.pow(kibibyte, magnitude)).toFixed(2)} ${units[magnitude]}`
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

/**
 * Define table columns for PDF list
 */
const columns = computed<TableColumn<PdfListItem>[]>(() => [
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
    key: 'systems',
    label: 'Systems',
  },
  {
    key: 'type',
    label: 'Type',
  },
  {
    key: 'pageCount',
    label: 'Page Count',
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
    key: 'fileSize',
    label: 'Size',
    formatter: (value) => formatFileSize(value),
  },
  {
    key: 'batchCount',
    label: 'Batches',
  },
  {
    key: 'vectorChunkCount',
    label: 'Chunks',
  },
  {
    key: 'tags',
    label: 'Tags',
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
  client.value = createClient(PdfService, transport)

  // Send initial search to populate table
  handleSearchSubmit()
})

function buildSearchPdfsRequest(): SearchPdfsRequest {
  // Create the request using filter parameters
  const req = new SearchPdfsRequest({
    titleQuery: titleQuery.value,
    systemFilters: systemFilters.value,
    typeFilter: typeFilter.value,
    tagFilters: [],
    pageSize: pageSize.value,
    pageNumber: pageNumber.value,
    sortOrder: SortOrder.NAME_ASC,
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
    const request = buildSearchPdfsRequest()
    log('Searching for PDFs...', 'info')

    const response = await client.value.searchPdfs(request)

    // Store the results
    pdfs.value = response.pdfs
    log(`Success! Found ${response.totalCount} PDFs`, 'success')
    log(`Returned ${response.pdfs.length} results on page ${response.pageNumber}`, 'info')
  }
  catch (error) {
    log(`Error during PDF search: ${(error as Error).message}`, 'error')
  }
  finally {
    loading.value = false
  }
}

// Open a global editor window for the selected document
async function handleEditDocument(pdf: PdfListItem) {
  if (!client.value) {
    log('Error: Client not initialized', 'error')
    return
  }

  try {
    log(`Fetching content for: ${pdf.name}`, 'info')

    // Import the necessary types
    const { GetPdfRequest } = await import('../bibliophage/v1alpha3/pdf_pb.ts')

    // Fetch the full PDF with content
    const request = new GetPdfRequest({ id: pdf.id })
    const response = await client.value.getPdf(request)

    if (!response.success || !response.pdf) {
      log(`Failed to fetch PDF: ${response.message}`, 'error')
      return
    }

    // Open editor window with the fetched content
    openWindow({
      title: response.pdf.name,
      content: response.pdf.content || '',
      documentId: response.pdf.id,
      isNew: false,
    })

    log(`Opened editor for: ${response.pdf.name} (${response.pdf.content?.length || 0} characters)`, 'success')
  }
  catch (error) {
    log(`Error fetching PDF: ${(error as Error).message}`, 'error')
  }
}
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">
      Document List
    </h1>
    <p class="text-lg">
      Here is where we would like to have a searchable list of all documents
    </p>
  </div>

  <form @submit.prevent="handleSearchSubmit">
    <button
      type="search"
      class="btn btn-accent btn-lg gap-2"
      v-bind:disabled="loading"
    >
      <Icon v-if="!loading" icon="game-icons:magnifying-glass" class="text-xl" />
      <span v-if="loading" class="loading loading-spinner" />
      Search
    </button>
  </form>

  <div>
    <DataTable
      :data="pdfs"
      :columns="columns"
      :loading="loading"
      :enable-column-visibility="true"
      table-id="document-list"
      row-key="id"
      empty-message="No PDFs found"
      empty-description="Upload a PDF to get started"
      empty-icon="heroicons:document"
      @row-click="handleEditDocument"
    >
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

        <!-- Custom rendering for Actions column with Edit button -->
        <template #cell-actions="{ row }">
          <button
            type="button"
            class="btn btn-sm btn-primary gap-1"
            @click.stop="handleEditDocument(row)"
          >
            <Icon icon="heroicons:pencil" />
            Edit
          </button>
        </template>
      </DataTable>
    </div>
</template>
