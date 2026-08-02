import { beforeEach, describe, expect, it, vi } from 'vitest'

const mockClient = {
  getTags: vi.fn(),
  getTag: vi.fn(),
  storeTag: vi.fn(),
  renameTag: vi.fn(),
  deleteTag: vi.fn(),
  updateTagColour: vi.fn(),
  storeTagValue: vi.fn(),
  renameTagValue: vi.fn(),
  deleteTagValue: vi.fn(),
}

vi.mock('@connectrpc/connect', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@connectrpc/connect')>()
  return { ...actual, createClient: vi.fn(() => mockClient) }
})
vi.mock('@connectrpc/connect-web', () => ({
  createConnectTransport: vi.fn(() => ({})),
}))

const { useTagApi } = await import('./useTagApi')

describe('useTagApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists tags with usage counts and an optional name filter', async () => {
    mockClient.getTags.mockResolvedValue({ success: true, message: '', tags: [] })
    const api = useTagApi()
    await api.initialise()

    await api.listTags('gen')

    expect(mockClient.getTags).toHaveBeenCalledWith(
      expect.objectContaining({ nameFilter: 'gen', countDocs: true, countValues: true }),
    )
  })

  it('lists all tags when no name filter is given', async () => {
    mockClient.getTags.mockResolvedValue({ success: true, message: '', tags: [] })
    const api = useTagApi()
    await api.initialise()

    await api.listTags()

    expect(mockClient.getTags).toHaveBeenCalledWith(
      expect.objectContaining({ nameFilter: undefined, countDocs: true, countValues: true }),
    )
  })

  it('creates a tag with an optional colour', async () => {
    mockClient.storeTag.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.createTag('genre', '#ff0000')

    expect(mockClient.storeTag).toHaveBeenCalledWith(
      expect.objectContaining({ tag: expect.objectContaining({ name: 'genre', colour: '#ff0000' }) }),
    )
  })

  it('renames a tag by id', async () => {
    mockClient.renameTag.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.renameTag('tag-1', 'new-name')

    expect(mockClient.renameTag).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tag-1', name: 'new-name' }),
    )
  })

  it('deletes a tag by id', async () => {
    mockClient.deleteTag.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.deleteTag('tag-1')

    expect(mockClient.deleteTag).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tag-1' }),
    )
  })

  it('updates a tag colour', async () => {
    mockClient.updateTagColour.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.updateTagColour('tag-1', '#00ff00')

    expect(mockClient.updateTagColour).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tag-1', colour: '#00ff00' }),
    )
  })

  it('creates a tag value under a tag, ahead of assignment to any document', async () => {
    mockClient.storeTagValue.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.createTagValue('tag-1', 'fantasy')

    expect(mockClient.storeTagValue).toHaveBeenCalledWith(
      expect.objectContaining({ tagId: 'tag-1', tagValue: expect.objectContaining({ value: 'fantasy' }) }),
    )
  })

  it('renames a tag value via the request\'s `name` field (tag.proto naming quirk)', async () => {
    mockClient.renameTagValue.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.renameTagValue('val-1', 'new-value')

    expect(mockClient.renameTagValue).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'val-1', name: 'new-value' }),
    )
  })

  it('deletes a tag value by id', async () => {
    mockClient.deleteTagValue.mockResolvedValue({ success: true, message: '' })
    const api = useTagApi()
    await api.initialise()

    await api.deleteTagValue('val-1')

    expect(mockClient.deleteTagValue).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'val-1' }),
    )
  })
})
