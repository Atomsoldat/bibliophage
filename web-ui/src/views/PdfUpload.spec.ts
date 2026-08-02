import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag } from '../bibliophage/v1alpha3/tag_pb'
import TagInput from '../components/TagInput.vue'
import PdfUpload from './PdfUpload.vue'

const mockPdfClient = {
  loadPdf: vi.fn(),
}

vi.mock('@connectrpc/connect', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@connectrpc/connect')>()
  return { ...actual, createClient: vi.fn(() => mockPdfClient) }
})
vi.mock('@connectrpc/connect-web', () => ({
  createConnectTransport: vi.fn(() => ({})),
}))
vi.mock('../composables/useTagApi', () => ({
  useTagApi: () => ({
    initialise: vi.fn().mockResolvedValue(undefined),
    listTags: vi.fn().mockResolvedValue({ success: true, message: '', tags: [] }),
  }),
}))

function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

function selectFile(wrapper: ReturnType<typeof mount>, file: File) {
  const input = wrapper.find('input[type="file"]').element as HTMLInputElement
  Object.defineProperty(input, 'files', { value: [file], writable: false })
  return wrapper.find('input[type="file"]').trigger('change')
}

describe('pdfUpload', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockPdfClient.loadPdf.mockResolvedValue({ pdf: { id: 'pdf-1', pageCount: 1, batchCount: 1, fileSize: 10 } })
  })

  it('has no RPG System or Publication Type selects', async () => {
    const wrapper = mount(PdfUpload)
    await flushPromises()

    expect(wrapper.text()).not.toContain('RPG System')
    expect(wrapper.text()).not.toContain('Publication Type')
  })

  it('renders TagInput in collect mode for assigning tags before submit', async () => {
    const wrapper = mount(PdfUpload)
    await flushPromises()

    const tagInput = wrapper.findComponent(TagInput)
    expect(tagInput.exists()).toBe(true)
    expect(tagInput.props('mode')).toBe('collect')
  })

  it('submits the collected tags as part of the load request', async () => {
    const wrapper = mount(PdfUpload)
    await flushPromises()

    const tags = [new Tag({ id: 'tag-doctype', name: 'document_type' })]
    await wrapper.findComponent(TagInput).vm.$emit('update:modelValue', tags)

    const file = new File(['%PDF-1.4'], 'monster-manual.pdf', { type: 'application/pdf' })
    await selectFile(wrapper, file)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mockPdfClient.loadPdf).toHaveBeenCalledTimes(1)
    const request = mockPdfClient.loadPdf.mock.calls[0]![0]
    expect(request.pdf.tags).toEqual(tags)
  })
})
