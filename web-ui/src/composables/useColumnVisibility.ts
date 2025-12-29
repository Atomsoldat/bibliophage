import type { Ref } from 'vue'
import { computed, watch } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import type { TableColumn } from '../components/DataTable.vue'

/**
 * Column visibility state structure
 * Maps column keys to visibility (true = visible, false = hidden)
 */
export interface ColumnVisibilityState {
  [columnKey: string]: boolean
}

/**
 * Statistics about column visibility
 */
export interface VisibilityStats {
  total: number
  visible: number
  required: number
  hideable: number
  hidden: number
}

/**
 * Composable for managing column visibility with localStorage persistence
 *
 * Provides reactive column visibility state that persists across sessions.
 * Each table instance has isolated state based on its tableId.
 *
 * @param columns - Reactive reference to table column definitions
 * @param tableId - Unique identifier for this table (used in localStorage key)
 * @returns Object with visibility state and control functions
 *
 * @example
 * const { visibleColumns, toggleColumn, isColumnVisible } = useColumnVisibility(
 *   computed(() => props.columns),
 *   'document-list'
 * )
 */
export function useColumnVisibility<T>(
  columns: Ref<TableColumn<T>[]>,
  tableId: string,
) {
  // Storage key for this specific table
  const storageKey = `datatable-columns-${tableId}`

  /**
   * Initialize default state with all columns visible
   */
  const getDefaultState = (): ColumnVisibilityState => {
    const state: ColumnVisibilityState = {}
    columns.value.forEach((col) => {
      state[col.key] = true // All columns visible by default
    })
    return state
  }

  /**
   * Reactive localStorage state using @vueuse/core
   * Automatically syncs with localStorage and handles serialization
   */
  const visibilityState = useLocalStorage<ColumnVisibilityState>(
    storageKey,
    getDefaultState(),
    {
      mergeDefaults: true, // Merge with defaults for new columns
    },
  )

  /**
   * Toggle visibility for a column
   * Required columns cannot be toggled and will remain visible
   */
  const toggleColumn = (columnKey: string) => {
    const column = columns.value.find(col => col.key === columnKey)
    if (column?.required) {
      // Don't toggle required columns
      return
    }
    visibilityState.value[columnKey] = !visibilityState.value[columnKey]
  }

  /**
   * Filter columns based on visibility state
   * Required columns are always included regardless of visibility state
   */
  const visibleColumns = computed(() => {
    return columns.value.filter((col) => {
      // Required columns are always visible
      if (col.required)
        return true

      // Check visibility state (default to visible if not set)
      return visibilityState.value[col.key] !== false
    })
  })

  /**
   * Check if a specific column is visible
   */
  const isColumnVisible = (columnKey: string): boolean => {
    const column = columns.value.find(col => col.key === columnKey)
    // Required columns are always visible
    if (column?.required)
      return true
    // Default to visible if not explicitly hidden
    return visibilityState.value[columnKey] !== false
  }

  /**
   * Get statistics about column visibility
   */
  const visibilityStats = computed((): VisibilityStats => {
    const total = columns.value.length
    const required = columns.value.filter(col => col.required).length
    const hideable = total - required
    const hidden = columns.value.filter(
      col => !col.required && visibilityState.value[col.key] === false,
    ).length
    const visible = total - hidden

    return { total, required, hideable, hidden, visible }
  })

  /**
   * Reset all columns to default visibility (all visible)
   */
  const resetToDefaults = () => {
    visibilityState.value = getDefaultState()
  }

  /**
   * Watch for column definition changes and sync new columns
   * When new columns are added, they default to visible
   */
  watch(
    () => columns.value.length,
    () => {
      const currentState = visibilityState.value
      const newState = getDefaultState()

      // Merge: keep existing preferences, add new columns as visible
      Object.keys(newState).forEach((key) => {
        if (!(key in currentState)) {
          currentState[key] = true
        }
      })

      visibilityState.value = currentState
    },
  )

  return {
    visibleColumns,
    visibilityState,
    toggleColumn,
    isColumnVisible,
    visibilityStats,
    resetToDefaults,
  }
}
