import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

export interface ContextDocument {
  id: string
  name: string
  snippet: string
}

export interface RetrievedChunk {
  chunkId: string
  documentId: string
  documentName: string
  content: string
  similarity: number
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<DisplayMessage[]>([])
  const selectedDocuments = ref<ContextDocument[]>([])
  const isStreaming = ref(false)
  const currentStreamingMessageId = ref<string | null>(null)
  const autoRetrievalEnabled = ref(true)
  const retrievedChunks = ref<RetrievedChunk[]>([])

  const conversationHistory = computed(() =>
    messages.value.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp,
    })),
  )

  function addUserMessage(content: string): string {
    const messageId = `msg-${Date.now()}-${Math.random()}`
    messages.value.push({ id: messageId, role: 'user', content, timestamp: new Date() })
    return messageId
  }

  function startAssistantMessage(): string {
    const messageId = `msg-${Date.now()}-${Math.random()}`
    messages.value.push({
      id: messageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    })
    isStreaming.value = true
    currentStreamingMessageId.value = messageId
    return messageId
  }

  function appendToken(token: string) {
    if (!currentStreamingMessageId.value)
      return
    const message = messages.value.find(m => m.id === currentStreamingMessageId.value)
    if (message) {
      message.content += token
    }
  }

  function finishStreaming() {
    if (!currentStreamingMessageId.value)
      return
    const message = messages.value.find(m => m.id === currentStreamingMessageId.value)
    if (message) {
      message.isStreaming = false
    }
    isStreaming.value = false
    currentStreamingMessageId.value = null
  }

  function toggleContextDocument(doc: ContextDocument) {
    const index = selectedDocuments.value.findIndex(d => d.id === doc.id)
    if (index >= 0) {
      selectedDocuments.value.splice(index, 1)
    }
    else {
      selectedDocuments.value.push(doc)
    }
  }

  function clearContextDocuments() {
    selectedDocuments.value = []
  }

  function clearMessages() {
    messages.value = []
  }

  function toggleAutoRetrieval() {
    autoRetrievalEnabled.value = !autoRetrievalEnabled.value
  }

  function setAutoRetrievalEnabled(enabled: boolean) {
    autoRetrievalEnabled.value = enabled
  }

  function setRetrievedChunks(chunks: RetrievedChunk[]) {
    retrievedChunks.value = chunks
  }

  function clearRetrievedChunks() {
    retrievedChunks.value = []
  }

  return {
    messages,
    selectedDocuments,
    isStreaming,
    autoRetrievalEnabled,
    retrievedChunks,
    conversationHistory,
    addUserMessage,
    startAssistantMessage,
    appendToken,
    finishStreaming,
    toggleContextDocument,
    clearContextDocuments,
    clearMessages,
    toggleAutoRetrieval,
    setAutoRetrievalEnabled,
    setRetrievedChunks,
    clearRetrievedChunks,
  }
})
