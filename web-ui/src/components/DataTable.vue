<script setup lang="ts" generic="T extends Record<string, any>">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useColumnVisibility } from '../composables/useColumnVisibility'

/**
 * Column definition for the data table
 */
export interface TableColumn<T = any> {
  /** Unique key for the column, also used to access row property */
  key: string
  /** Display label in the table header */
  label: string
  /** Optional formatter function to transform the cell value */
  formatter?: (value: any, row: T, index: number) => string | number
  /** Optional CSS classes for table cells in this column */
  cellClass?: string
  /** Optional CSS classes for the column header */
  headerClass?: string
  /** Mark column as required (always visible, cannot be hidden) */
  required?: boolean
}

/**
 * Props for the DataTable component
 */
interface Props {
  /** Array of data items to display */
  data: T[]
  /** Column definitions */
  columns: TableColumn<T>[]
  /** Loading state - shows spinner when true */
  loading?: boolean
  /** Whether to show selection checkboxes */
  selectable?: boolean
  /** Property name to use as unique row key */
  rowKey?: keyof T
  /** Message to display when table is empty */
  emptyMessage?: string
  /** Additional description for empty state */
  emptyDescription?: string
  /** Icon to display in empty state */
  emptyIcon?: string
  /** Enable column visibility controls */
  enableColumnVisibility?: boolean
  /** Unique identifier for this table instance (for localStorage key) */
  tableId?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  selectable: false,
  rowKey: 'id' as keyof T,
  emptyMessage: 'No data available',
  emptyDescription: 'There are no items to display',
  emptyIcon: 'heroicons:document-text',
  enableColumnVisibility: false,
  tableId: 'default',
})

/**
 * Events emitted by the component
 */
const emit = defineEmits<{
  /** Emitted when a row is clicked */
  rowClick: [row: T, index: number]
}>()

/**
 * v-model for selected row IDs
 */
const selectedIds = defineModel<Set<string | number>>({ default: () => new Set() })

/**
 * Helper to get nested property value from an object
 * Supports dot notation like 'user.name'
 */
function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, prop) => current?.[prop], obj)
}

/**
 * Format cell value using column's formatter or return raw value
 */
function formatCell(row: T, column: TableColumn<T>, index: number): string | number {
  const value = getNestedValue(row, column.key)
  return column.formatter ? column.formatter(value, row, index) : value
}

/**
 * Get the unique key for a row
 */
function getRowKey(row: T): string | number {
  return row[props.rowKey] as string | number
}

/**
 * Toggle selection for a single row
 */
function toggleSelection(row: T) {
  const key = getRowKey(row)
  const newSelection = new Set(selectedIds.value)

  if (newSelection.has(key)) {
    newSelection.delete(key)
  }
  else {
    newSelection.add(key)
  }

  selectedIds.value = newSelection
}

/**
 * Toggle selection for all rows
 */
function toggleSelectAll() {
  if (selectedIds.value.size === props.data.length) {
    selectedIds.value = new Set()
  }
  else {
    selectedIds.value = new Set(props.data.map(getRowKey))
  }
}

/**
 * Computed property to check if all rows are selected
 */
const isAllSelected = computed(() => {
  return props.data.length > 0 && selectedIds.value.size === props.data.length
})

/**
 * Column visibility management (conditionally initialized)
 */
const columnVisibility = props.enableColumnVisibility
  ? useColumnVisibility(computed(() => props.columns), props.tableId)
  : null

/**
 * Columns to display (filtered by visibility when feature is enabled)
 */
const displayColumns = computed(() => {
  return props.enableColumnVisibility && columnVisibility
    ? columnVisibility.visibleColumns.value
    : props.columns
})

/**
 * Check if a column is visible
 */
function isColumnVisible(key: string): boolean {
  return columnVisibility?.isColumnVisible(key) ?? true
}

/**
 * Toggle column visibility
 */
function toggleColumn(key: string): void {
  columnVisibility?.toggleColumn(key)
}

/**
 * Get visibility statistics
 */
