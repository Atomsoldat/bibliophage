import type { Client } from '@connectrpc/connect'

import type {
  DeleteTagResponse,
  DeleteTagValueResponse,
  GetTagResponse,
  GetTagsResponse,
  RenameTagResponse,
  RenameTagValueResponse,
  StoreTagResponse,
  StoreTagValueResponse,
  UpdateTagColourResponse,
} from '../bibliophage/v1alpha3/tag_pb'
import { createClient } from '@connectrpc/connect'
import { createConnectTransport } from '@connectrpc/connect-web'

import { ref } from 'vue'
import { TagService } from '../bibliophage/v1alpha3/tag_connect'
import {
  DeleteTagRequest,
  DeleteTagValueRequest,
  GetTagRequest,
  GetTagsRequest,
  RenameTagRequest,
  RenameTagValueRequest,
  StoreTagRequest,
  StoreTagValueRequest,
  Tag,
  TagValue,
  UpdateTagColourRequest,
} from '../bibliophage/v1alpha3/tag_pb'
import { useConfig } from './useConfig'

// Shared client instance (singleton pattern), same approach as useDocumentApi.ts
const client = ref<Client<typeof TagService> | null>(null)
const isInitialised = ref(false)

/**
 * Composable for Tag governance API operations.
 * A tag's values are read via listTags()/getTag()'s returned Tag.values -
 * there is no separate list-values RPC (see tag.proto).
 *
 * @example
 * const api = useTagApi()
 * await api.initialise()
 * const response = await api.createTag('genre')
 */
export function useTagApi() {
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

    client.value = createClient(TagService, transport)
    isInitialised.value = true
  }

  function checkInitialisation() {
    if (!client.value) {
      throw new Error('API client not initialised. Call initialise() first.')
    }
  }

  /**
   * List tags with usage counts, optionally filtered by name
   */
  async function listTags(nameFilter?: string): Promise<GetTagsResponse> {
    checkInitialisation()

    const request = new GetTagsRequest({ nameFilter, countDocs: true, countValues: true })
    return await client.value!.getTags(request)
  }

  /**
   * Get a single tag by id, with usage counts and its values
   */
  async function getTag(id: string): Promise<GetTagResponse> {
    checkInitialisation()

    const request = new GetTagRequest({ id, countDocs: true, countValues: true })
    return await client.value!.getTag(request)
  }

  /**
   * Create a new tag name
   */
  async function createTag(name: string, colour?: string): Promise<StoreTagResponse> {
    checkInitialisation()

    const request = new StoreTagRequest({ tag: new Tag({ name, colour }) })
    return await client.value!.storeTag(request)
  }

  /**
   * Rename an existing tag
   */
  async function renameTag(id: string, name: string): Promise<RenameTagResponse> {
    checkInitialisation()

    const request = new RenameTagRequest({ id, name })
    return await client.value!.renameTag(request)
  }

  /**
   * Delete a tag by id
   */
  async function deleteTag(id: string): Promise<DeleteTagResponse> {
    checkInitialisation()

    const request = new DeleteTagRequest({ id })
    return await client.value!.deleteTag(request)
  }

  /**
   * Change a tag's colour
   */
  async function updateTagColour(id: string, colour: string): Promise<UpdateTagColourResponse> {
    checkInitialisation()

    const request = new UpdateTagColourRequest({ id, colour })
    return await client.value!.updateTagColour(request)
  }

  /**
   * Create a new value under an existing tag, without assigning it to a document
   */
  async function createTagValue(tagId: string, value: string): Promise<StoreTagValueResponse> {
    checkInitialisation()

    const request = new StoreTagValueRequest({ tagId, tagValue: new TagValue({ value }) })
    return await client.value!.storeTagValue(request)
  }

  /**
   * Rename an existing tag value
   */
  async function renameTagValue(id: string, value: string): Promise<RenameTagValueResponse> {
    checkInitialisation()

    // RenameTagValueRequest's field is called `name` in tag.proto even though
    // TagValue itself calls the same concept `value` - a proto-level naming
    // inconsistency, not something to work around here.
    const request = new RenameTagValueRequest({ id, name: value })
    return await client.value!.renameTagValue(request)
  }

  /**
   * Delete a tag value by id
   */
  async function deleteTagValue(id: string): Promise<DeleteTagValueResponse> {
    checkInitialisation()

    const request = new DeleteTagValueRequest({ id })
    return await client.value!.deleteTagValue(request)
  }

  return {
    initialise,
    listTags,
    getTag,
    createTag,
    renameTag,
    deleteTag,
    updateTagColour,
    createTagValue,
    renameTagValue,
    deleteTagValue,
    isInitialised,
  }
}
