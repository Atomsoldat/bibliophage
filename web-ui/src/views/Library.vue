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
import { DocumentService } from '../bibliophage/v1alpha3/document_connect.ts'
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
const documentClient = ref<Client<typeof DocumentService> | null>(null)

const pdfs = ref<PdfListItem[]>([])
const loading = ref(false)
const selectedIds = ref<Set<string | number>>(new Set())

// Bulk edit modal state
const showBulkEditModal = ref(false)
const bulkEditSystems = ref('')
const bulkEditType = ref('')
const bulkEditTags = ref('')

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

  // Create clients with loaded config
  const transport = createConnectTransport({
    baseUrl: config.value.backendHost,
  })
  client.value = createClient(PdfService, transport)
  documentClient.value = createClient(DocumentService, transport)

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

// Open bulk edit modal
function openBulkEditModal() {
  if (selectedIds.value.size === 0) {
    logger.warning('No documents selected for bulk edit')
    return
  }

  // Pre-populate with common values if only one item is selected
  if (selectedIds.value.size === 1) {
    const selectedId = Array.from(selectedIds.value)[0]
    const selectedPdf = pdfs.value.find(pdf => pdf.id === selectedId)
    if (selectedPdf) {
      bulkEditSystems.value = selectedPdf.systems.join(', ')
      bulkEditType.value = selectedPdf.type
      bulkEditTags.value = selectedPdf.tags.map(tag => `${tag.name}:${tag.values.join('|')}`).join(', ')
    }
  }
  else {
    // Clear fields for multiple selection
    bulkEditSystems.value = ''
    bulkEditType.value = ''
    bulkEditTags.value = ''
  }

  showBulkEditModal.value = true
}

