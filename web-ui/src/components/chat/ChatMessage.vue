<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { marked } from 'marked'
import type { DisplayMessage } from '../../composables/useChatState'

const props = defineProps<{
  message: DisplayMessage
}>()

// Render markdown content
const renderedContent = computed(() => {
  return marked.parse(props.message.content)
})

// Format timestamp
const formattedTime = computed(() => {
  return props.message.timestamp.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
})
</script>

<template>
  <div class="chat" :class="message.role === 'user' ? 'chat-end' : 'chat-start'">
    <div class="chat-image avatar">
      <div class="w-10 rounded-full bg-base-300 flex items-center justify-center">
        <Icon
          :icon="message.role === 'user' ? 'heroicons:user' : 'heroicons:cpu-chip'"
          class="text-lg"
        />
      </div>
    </div>
    <div class="chat-header mb-1">
      {{ message.role === 'user' ? 'You' : 'Minion' }}
      <time class="text-xs opacity-50 ml-1">{{ formattedTime }}</time>
    </div>
    <div
      class="chat-bubble"
      :class="{
        'chat-bubble-primary': message.role === 'user',
        'chat-bubble-secondary': message.role === 'assistant',
      }"
    >
      <div v-html="renderedContent" class="prose prose-sm max-w-none" />
      <span v-if="message.isStreaming" class="loading loading-dots loading-sm ml-2" />
    </div>
  </div>
</template>