const visibilityStats = computed(() => {
  return columnVisibility?.visibilityStats.value ?? {
    total: props.columns.length,
    visible: props.columns.length,
    required: 0,
    hideable: props.columns.length,
    hidden: 0,
  }
})

/**
 * Reset all columns to default visibility
 */
function resetToDefaults(): void {
  columnVisibility?.resetToDefaults()
}

/**
 * Handle row click event
 */
function handleRowClick(row: T, index: number) {
  emit('rowClick', row, index)
}
</script>

<template>
  <!-- Loading indicator -->
  <div v-if="loading && data.length === 0" class="flex justify-center items-center p-8">
    <span class="loading loading-spinner loading-lg" />
  </div>

  <!-- Data table -->
  <div v-else-if="data.length > 0" class="overflow-x-auto">
    <table class="table table-zebra">
      <thead>
        <tr>
          <th v-if="selectable">
            <input
              type="checkbox"
              class="checkbox"
              :checked="isAllSelected"
              @change="toggleSelectAll"
            />
          </th>
          <th
            v-for="column in displayColumns"
            :key="column.key"
            :class="column.headerClass"
          >
            {{ column.label }}
          </th>
          <!-- Column visibility dropdown -->
          <th v-if="enableColumnVisibility" class="w-12">
            <div class="dropdown dropdown-end">
              <button
                type="button"
                tabindex="0"
                class="btn btn-ghost btn-sm btn-circle"
                title="Show/hide columns"
              >
                <Icon icon="heroicons:view-columns" class="text-lg" />
              </button>
              <div
                tabindex="0"
                class="dropdown-content z-[1] menu p-2 shadow-lg bg-base-100 rounded-box w-64 border border-base-300"
              >
                <div class="px-2 py-1 text-xs font-semibold text-base-content/60 border-b border-base-300 mb-1">
                  Column Visibility
                </div>

                <!-- Column visibility checkboxes -->
                <label
                  v-for="column in columns"
                  :key="column.key"
                  class="label cursor-pointer justify-start gap-2 px-2 hover:bg-base-200 rounded"
                >
                  <input
                    type="checkbox"
                    class="checkbox checkbox-sm"
                    :checked="isColumnVisible(column.key)"
                    :disabled="column.required"
                    @change="toggleColumn(column.key)"
                  />
                  <span class="label-text flex-1" :class="{ 'text-base-content/40': column.required }">
                    {{ column.label }}
                  </span>
                  <span v-if="column.required" class="badge badge-xs">Required</span>
                </label>

                <!-- Stats and reset button -->
                <div class="divider my-1" />
                <div class="px-2 flex justify-between items-center">
                  <span class="text-xs text-base-content/60">
                    {{ visibilityStats.visible }} / {{ visibilityStats.total }} visible
                  </span>
                  <button
                    type="button"
                    class="btn btn-ghost btn-xs"
                    @click="resetToDefaults"
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in data"
          :key="getRowKey(row)"
          class="hover"
          @click="handleRowClick(row, index)"
        >
          <td v-if="selectable" @click.stop>
            <input
              type="checkbox"
              class="checkbox"
              :checked="selectedIds.has(getRowKey(row))"
              @change="toggleSelection(row)"
            />
          </td>
          <td
            v-for="column in displayColumns"
            :key="column.key"
            :class="column.cellClass"
          >
            <slot
              :name="`cell-${column.key}`"
              :value="getNestedValue(row, column.key)"
              :row="row"
              :index="index"
              :column="column"
            >
              {{ formatCell(row, column, index) }}
            </slot>
          </td>
          <!-- Empty cell to align with header's dropdown column -->
          <td v-if="enableColumnVisibility" />
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Empty state -->
  <div v-else class="text-center p-12">
    <Icon :icon="emptyIcon" class="text-6xl text-base-content/30 mx-auto mb-4" />
    <p class="text-lg text-base-content/70">
      {{ emptyMessage }}
    </p>
    <p class="text-sm text-base-content/50 mt-2">
      {{ emptyDescription }}
    </p>
  </div>
</template>