async function handleBulkUpdate() {
  if (!documentClient.value) {
    logger.error('Error: Document client not initialized')
    return
  }

  try {
    logger.info(`Bulk updating ${selectedIds.value.size} documents...`)

    // Import necessary types
    const { GetDocumentRequest, UpdateDocumentRequest } = await import('../bibliophage/v1alpha3/document_pb.ts')
    const { Tag } = await import('../bibliophage/v1alpha3/common_pb.ts')

    // Parse input fields
    const newSystems = bulkEditSystems.value.trim()
      ? bulkEditSystems.value.split(',').map(s => s.trim()).filter(s => s.length > 0)
      : null

    const newType = bulkEditType.value.trim() || null

    // Parse tags format: "name:value1|value2, name2:value3"
    const newTags = bulkEditTags.value.trim()
      ? bulkEditTags.value.split(',').map(tagStr => {
          const [name, valuesStr] = tagStr.trim().split(':')
          if (!name || !valuesStr)
            return null
          const values = valuesStr.split('|').map(v => v.trim()).filter(v => v.length > 0)
          return { name: name.trim(), values }
        }).filter(tag => tag !== null)
      : null

    // Track results
    let successCount = 0
    let failureCount = 0
    const errors: string[] = []

    // Update each selected document
    for (const docId of selectedIds.value) {
      try {
        // Fetch the document
        const getRequest = new GetDocumentRequest({ id: String(docId) })
        const getResponse = await documentClient.value.getDocument(getRequest)

        if (!getResponse.success || !getResponse.document) {
          errors.push(`${docId}: ${getResponse.message}`)
          failureCount++
          continue
        }

        const doc = getResponse.document

        // Update only non-empty fields
        if (newSystems !== null) {
          doc.systems = newSystems
        }

        if (newType !== null) {
          // Update publication_type in metadata if it exists
          if (doc.metadata) {
            doc.metadata.publicationType = newType
          }
        }

        if (newTags !== null) {
          doc.tags = newTags.map(tagData => {
            const tag = new Tag()
            tag.name = tagData!.name
            tag.values = tagData!.values
            return tag
          })
        }

        // Send update request
        const updateRequest = new UpdateDocumentRequest({ document: doc })
        const updateResponse = await documentClient.value.updateDocument(updateRequest)

        if (updateResponse.success) {
          successCount++
        }
        else {
          errors.push(`${doc.name}: ${updateResponse.message}`)
          failureCount++
        }
      }
      catch (error) {
        errors.push(`${docId}: ${(error as Error).message}`)
        failureCount++
      }
    }

    // Report results
    if (successCount > 0) {
      logger.success(`Successfully updated ${successCount} document${successCount > 1 ? 's' : ''}`)
    }

    if (failureCount > 0) {
      logger.error(`Failed to update ${failureCount} document${failureCount > 1 ? 's' : ''}`)
      errors.forEach(err => logger.error(err))
    }

    // Close modal and refresh
    showBulkEditModal.value = false
    selectedIds.value.clear()
    await handleSearchSubmit()
  }
  catch (error) {
    logger.error(`Error during bulk update: ${(error as Error).message}`)
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

  <!-- Bulk actions toolbar (shown when items are selected) -->
  <div v-if="selectedIds.size > 0" class="alert alert-info mb-4 flex justify-between items-center">
    <div class="flex items-center gap-2">
      <Icon icon="heroicons:information-circle" class="text-xl" />
      <span>{{ selectedIds.size }} document{{ selectedIds.size > 1 ? 's' : '' }} selected</span>
    </div>
    <div class="flex gap-2">
      <button type="button" class="btn btn-sm btn-primary gap-1" @click="openBulkEditModal">
        <Icon icon="heroicons:pencil" />
        Edit Metadata
      </button>
      <button type="button" class="btn btn-sm btn-ghost gap-1" @click="selectedIds.clear()">
        <Icon icon="heroicons:x-mark" />
        Clear Selection
      </button>
    </div>
  </div>

  <div>
    <DataTable
      v-model="selectedIds"
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

  <!-- Bulk Edit Modal -->
  <dialog v-bind:open="showBulkEditModal" class="modal">
    <div class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        Edit Metadata for {{ selectedIds.size }} Document{{ selectedIds.size > 1 ? 's' : '' }}
      </h3>

      <div class="alert alert-warning mb-4">
        <Icon icon="heroicons:exclamation-triangle" class="text-xl" />
        <span>Only non-empty fields will be updated. Leave a field empty to keep existing values.</span>
      </div>

      <form @submit.prevent="handleBulkUpdate" class="space-y-4">
        <!-- Systems Input -->
        <div class="form-control">
          <label class="label" for="bulk-systems">
            <span class="label-text">Systems (comma-separated)</span>
            <span class="label-text-alt text-base-content/50">e.g., Pathfinder 1e, Call of Cthulhu</span>
          </label>
          <input
            id="bulk-systems"
            v-model="bulkEditSystems"
            type="text"
            placeholder="Leave empty to keep existing values"
            class="input input-bordered w-full"
          />
        </div>

        <!-- Type Input -->
        <div class="form-control">
          <label class="label" for="bulk-type">
            <span class="label-text">Type</span>
            <span class="label-text-alt text-base-content/50">e.g., Core Rulebook, Adventure</span>
          </label>
          <input
            id="bulk-type"
            v-model="bulkEditType"
            type="text"
            placeholder="Leave empty to keep existing values"
            class="input input-bordered w-full"
          />
        </div>

        <!-- Tags Input -->
        <div class="form-control">
          <label class="label" for="bulk-tags">
            <span class="label-text">Tags (format: name:value1|value2, name2:value3)</span>
            <span class="label-text-alt text-base-content/50">e.g., genre:fantasy|horror, campaign:storm-king</span>
          </label>
          <input
            id="bulk-tags"
            v-model="bulkEditTags"
            type="text"
            placeholder="Leave empty to keep existing values"
            class="input input-bordered w-full"
          />
        </div>

        <!-- Action Buttons -->
        <div class="modal-action">
          <button type="button" class="btn btn-ghost" @click="showBulkEditModal = false">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            Update Documents
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop" @click="showBulkEditModal = false">
      <button type="button">close</button>
    </form>
  </dialog>
</template>
