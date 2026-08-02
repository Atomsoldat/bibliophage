import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag, TagValue } from '../bibliophage/v1alpha3/tag_pb'

const mockApi = {
  initialise: vi.fn().mockResolvedValue(undefined),
  listTags: vi.fn(),
  createTag: vi.fn(),
  renameTag: vi.fn(),
  deleteTag: vi.fn(),
  updateTagColour: vi.fn(),
  createTagValue: vi.fn(),
  renameTagValue: vi.fn(),
  deleteTagValue: vi.fn(),
}

vi.mock('../composables/useTagApi', () => ({
  useTagApi: () => mockApi,
}))

const { useTagStore } = await import('./tags')

function tag(name: string, values: string[] = []): Tag {
  return new Tag({
    id: `tag-${name}`,
    name,
    values: values.map(value => new TagValue({ value })),
  })
}

describe('useTagStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockApi.listTags.mockResolvedValue({ success: true, message: '', tags: [tag('genre', ['fantasy', 'comedy']), tag('world', ['arrakis'])] })
  })

  it('loads tags from the API on reload()', async () => {
    const store = useTagStore()

    await store.reload()

    expect(store.tags.map(t => t.name)).toEqual(['genre', 'world'])
  })

  it('ensureLoaded() only fetches once until reload() is called again', async () => {
    const store = useTagStore()

    await store.ensureLoaded()
    await store.ensureLoaded()

    expect(mockApi.listTags).toHaveBeenCalledTimes(1)
  })

  it('finds a tag by name case-insensitively', async () => {
    const store = useTagStore()
    await store.reload()

    expect(store.findTagByName('GENRE')?.id).toBe('tag-genre')
    expect(store.findTagByName('missing')).toBeUndefined()
  })

  it('matches tags by a case-insensitive substring query', async () => {
    const store = useTagStore()
    await store.reload()

    expect(store.matchingTags('gen').map(t => t.name)).toEqual(['genre'])
    expect(store.matchingTags('').map(t => t.name)).toEqual(['genre', 'world'])
  })

  it('matches values under a locked tag by a case-insensitive substring query', async () => {
    const store = useTagStore()
    await store.reload()

    expect(store.matchingValues('genre', 'com').map(v => v.value)).toEqual(['comedy'])
    expect(store.matchingValues('genre', '').map(v => v.value)).toEqual(['fantasy', 'comedy'])
    expect(store.matchingValues('unknown-tag', 'x')).toEqual([])
  })

  it('reloads tags after a governance mutation so every open TagInput/TagManager sees it', async () => {
    mockApi.createTag.mockResolvedValue({ success: true, message: '', tag: tag('canon') })
    const store = useTagStore()
    await store.reload()
    expect(mockApi.listTags).toHaveBeenCalledTimes(1)

    await store.createTag('canon')

    expect(mockApi.createTag).toHaveBeenCalledWith('canon', undefined)
    expect(mockApi.listTags).toHaveBeenCalledTimes(2)
  })
})
