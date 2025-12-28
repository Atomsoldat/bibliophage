import type { Client } from '@connectrpc/connect'

import type {
  DeleteDocumentResponse,
  GetDocumentResponse,
  SearchDocumentsResponse,
  StoreDocumentResponse,
  UpdateDocumentResponse,
} from '../bibliophage/v1alpha2/document_pb'
import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'

import { ref } from 'vue'
import { DocumentService } from '../bibliophage/v1alpha2/document_connect'
import {
  DeleteDocumentRequest,
  Document,
  GetDocumentRequest,
  SearchDocumentsRequest,
  StoreDocumentRequest,
  UpdateDocumentRequest,
} from '../bibliophage/v1alpha2/document_pb'
import { useConfig } from './useConfig'

// Shared client instance (singleton pattern)
const client = ref<Client<typeof DocumentService> | null>(null)
const isInitialised = ref(false)

/**
 * Composable for Document API operations
 * Provides methods to interact with the document service
 *
 * @example
 * const api = useDocumentApi()
 * await api.initialise()
 *
 * // Create new document
 * const response = await api.storeDocument({ name: 'My Doc', content: 'Hello' })
 *
 * // Update existing document
 * const updateResponse = await api.updateDocument(documentId, { name: 'Updated', content: 'World' })
 */
export function useDocumentApi() {
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

    client.value = createClient(DocumentService, transport)
    isInitialised.value = true
  }
  function checkInitialisation() {
    if (!client.value) {
      throw new Error('API client not initialised. Call initialise() first.')
    }
  }

  /**
   * Store a new document
   */
  async function storeDocument(document: Partial<Document>): Promise<StoreDocumentResponse> {
    checkInitialisation()

    const request = new StoreDocumentRequest({
      document: new Document(document),
    })
    return await client.value!.storeDocument(request)
  }

  /**
   * Update an existing document
   * The document must include an id
   */
  async function updateDocument(document: Partial<Document>): Promise<UpdateDocumentResponse> {
    checkInitialisation()

    const request = new UpdateDocumentRequest({
      document: new Document(document),
    })

    return await client.value!.updateDocument(request)
  }

  /**
   * Get a document by ID
   */
  async function getDocument(id: string): Promise<GetDocumentResponse> {
    checkInitialisation()

    const request = new GetDocumentRequest({ id })

    return await client.value!.getDocument(request)
  }

  /**
   *  Search for documents
   */
  async function searchDocuments(params: Partial<SearchDocumentsRequest>): Promise<SearchDocumentsResponse> {
    checkInitialisation()

    const request = new SearchDocumentsRequest(params)

    return await client.value!.searchDocuments(request)
  }

  /**
   *  Delete a document by ID
   */
  async function deleteDocument(id: string): Promise<DeleteDocumentResponse> {
    checkInitialisation()

    const request = new DeleteDocumentRequest({ id })

    return await client.value!.deleteDocument(request)
  }

  // return client object with all the needed methods
  return {
    initialise,
    storeDocument,
    updateDocument,
    getDocument,
    searchDocuments,
    deleteDocument,
    isInitialised,
  }
}
