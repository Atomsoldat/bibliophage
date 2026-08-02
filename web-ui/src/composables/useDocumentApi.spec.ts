import { beforeEach, describe, expect, it, vi } from 'vitest'

const mockClient = {
  assignTagValues: vi.fn(),
  deleteTagValues: vi.fn(),
}

vi.mock('@connectrpc/connect', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@connectrpc/connect')>()
  return { ...actual, createClient: vi.fn(() => mockClient) }
})
vi.mock('@connectrpc/connect-web', () => ({
  createConnectTransport: vi.fn(() => ({})),
}))

const { useDocumentApi } = await import('./useDocumentApi')

describe('useDocumentApi tag assignment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('assigns one or more tag values to one or more documents atomically', async () => {
    mockClient.assignTagValues.mockResolvedValue({ success: true, message: '' })
    const api = useDocumentApi()
    await api.initialise()

    await api.assignTagValue(['doc-1', 'doc-2'], 'tag-1', ['fantasy', 'comedy'])

    expect(mockClient.assignTagValues).toHaveBeenCalledWith(
      expect.objectContaining({
        documentIds: ['doc-1', 'doc-2'],
        tagId: 'tag-1',
        tagValues: [
          expect.objectContaining({ value: 'fantasy' }),
          expect.objectContaining({ value: 'comedy' }),
        ],
      }),
    )
  })

  it('removes specific tag values from documents', async () => {
    mockClient.deleteTagValues.mockResolvedValue({ success: true, message: '' })
    const api = useDocumentApi()
    await api.initialise()

    await api.removeTagValue(['doc-1'], 'tag-1', ['fantasy'])

    expect(mockClient.deleteTagValues).toHaveBeenCalledWith(
      expect.objectContaining({
        documentIds: ['doc-1'],
        tagId: 'tag-1',
        tagValues: [expect.objectContaining({ value: 'fantasy' })],
      }),
    )
  })

  it('removes an entire tag from documents when no values are given', async () => {
    mockClient.deleteTagValues.mockResolvedValue({ success: true, message: '' })
    const api = useDocumentApi()
    await api.initialise()

    await api.removeTagValue(['doc-1'], 'tag-1')

    expect(mockClient.deleteTagValues).toHaveBeenCalledWith(
      expect.objectContaining({
        documentIds: ['doc-1'],
        tagId: 'tag-1',
        tagValues: [],
      }),
    )
  })
})
