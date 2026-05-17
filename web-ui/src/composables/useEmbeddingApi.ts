import type { Client } from '@connectrpc/connect'

import type {
  ChunkBoundary,
  DeleteEmbeddingsResponse,
  EmbedDocumentResponse,
  GetChunkBoundariesResponse,
  ProposeChunksResponse,
} from '../bibliophage/v1alpha3/embedding_pb'
import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'

import { ref } from 'vue'
import { EmbeddingService } from '../bibliophage/v1alpha3/embedding_connect'
import {
  ChunkingConfig,
  DeleteEmbeddingsRequest,
  EmbedDocumentRequest,
  GetChunkBoundariesRequest,
  ProposeChunksRequest,
} from '../bibliophage/v1alpha3/embedding_pb'
import { useConfig } from './useConfig'

// Shared client instance (singleton pattern)
const client = ref<Client<typeof EmbeddingService> | null>(null)
const isInitialised = ref(false)

/**
 * Composable for Embedding API operations
 * Provides methods to interact with the embedding service for chunking and vector embeddings
 *
 * @example
 * const api = useEmbeddingApi()
 * await api.initialise()
 *
 * // Propose chunk boundaries
 * const response = await api.proposeChunks(documentId, chunkingConfig)
 *
 * // Embed document with boundaries
 * const embedResponse = await api.embedDocument(documentId, config, boundaries)
 */
export function useEmbeddingApi() {
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

    client.value = createClient(EmbeddingService, transport)
    isInitialised.value = true
  }

  function checkInitialisation() {
    if (!client.value) {
      throw new Error('API client not initialised. Call initialise() first.')
    }
  }

  /**
   * Propose chunk boundaries for a document using a chunking strategy
   *
   * @param documentId - The ID of the document to chunk
   * @param config - Chunking configuration (strategy, token limits, etc.)
   * @returns Response containing proposed chunk boundaries and statistics
   */
  async function proposeChunks(
    documentId: string,
    config: Partial<ChunkingConfig>,
  ): Promise<ProposeChunksResponse> {
    checkInitialisation()

    const request = new ProposeChunksRequest({
      documentId,
      config: new ChunkingConfig(config),
    })

    return await client.value!.proposeChunks(request)
  }

  /**
   * Embed a document with approved chunk boundaries
   * Creates vector embeddings and stores them in pgvector
   *
   * @param documentId - The ID of the document to embed
   * @param config - Chunking configuration used for these boundaries
   * @param boundaries - Optional custom boundaries; if not provided, will be generated from config
   * @returns Response with embedding status
   */
  async function embedDocument(
    documentId: string,
    config: Partial<ChunkingConfig>,
    boundaries?: ChunkBoundary[],
  ): Promise<EmbedDocumentResponse> {
    checkInitialisation()

    const request = new EmbedDocumentRequest({
      documentId,
      config: new ChunkingConfig(config),
      desiredBoundaries: boundaries,
    })

    return await client.value!.embedDocument(request)
  }

  /**
   * Get stored chunk boundaries for a document
   *
   * @param documentId - The ID of the document
   * @returns Response containing boundaries, config, and embedding status
   */
  async function getChunkBoundaries(documentId: string): Promise<GetChunkBoundariesResponse> {
    checkInitialisation()

    const request = new GetChunkBoundariesRequest({
      documentId,
    })

    return await client.value!.getChunkBoundaries(request)
  }

  /**
   * Delete all embeddings for a document
   * Removes both chunk boundaries from FerretDB and vectors from pgvector
   *
   * @param documentId - The ID of the document
   * @returns Response with count of deleted chunks
   */
  async function deleteEmbeddings(documentId: string): Promise<DeleteEmbeddingsResponse> {
    checkInitialisation()

    const request = new DeleteEmbeddingsRequest({
      documentId,
    })

    return await client.value!.deleteEmbeddings(request)
  }

  // Return client object with all the needed methods
  return {
    initialise,
    proposeChunks,
    embedDocument,
    getChunkBoundaries,
    deleteEmbeddings,
    isInitialised,
  }
}
