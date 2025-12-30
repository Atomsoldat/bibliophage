import type { Client } from '@connectrpc/connect'

import type { ChatMessage, ChatResponseChunk } from '../bibliophage/v1alpha3/chat_pb'
import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'

import { ref } from 'vue'
import { ChatService } from '../bibliophage/v1alpha3/chat_connect'
import { ChatRequest } from '../bibliophage/v1alpha3/chat_pb'
import { useConfig } from './useConfig'

// Shared client instance (singleton)
const client = ref<Client<typeof ChatService> | null>(null)
const isInitialised = ref(false)

/**
 * Callback for receiving streaming chunks
 */
export type StreamCallback = (chunk: ChatResponseChunk) => void

/**
 * Composable for Chat API operations
 * Provides methods to interact with the chat service
 *
 * @example
 * const api = useChatApi()
 * await api.initialise()
 *
 * // Stream chat responses
 * await api.streamChat('What is a saving throw?', [], [], (chunk) => {
 *   console.log(chunk.content)
 * })
 */
export function useChatApi() {
  const { config, loadConfig } = useConfig()

  /**
   * Initialise the API client
   * Must be called before using any API methods
   * Safe to call multiple times - only initialises once
   */
  async function initialise(): Promise<void> {
    if (isInitialised.value) {
      return
    }

    await loadConfig()

    const transport = createConnectTransport({
      baseUrl: config.value.backendHost,
    })

    client.value = createClient(ChatService, transport)
    isInitialised.value = true
  }

  function checkInitialisation() {
    if (!client.value) {
      throw new Error('Chat API client not initialised. Call initialise() first.')
    }
  }

  /**
   * Stream chat responses token-by-token
   */
  async function streamChat(
    message: string,
    contextDocumentIds: string[],
    conversationHistory: ChatMessage[],
    onChunk: StreamCallback,
  ): Promise<void> {
    checkInitialisation()

    const request = new ChatRequest({
      message,
      contextDocumentIds,
      conversationHistory,
    })

    // Connect RPC streaming: iterate over async iterable
    for await (const chunk of client.value!.streamChat(request)) {
      onChunk(chunk)
    }
  }

  return {
    initialise,
    streamChat,
    isInitialised,
  }
}
