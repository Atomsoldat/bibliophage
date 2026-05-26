<script setup lang="ts">
import type { ConsoleMessageType } from '../stores/console'
import { Icon } from '@iconify/vue'
import { nextTick, ref, watch } from 'vue'
import { useConsoleStore } from '../stores/console'

const { messages, isVisible, unreadCount, toggleVisibility, clear } = useConsoleStore()

// Ref to scroll container for auto-scroll
const messagesContainer = ref<HTMLElement | null>(null)

// Auto-scroll to bottom when new messages arrive
watch(messages, async () => {
  if (isVisible.value && messagesContainer.value) {
    await nextTick()
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}, { deep: true })

// Also scroll when console becomes visible
watch(isVisible, async (visible) => {
  if (visible && messagesContainer.value) {
    await nextTick()
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
})

// Get icon for message type
function getMessageIcon(type: ConsoleMessageType): string {
  switch (type) {
    case 'success': return 'heroicons:check-circle'
    case 'error': return 'heroicons:x-circle'
    case 'warning': return 'heroicons:exclamation-triangle'
    case 'info':
    default: return 'heroicons:information-circle'
  }
}

// Get color classes for message type
function getMessageClasses(type: ConsoleMessageType): string {
  switch (type) {
    case 'success': return 'text-success'
    case 'error': return 'text-error'
    case 'warning': return 'text-warning'
    case 'info':
    default: return 'text-info'
  }
}

// Format timestamp
function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
</script>

<template>
  <!-- Toggle Button - Fixed position in bottom-right corner -->
  <button
    class="btn btn-circle btn-primary fixed bottom-4 right-4 z-50 shadow-lg"
    v-bind:class="{ 'btn-accent': unreadCount > 0 }"
    @click="toggleVisibility"
  >
    <div class="indicator">
      <Icon icon="heroicons:command-line" class="text-xl" />
      <span v-if="unreadCount > 0" class="indicator-item badge badge-secondary badge-sm">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </div>
  </button>

  <!-- Console Panel - Part of layout flow, respects sidebar -->
  <div
    v-if="isVisible"
    class="ml-16 bg-base-300 shadow-2xl border-t-4 border-primary transition-all duration-300 ease-out"
    style="height: 50vh;"
  >
    <!-- Console Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-base-200 border-b border-base-300">
      <div class="flex items-center gap-2">
        <Icon icon="heroicons:command-line" class="text-xl text-primary" />
        <h3 class="font-bold text-lg">
          Application Console
        </h3>
        <span class="badge badge-sm">{{ messages.length }} / 1000</span>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-ghost gap-1" @click="clear">
          <Icon icon="heroicons:trash" />
          Clear
        </button>
        <button class="btn btn-sm btn-ghost gap-1" @click="toggleVisibility">
          <Icon icon="heroicons:chevron-down" />
          Hide
        </button>
      </div>
    </div>

    <!-- Messages Container -->
    <div
      ref="messagesContainer"
      class="overflow-y-auto p-4 font-mono text-sm h-full bg-base-300"
      style="height: calc(100% - 3.5rem);"
    >
      <div v-if="messages.length === 0" class="text-base-content/50 text-center py-8">
        No messages yet. Console output will appear here.
      </div>
      <div
        v-for="(msg, index) in messages"
        v-bind:key="index"
        class="mb-2 flex gap-2 items-start"
      >
        <span class="text-base-content/50 text-xs whitespace-nowrap">
          {{ formatTime(msg.timestamp) }}
        </span>
        <Icon
          v-bind:icon="getMessageIcon(msg.type)"
          v-bind:class="getMessageClasses(msg.type)"
          class="text-base mt-0.5"
        />
        <span v-bind:class="getMessageClasses(msg.type)" class="flex-1 break-words">
          {{ msg.message }}
        </span>
      </div>
    </div>
  </div>
</template>
