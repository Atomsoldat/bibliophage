import { computed, readonly, ref } from 'vue'

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean // True while assistant message is being streamed
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

// Shared state
const messages = ref<DisplayMessage[]>([])
const selectedDocuments = ref<ContextDocument[]>([])
const isStreaming = ref(false)
const currentStreamingMessageId = ref<string | null>(null)
const autoRetrievalEnabled = ref(true)
const retrievedChunks = ref<RetrievedChunk[]>([])

/**
 * Composable for managing chat UI state
 *
 * Handles message history, streaming state, and selected context documents.
 */
export function useChatState() {
  /**
   * Add a user message to the chat
   */
  function addUserMessage(content: string): string {
    const messageId = `msg-${Date.now()}-${Math.random()}`
    messages.value.push({
      id: messageId,
      role: 'user',
      content,
      timestamp: new Date(),
    })
    return messageId
  }

  /**
   * Start streaming an assistant message
   */
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

  /**
   * Append a token to the current streaming message
   */
  function appendToken(token: string) {
    if (!currentStreamingMessageId.value)
      return

    const message = messages.value.find(m => m.id === currentStreamingMessageId.value)
    if (message) {
      message.content += token
    }
  }

  /**
   * Complete the current streaming message
   */
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

  /**
   * Add or remove a context document
   */
  function toggleContextDocument(doc: ContextDocument) {
    const index = selectedDocuments.value.findIndex(d => d.id === doc.id)
    if (index >= 0) {
      selectedDocuments.value.splice(index, 1)
    }
    else {
      selectedDocuments.value.push(doc)
    }
  }

  /**
   * Clear all selected documents
   */
  function clearContextDocuments() {
    selectedDocuments.value = []
  }

  /**
   * Clear all messages
   */
  function clearMessages() {
    messages.value = []
  }

  /**
   * Toggle auto-retrieval feature
   */
  function toggleAutoRetrieval() {
    autoRetrievalEnabled.value = !autoRetrievalEnabled.value
  }

  /**
   * Set auto-retrieval enabled state
   */
  function setAutoRetrievalEnabled(enabled: boolean) {
    autoRetrievalEnabled.value = enabled
  }

  /**
   * Set retrieved chunks from the latest query
   */
  function setRetrievedChunks(chunks: RetrievedChunk[]) {
    retrievedChunks.value = chunks
  }

  /**
   * Clear retrieved chunks
   */
  function clearRetrievedChunks() {
    retrievedChunks.value = []
  }

  /**
   * Get conversation history in ChatMessage format for API
   */
  const conversationHistory = computed(() => {
    return messages.value.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp,
    }))
  })

  return {
    messages: readonly(messages),
    selectedDocuments: readonly(selectedDocuments),
    isStreaming: readonly(isStreaming),
    autoRetrievalEnabled,
    retrievedChunks: readonly(retrievedChunks),
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
    conversationHistory,
  }
}
