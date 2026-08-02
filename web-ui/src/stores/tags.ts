import type {
  DeleteTagResponse,
  DeleteTagValueResponse,
  RenameTagResponse,
  RenameTagValueResponse,
  StoreTagResponse,
  StoreTagValueResponse,
  Tag,
  TagValue,
  UpdateTagColourResponse,
} from '../bibliophage/v1alpha3/tag_pb'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useLogger } from '../composables/useLogger'
import { useTagApi } from '../composables/useTagApi'

/**
 * Shared cache of tag names/values. A single instance of this store backs
 * every open TagInput/TagManager, so a reload() after any governance edit
 * (create/rename/delete) is immediately reflected everywhere it's shown.
 */
export const useTagStore = defineStore('tags', () => {
  const api = useTagApi()
  const logger = useLogger()

  const tags = ref<Tag[]>([])
  const loading = ref(false)
  let loaded = false

  async function reload(): Promise<void> {
    loading.value = true
    try {
      await api.initialise()
      const response = await api.listTags()
      tags.value = response.tags
      loaded = true
    }
    catch (error) {
      logger.error(`Failed to load tags: ${(error as Error).message}`)
    }
    finally {
      loading.value = false
    }
  }

  /** Load tags once; safe to call from every component that needs them on mount */
  async function ensureLoaded(): Promise<void> {
    if (!loaded) {
      await reload()
    }
  }

  function findTagByName(name: string): Tag | undefined {
    const query = name.toLowerCase()
    return tags.value.find(t => t.name.toLowerCase() === query)
  }

  function matchingTags(query: string): Tag[] {
    const q = query.trim().toLowerCase()
    if (!q) {
      return tags.value
    }
    return tags.value.filter(t => t.name.toLowerCase().includes(q))
  }

  function matchingValues(tagName: string, query: string): TagValue[] {
    const tag = findTagByName(tagName)
    if (!tag) {
      return []
    }
    const q = query.trim().toLowerCase()
    if (!q) {
      return tag.values
    }
    return tag.values.filter(v => v.value.toLowerCase().includes(q))
  }

  async function createTag(name: string, colour?: string): Promise<StoreTagResponse> {
    const response = await api.createTag(name, colour)
    await reload()
    return response
  }

  async function renameTag(id: string, name: string): Promise<RenameTagResponse> {
    const response = await api.renameTag(id, name)
    await reload()
    return response
  }

  async function deleteTag(id: string): Promise<DeleteTagResponse> {
    const response = await api.deleteTag(id)
    await reload()
    return response
  }

  async function updateTagColour(id: string, colour: string): Promise<UpdateTagColourResponse> {
    const response = await api.updateTagColour(id, colour)
    await reload()
    return response
  }

  async function createTagValue(tagId: string, value: string): Promise<StoreTagValueResponse> {
    const response = await api.createTagValue(tagId, value)
    await reload()
    return response
  }

  async function renameTagValue(id: string, value: string): Promise<RenameTagValueResponse> {
    const response = await api.renameTagValue(id, value)
    await reload()
    return response
  }

  async function deleteTagValue(id: string): Promise<DeleteTagValueResponse> {
    const response = await api.deleteTagValue(id)
    await reload()
    return response
  }

  return {
    tags,
    loading,
    reload,
    ensureLoaded,
    findTagByName,
    matchingTags,
    matchingValues,
    createTag,
    renameTag,
    deleteTag,
    updateTagColour,
    createTagValue,
    renameTagValue,
    deleteTagValue,
  }
})
