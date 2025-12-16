import { readonly, ref } from 'vue'

// TODO: Do we really need the success type?
/**
 * Console message types for different log levels
 */
export type ConsoleMessageType = 'info' | 'success' | 'error' | 'warning'

/**
 * Structure of a console message
 */
export interface ConsoleMessage {
  message: string
  type: ConsoleMessageType
  timestamp: Date
}

// Ring buffer configuration
const MAX_MESSAGES = 1000

// Shared state across all component instances
const messages = ref<ConsoleMessage[]>([])
const isVisible = ref(false)
const unreadCount = ref(0)

/**
 * Composable for global application console
 *
 * Provides a Quake-style console that can be toggled and accessed from any component.
 * Uses a ring buffer to prevent memory issues with large message counts.
 *
 * @example
 * const { log, toggleVisibility, isVisible } = useAppConsole()
 * log("Processing PDF...", "info")
 * log("Upload successful!", "success")
 */
export function useAppConsole() {
  /**
   * Add a message to the console
   * Implements ring buffer - when full, oldest messages are dropped
   */
  function log(message: string, type: ConsoleMessageType = 'info'): void {
    const newMessage: ConsoleMessage = {
      message,
      type,
      timestamp: new Date(),
    }

    // Ring buffer: if at capacity, remove oldest message
    if (messages.value.length >= MAX_MESSAGES) {
      messages.value.shift()
    }

    messages.value.push(newMessage)

    // Increment unread count if console is hidden
    if (!isVisible.value) {
      unreadCount.value++
    }
  }

  /**
   * Toggle console visibility
   */
  function toggleVisibility(): void {
    isVisible.value = !isVisible.value

    // Reset unread count when showing console
    if (isVisible.value) {
      unreadCount.value = 0
    }
  }

  /**
   * Show the console
   */
  function show(): void {
    isVisible.value = true
    unreadCount.value = 0
  }

  /**
   * Hide the console
   */
  function hide(): void {
    isVisible.value = false
  }

  /**
   * Clear all messages
   */
  function clear(): void {
    messages.value = []
    unreadCount.value = 0
  }

  return {
    messages: readonly(messages),
    isVisible: readonly(isVisible),
    unreadCount: readonly(unreadCount),
    log,
    toggleVisibility,
    show,
    hide,
    clear,
  }
}
