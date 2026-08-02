import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag, TagValue } from '../bibliophage/v1alpha3/tag_pb'

const mockApi = {
  initialise: vi.fn().mockResolvedValue(undefined),
  assignTagValue: vi.fn(),
  removeTagValue: vi.fn(),
  searchDocuments: vi.fn().mockResolvedValue({ success: true, message: '', matches: [], totalCount: 0, pageNumber: 0, hasMore: false }),
}

vi.mock('./useDocumentApi', () => ({
  useDocumentApi: () => mockApi,
}))

const { useDocumentStore } = await import('../stores/documents')
const { useBulkMetadataEdit } = await import('./useBulkMetadataEdit')

function tag(id: string, name: string, values: string[]): Tag {
  return new Tag({ id, name, values: values.map(value => new TagValue({ value })) })
}

describe('useBulkMetadataEdit', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockApi.assignTagValue.mockResolvedValue({ success: true, message: '' })
    mockApi.removeTagValue.mockResolvedValue({ success: true, message: '' })
  })

  it('does not open when nothing is selected', () => {
    const bulkEdit = useBulkMetadataEdit()
    bulkEdit.openModal()
    expect(bulkEdit.showModal.value).toBe(false)
  })

  it('opens when documents are selected', () => {
    const documentStore = useDocumentStore()
    documentStore.selectedIds.add('doc-1')

    const bulkEdit = useBulkMetadataEdit()
    bulkEdit.openModal()

    expect(bulkEdit.showModal.value).toBe(true)
  })

  it('assigns each added tag to every selected document in one call', async () => {
    const documentStore = useDocumentStore()
    documentStore.selectedIds.add('doc-1')
    documentStore.selectedIds.add('doc-2')

    const bulkEdit = useBulkMetadataEdit()
    await bulkEdit.handleUpdate({
      tagsToAdd: [tag('tag-genre', 'genre', ['fantasy', 'comedy'])],
      tagsToRemove: [],
    })

    expect(mockApi.assignTagValue).toHaveBeenCalledWith(['doc-1', 'doc-2'], 'tag-genre', ['fantasy', 'comedy'])
  })

  it('removes each removed tag from every selected document in one call', async () => {
    const documentStore = useDocumentStore()
    documentStore.selectedIds.add('doc-1')

    const bulkEdit = useBulkMetadataEdit()
    await bulkEdit.handleUpdate({
      tagsToAdd: [],
      tagsToRemove: [tag('tag-genre', 'genre', ['fantasy'])],
    })

    expect(mockApi.removeTagValue).toHaveBeenCalledWith(['doc-1'], 'tag-genre', ['fantasy'])
  })

  it('closes the modal, clears selection and reloads on full success', async () => {
    const documentStore = useDocumentStore()
    await documentStore.search({ nameQuery: '', pageSize: 20, pageNumber: 0, sortOrder: 0 })
    mockApi.searchDocuments.mockClear()
    documentStore.selectedIds.add('doc-1')
    const bulkEdit = useBulkMetadataEdit()
    bulkEdit.openModal()

    await bulkEdit.handleUpdate({ tagsToAdd: [tag('tag-genre', 'genre', ['fantasy'])], tagsToRemove: [] })

    expect(bulkEdit.showModal.value).toBe(false)
    expect(documentStore.selectedIds.size).toBe(0)
    expect(mockApi.searchDocuments).toHaveBeenCalled()
  })

  it('keeps the modal open and selection intact when a call fails', async () => {
    mockApi.assignTagValue.mockResolvedValue({ success: false, message: 'boom' })
    const documentStore = useDocumentStore()
    documentStore.selectedIds.add('doc-1')
    const bulkEdit = useBulkMetadataEdit()
    bulkEdit.openModal()

    await bulkEdit.handleUpdate({ tagsToAdd: [tag('tag-genre', 'genre', ['fantasy'])], tagsToRemove: [] })

    expect(bulkEdit.showModal.value).toBe(true)
    expect(documentStore.selectedIds.size).toBe(1)
  })
})
