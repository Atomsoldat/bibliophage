<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ChunkType } from '../bibliophage/v1alpha3/chat_pb'
import ChatInput from '../components/chat/ChatInput.vue'
import ChatMessage from '../components/chat/ChatMessage.vue'
import DocumentPicker from '../components/chat/DocumentPicker.vue'
import { useChatApi } from '../composables/useChatApi'
import { useChatStore } from '../stores/chat'
import { useLogger } from '../composables/useLogger'

const chatApi = useChatApi()
const chat = useChatStore()
const logger = useLogger()

const messagesContainer = ref<HTMLElement | null>(null)
const currentMetadata = ref<any>(null)

onMounted(async () => {
  await chatApi.initialise()
})

async function handleSend(message: string) {
  chat.addUserMessage(message)
  chat.startAssistantMessage()
  await scrollToBottom()

  logger.debug('Starting chat stream', {
    message,
    contextDocs: chat.selectedDocuments.length,
  })

  try {
    chat.clearRetrievedChunks()

    await chatApi.streamChat(
      message,
      Array.from(chat.selectedDocuments).map(d => d.id),
      [],
      (chunk) => {
        if (chunk.type === ChunkType.TOKEN) {
          chat.appendToken(chunk.content)
          scrollToBottom()
        }
        else if (chunk.type === ChunkType.METADATA) {
          currentMetadata.value = chunk.metadata
          if (chunk.metadata?.retrievedChunks) {
            chat.setRetrievedChunks(
              chunk.metadata.retrievedChunks.map(c => ({
                chunkId: c.chunkId,
                documentId: c.documentId,
                documentName: c.documentName,
                content: c.content,
                similarity: c.similarity,
              })),
            )
          }
          const docCount = chunk.metadata?.contextDocuments.length || 0
          const chunkCount = chunk.metadata?.retrievedChunks.length || 0
          logger.notify(
            `Using ${docCount} documents, ${chunkCount} auto-retrieved chunks`,
            'info',
          )
          logger.debug('Context metadata', chunk.metadata)
        }
        else if (chunk.type === ChunkType.DONE) {
          chat.finishStreaming()
          logger.success('Response complete')
        }
        else if (chunk.type === ChunkType.ERROR) {
          chat.finishStreaming()
          logger.error(`Error: ${chunk.content}`)
        }
      },
      { enableAutoRetrieval: chat.autoRetrievalEnabled },
    )
  }
  catch (error) {
    chat.finishStreaming()
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
            v-if="chat.messages.length === 0"
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
              v-for="msg in chat.messages"
              v-bind:key="msg.id"
              v-bind:message="msg"
            />
          </div>
        </div>

        <!-- Input -->
        <ChatInput v-bind:disabled="chat.isStreaming" @send="handleSend" />
      </div>

      <!-- Sidebar: Document picker -->
      <div class="w-96 flex-shrink-0">
        <DocumentPicker />
      </div>
    </div>
  </div>
</template>
