<script setup lang="ts">
import type { DocumentListItem } from '../bibliophage/v1alpha3/document_pb.ts'
import type { TableColumn } from './DataTable.vue'

import { Icon } from '@iconify/vue'
import { computed } from 'vue'

import { DocumentType } from '../bibliophage/v1alpha3/document_pb.ts'
import DataTable from './DataTable.vue'

interface Props {
  /** Array of documents to display */
  data: DocumentListItem[]
  /** Loading state */
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  /** Emitted when user wants to edit a document */
  edit: [document: DocumentListItem]
  /** Emitted when user wants to embed a document */
  embed: [document: DocumentListItem]
}>()

/**
 * v-model for selected document IDs
 */
const selectedIds = defineModel<Set<string | number>>({ default: () => new Set() })

/**
 * Format DocumentType enum to display string using TypeScript reverse mapping.
 * Returns the technical enum name (e.g., "LORE_FRAGMENT").
 */
function formatDocumentType(type: DocumentType): string {
  return DocumentType[type] ?? 'UNKNOWN'
}

/**
 * Format timestamp for display
 */
function formatDate(timestamp: { toDate: () => Date } | null | undefined): string {
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
 * Define table columns for document list
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
    key: 'systems',
    label: 'Systems',
  },
  {
    key: 'type',
    label: 'Type',
    formatter: value => formatDocumentType(value),
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
    key: 'embeddingStatus',
    label: 'Embedding Status',
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

function handleRowClick(row: DocumentListItem) {
  emit('edit', row)
}

function handleEdit(row: DocumentListItem) {
  emit('edit', row)
}

function handleEmbed(row: DocumentListItem) {
  emit('embed', row)
}
</script>

<template>
  <DataTable
    v-model="selectedIds"
    v-bind:data="data"
    v-bind:columns="columns"
    v-bind:loading="loading"
    v-bind:enable-column-visibility="true"
    v-bind:selectable="true"
    v-bind:select-on-row-click="false"
    table-id="document-list"
    row-key="id"
    empty-message="No documents found"
    empty-description="Upload a PDF or create a new entry to get started"
    empty-icon="heroicons:document"
    @row-click="handleRowClick"
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

    <!-- Custom rendering for Embedding Status column with badges -->
    <template #cell-embeddingStatus="{ row }">
      <div class="flex gap-1 flex-wrap">
        <span
          v-if="!row.embeddingStatus"
          class="badge badge-sm badge-ghost"
        >
          Not Embedded
        </span>
        <span
          v-else-if="!row.embeddingStatus.isEmbedded"
          class="badge badge-sm badge-info"
        >
          Not Embedded
        </span>
        <span
          v-else-if="!row.embeddingStatus.embeddingsCurrent"
          class="badge badge-sm badge-warning"
        >
          Stale
        </span>
        <span
          v-else
          class="badge badge-sm badge-success"
        >
          Current ({{ row.embeddingStatus.totalChunks }})
        </span>
      </div>
    </template>

    <!-- Custom rendering for Tags column -->
    <template #cell-tags="{ row }">
      <div class="flex gap-1 flex-wrap">
        <span v-for="tag in row.tags" v-bind:key="tag.name" class="badge badge-sm badge-secondary">
          {{ tag.name }}: {{ tag.values.join(', ') }}
        </span>
        <span v-if="row.tags.length === 0" class="text-sm text-base-content/50">
          -
        </span>
      </div>
    </template>

    <!-- Custom rendering for Actions column with Edit and Embed buttons -->
    <template #cell-actions="{ row }">
      <div class="flex gap-2">
        <button
          type="button"
          class="btn btn-sm btn-primary gap-1"
          @click.stop="handleEdit(row)"
        >
          <Icon icon="heroicons:pencil" />
          Edit
        </button>
        <button
          type="button"
          class="btn btn-sm btn-accent gap-1"
          @click.stop="handleEmbed(row)"
        >
          <Icon icon="heroicons:cube" />
          Embed
        </button>
      </div>
    </template>
  </DataTable>
</template>
