<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

const message = ref('')

function handleSend() {
  const text = message.value.trim()
  if (!text)
    return

  emit('send', text)

  // Clear input after sending
  message.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  // Send on Cmd+Enter or Ctrl+Enter
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="border border-base-300 rounded-lg bg-base-100">
    <textarea
      v-model="message"
      class="textarea w-full min-h-[80px] max-h-[200px] resize-none focus:outline-none border-0 rounded-b-none"
      placeholder="Type your message..."
      v-bind:disabled="disabled"
      @keydown="handleKeydown"
    />
    <div class="border-t border-base-300 p-2 flex justify-between items-center">
      <span class="text-xs text-base-content/50"> Press Cmd+Enter to send </span>
      <button class="btn btn-primary btn-sm" v-bind:disabled="disabled" @click="handleSend">
        <Icon icon="heroicons:paper-airplane" />
        Send
      </button>
    </div>
  </div>
</template>
