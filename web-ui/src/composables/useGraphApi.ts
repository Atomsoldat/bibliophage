import type { Client } from '@connectrpc/connect'

import type {
  CreateEdgeResponse,
  DeleteEdgeResponse,
  GetNeighboursResponse,
  ListEdgesResponse,
} from '../bibliophage/v1alpha3/graph_pb'
import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'

import { ref } from 'vue'
import { GraphService } from '../bibliophage/v1alpha3/graph_connect'
import {
  CreateEdgeRequest,
  DeleteEdgeRequest,
  GetNeighboursRequest,
  ListEdgesRequest,
} from '../bibliophage/v1alpha3/graph_pb'
import { useConfig } from './useConfig'

// Shared client instance (singleton pattern)
// see https://connectrpc.com/docs/node/using-clients/#connect
const client = ref<Client<typeof GraphService> | null>(null)
const isInitialised = ref(false)

/**
 * Composable for Graph API operations.
 *
 * Nodes are documents — to create or delete a node, use useDocumentApi.
 * This composable covers edge CRUD plus the two graph-shaped reads
 * (neighbours of a single node, edges within a set of nodes).
 *
 * @example
 *   const api = useGraphApi()
 *   await api.initialise()
 *   const { neighbours, edges } = await api.getNeighbours(documentId)
 */
export function useGraphApi() {
  const { config, loadConfig } = useConfig()

  /**
   * Initialise the API client. Safe to call multiple times — only opens once.
   */
  async function initialise(): Promise<void> {
    if (isInitialised.value) {
      return
    }

    await loadConfig()

    const transport = createConnectTransport({
      baseUrl: config.value.backendHost,
    })

    client.value = createClient(GraphService, transport)
    isInitialised.value = true
  }

  function checkInitialisation() {
    if (!client.value) {
      throw new Error('API client not initialised. Call initialise() first.')
    }
  }

  /**
   * Create an edge between two documents. Defaults to an undirected
   * `RELATED` edge — that's all the MVP uses; the proto's `relationship`
   * and `directed` fields are wired through for future use.
   */
  async function createEdge(
    sourceNodeId: string,
    targetNodeId: string,
    relationship = 'RELATED',
    directed = false,
  ): Promise<CreateEdgeResponse> {
    checkInitialisation()
    const request = new CreateEdgeRequest({
      sourceNodeId,
      targetNodeId,
      relationship,
      directed,
    })
    return await client.value!.createEdge(request)
  }

  async function deleteEdge(edgeId: string): Promise<DeleteEdgeResponse> {
    checkInitialisation()
    const request = new DeleteEdgeRequest({ id: edgeId })
    return await client.value!.deleteEdge(request)
  }

  /**
   * Fetch the one-hop neighbourhood of a document along with the edges
   * connecting it to those neighbours.
   */
  async function getNeighbours(documentId: string): Promise<GetNeighboursResponse> {
    checkInitialisation()
    const request = new GetNeighboursRequest({ documentId })
    return await client.value!.getNeighbours(request)
  }

  /**
   * Fetch every edge whose endpoints both lie in the given document set.
   * Used to draw edges between nodes that are already on the canvas.
   */
  async function listEdges(documentIds: string[]): Promise<ListEdgesResponse> {
    checkInitialisation()
    const request = new ListEdgesRequest({ documentIds })
    return await client.value!.listEdges(request)
  }

  return {
    initialise,
    createEdge,
    deleteEdge,
    getNeighbours,
    listEdges,
    isInitialised,
  }
}
