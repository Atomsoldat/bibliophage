import { ref, watch } from 'vue'

// Simple trigger counter - incrementing it signals that journal should refresh
const refreshTrigger = ref(0)

/**
 * Minimal composable for triggering journal refreshes across components
 * No state management - just a signal to refetch from backend
 */
export function useJournalRefresh() {
  /**
   * Trigger a refresh of the journal list
   * Call this after creating/updating/deleting journal documents
   */
  function triggerRefresh() {
    refreshTrigger.value++
  }

  /**
   * Watch for refresh triggers and execute callback
   * Use in Journal.vue to refetch when triggered
   */
  function onRefreshTriggered(callback: () => void) {
    watch(refreshTrigger, () => {
      if (refreshTrigger.value > 0) {
        callback()
      }
    })
  }

  return {
    triggerRefresh,
    onRefreshTriggered,
  }
}
