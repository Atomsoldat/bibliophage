<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ChunkType } from '../bibliophage/v1alpha3/chat_pb'
import ChatInput from '../components/chat/ChatInput.vue'
import ChatMessage from '../components/chat/ChatMessage.vue'
import DocumentPicker from '../components/chat/DocumentPicker.vue'
import { useChatApi } from '../composables/useChatApi'
import { useChatState } from '../composables/useChatState'
import { useLogger } from '../composables/useLogger'

const chatApi = useChatApi()
const chatState = useChatState()
const logger = useLogger()

const messagesContainer = ref<HTMLElement | null>(null)
const currentMetadata = ref<any>(null)

onMounted(async () => {
  await chatApi.initialise()
})

async function handleSend(message: string) {
  // Add user message to UI
  chatState.addUserMessage(message)

  // Start assistant message
  chatState.startAssistantMessage()

  // Scroll to bottom
  await scrollToBottom()

  // Debug info (browser console only)
  logger.debug('Starting chat stream', {
    message,
    contextDocs: chatState.selectedDocuments.value.length,
  })

  try {
    // Stream response from backend
    await chatApi.streamChat(
      message,
      Array.from(chatState.selectedDocuments.value).map(d => d.id),
      [], // Empty history for now (can extend later with full conversation)
      (chunk) => {
        if (chunk.type === ChunkType.TOKEN) {
          chatState.appendToken(chunk.content)
          scrollToBottom()
        }
        else if (chunk.type === ChunkType.METADATA) {
          currentMetadata.value = chunk.metadata
          // User-facing notification
          logger.notify(
            `Using ${chunk.metadata?.contextDocuments.length || 0} context documents`,
            'info',
          )
          // Technical details (browser only)
          logger.debug('Context metadata', chunk.metadata)
        }
        else if (chunk.type === ChunkType.DONE) {
          chatState.finishStreaming()
          logger.success('Response complete')
        }
        else if (chunk.type === ChunkType.ERROR) {
          chatState.finishStreaming()
          // Show error to user and log details for debugging
          logger.error(`Error: ${chunk.content}`)
        }
      },
    )
  }
  catch (error) {
    chatState.finishStreaming()
    // Both consoles get error notification (default behavior)
    logger.error(`Failed to send message: ${error}`, 'both', error)
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <h1 class="text-4xl font-bold mb-4">
      LLM Chat
    </h1>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Chat area -->
      <div class="flex-1 flex flex-col min-w-0">
        <!-- Messages -->
        <div
          ref="messagesContainer"
          class="flex-1 overflow-y-auto mb-4 p-4 border border-base-300 rounded-lg bg-base-100"
        >
          <div
            v-if="chatState.messages.value.length === 0"
            class="text-center text-base-content/50 py-12"
          >
            <p class="text-lg">
              Start a conversation
            </p>
            <p class="text-sm">
              Ask a question or select context documents below
            </p>
          </div>
          <div v-else class="space-y-4">
            <ChatMessage
              v-for="msg in chatState.messages.value"
              v-bind:key="msg.id"
              v-bind:message="msg"
            />
          </div>
        </div>

        <!-- Input -->
        <ChatInput v-bind:disabled="chatState.isStreaming.value" @send="handleSend" />
      </div>

      <!-- Sidebar: Document picker -->
      <div class="w-96 flex-shrink-0">
        <DocumentPicker
          v-bind:selected-documents="chatState.selectedDocuments.value"
          @toggle="chatState.toggleContextDocument"
        />
      </div>
    </div>
  </div>
</template>
