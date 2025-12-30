<script setup lang="ts">
import type { Client } from '@connectrpc/connect'
import type { PdfListItem } from '../bibliophage/v1alpha3/pdf_pb.ts'
import type { TableColumn } from '../components/DataTable.vue'

import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'
import { Icon } from '@iconify/vue'
import { computed, onBeforeMount, ref, watch } from 'vue'

import { SortOrder } from '../bibliophage/v1alpha3/common_pb.ts'
import { PdfService } from '../bibliophage/v1alpha3/pdf_connect.ts'
import { SearchPdfsRequest } from '../bibliophage/v1alpha3/pdf_pb.ts'
import DataTable from '../components/DataTable.vue'
import { useConfig } from '../composables/useConfig.ts'
import { useEditorWindows } from '../composables/useEditorWindows.ts'
import { useLogger } from '../composables/useLogger.ts'

const { config, loadConfig } = useConfig()
const logger = useLogger()
const { openWindow } = useEditorWindows()

// Client will be initialized after config loads
// see https://connectrpc.com/docs/node/using-clients/#connect
const client = ref<Client<typeof PdfService> | null>(null)

const pdfs = ref<PdfListItem[]>([])
const loading = ref(false)

// Search filter parameters
const titleQuery = ref('')
const systemFiltersInput = ref('') // User input for systems (comma-separated)
const systemFilters = ref<string[]>([]) // Parsed array of system filters
const typeFilter = ref('')
const pageSize = ref(20)
const pageNumber = ref(0)

// Watch systemFiltersInput and parse it into systemFilters array
watch(systemFiltersInput, (newValue) => {
  if (!newValue.trim()) {
    systemFilters.value = []
    return
  }

  // Split by comma, trim whitespace, and filter out empty strings
  systemFilters.value = newValue
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)
})

/**
 * Format file size in bytes to human-readable format (KB, MB, GB)
 */
function formatFileSize(bytes: number | bigint): string {
  if (bytes === 0 || bytes === 0n)
    return '0 B'

  const numBytes = typeof bytes === 'bigint' ? Number(bytes) : bytes
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  const kibibyte = 1024
  const magnitude = Math.floor(Math.log(numBytes) / Math.log(kibibyte))

  return `${(numBytes / kibibyte ** magnitude).toFixed(2)} ${units[magnitude]}`
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
    formatter: value => formatDate(value),
  },
  {
    key: 'updatedAt',
    label: 'Updated',
    formatter: value => formatDate(value),
  },
  {
    key: 'fileSize',
    label: 'Size',
    formatter: value => formatFileSize(value),
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
    tagFilters: [], // Tag filtering not implemented yet
    pageSize: pageSize.value,
    pageNumber: pageNumber.value,
    sortOrder: SortOrder.NAME_ASC,
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
    const request = buildSearchPdfsRequest()
    logger.info('Searching for PDFs...')

    const response = await client.value.searchPdfs(request)

    // Store the results
    pdfs.value = response.pdfs
    logger.success(`Success! Found ${response.totalCount} PDFs`)
    logger.info(`Returned ${response.pdfs.length} results on page ${response.pageNumber}`)
  }
  catch (error) {
    logger.error(`Error during PDF search: ${(error as Error).message}`)
  }
  finally {
    loading.value = false
  }
}

// Open a global editor window for the selected document
async function handleEditDocument(pdf: PdfListItem) {
  if (!client.value) {
    logger.error('Error: Client not initialized')
    return
  }

  try {
    logger.info(`Fetching content for: ${pdf.name}`)

    // Import the necessary types
    const { GetPdfRequest } = await import('../bibliophage/v1alpha3/pdf_pb.ts')

    // Fetch the full PDF with content
    const request = new GetPdfRequest({ id: pdf.id })
    const response = await client.value.getPdf(request)

    if (!response.success || !response.pdf) {
      logger.error(`Failed to fetch PDF: ${response.message}`)
      return
    }

    // Open editor window with the fetched content
    openWindow({
      title: response.pdf.name,
      content: response.pdf.content || '',
      documentId: response.pdf.id,
      isNew: false,
    })

    logger.success(`Opened editor for: ${response.pdf.name} (${response.pdf.content?.length || 0} characters)`)
  }
  catch (error) {
    logger.error(`Error fetching PDF: ${(error as Error).message}`)
  }
}
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">
      Library
    </h1>
    <p class="text-lg">
      Here is where we would like to have a searchable list of all imported documents ( PDFs, Text Files, ...)
    </p>
  </div>

  <form @submit.prevent="handleSearchSubmit" class="card bg-base-200 shadow-xl p-6 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <!-- Name Search Input -->
      <div class="form-control">
        <label class="label" for="title-search">
          <span class="label-text">Document Name</span>
        </label>
        <input
          id="title-search"
          v-model="titleQuery"
          type="text"
          placeholder="Search by name..."
          class="input input-bordered w-full"
        />
      </div>

      <!-- System Filters Input -->
      <div class="form-control">
        <label class="label" for="system-search">
          <span class="label-text">Systems (comma-separated)</span>
        </label>
        <input
          id="system-search"
          v-model="systemFiltersInput"
          type="text"
          placeholder="e.g., Pathfinder 1e, Call of Cthulhu"
          class="input input-bordered w-full"
        />
      </div>
    </div>

    <!-- Search Button -->
    <div class="flex justify-end">
      <button
        type="submit"
        class="btn btn-accent btn-lg gap-2"
        v-bind:disabled="loading"
      >
        <Icon v-if="!loading" icon="game-icons:magnifying-glass" class="text-xl" />
        <span v-if="loading" class="loading loading-spinner" />
        Search
      </button>
    </div>
  </form>

  <div>
    <DataTable
      v-bind:data="pdfs"
      v-bind:columns="columns"
      v-bind:loading="loading"
      v-bind:enable-column-visibility="true"
      v-bind:selectable="true"
      v-bind:select-on-row-click="false"
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
