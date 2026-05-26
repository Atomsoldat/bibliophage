import { defineStore } from 'pinia'
import { ref } from 'vue'

// TODO: Do we really need the success type?
export type ConsoleMessageType = 'info' | 'success' | 'error' | 'warning'

export interface ConsoleMessage {
  message: string
  type: ConsoleMessageType
  timestamp: Date
}

const MAX_MESSAGES = 1000

export const useConsoleStore = defineStore('console', () => {
  const messages = ref<ConsoleMessage[]>([])
  const isVisible = ref(false)
  const unreadCount = ref(0)

  function log(message: string, type: ConsoleMessageType = 'info'): void {
    if (messages.value.length >= MAX_MESSAGES) {
      messages.value.shift()
    }
    messages.value.push({ message, type, timestamp: new Date() })
    if (!isVisible.value) {
      unreadCount.value++
    }
  }

  function toggleVisibility(): void {
    isVisible.value = !isVisible.value
    if (isVisible.value) {
      unreadCount.value = 0
    }
  }

  function show(): void {
    isVisible.value = true
    unreadCount.value = 0
  }

  function hide(): void {
    isVisible.value = false
  }

  function clear(): void {
    messages.value = []
    unreadCount.value = 0
  }

  return { messages, isVisible, unreadCount, log, toggleVisibility, show, hide, clear }
})
