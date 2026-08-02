import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag, TagValue } from '../bibliophage/v1alpha3/tag_pb'
import TagManager from './TagManager.vue'

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

function tag(overrides: Partial<{ id: string, name: string, documentCount: number, valueCount: number, values: TagValue[] }>): Tag {
  return new Tag({
    id: overrides.id ?? 'tag-genre',
    name: overrides.name ?? 'genre',
    documentCount: overrides.documentCount ?? 0,
    valueCount: overrides.valueCount ?? (overrides.values?.length ?? 0),
    values: overrides.values ?? [],
  })
}

async function mountManager() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(TagManager, { global: { plugins: [pinia] } })
  await flushPromises()
  return wrapper
}

function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('tagManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockApi.listTags.mockResolvedValue({
      success: true,
      message: '',
      tags: [
        tag({ id: 'tag-genre', name: 'genre', documentCount: 3, values: [new TagValue({ id: 'value-fantasy', value: 'fantasy', documentCount: 2 }), new TagValue({ id: 'value-comedy', value: 'comedy', documentCount: 1 })] }),
        tag({ id: 'tag-world', name: 'world', documentCount: 1 }),
      ],
    })
  })

  it('lists tags with their usage counts', async () => {
    const wrapper = await mountManager()

    const text = wrapper.text()
    expect(text).toContain('genre')
    expect(text).toContain('world')
    expect(text).toContain('3')
  })

  it('filters the tag list by a search query', async () => {
    const wrapper = await mountManager()

    await wrapper.find('input[placeholder="Search tags..."]').setValue('gen')

    expect(wrapper.text()).toContain('genre')
    expect(wrapper.text()).not.toContain('world')
  })

  it('creates a new tag from the create-tag form', async () => {
    mockApi.createTag.mockResolvedValue({ success: true, message: '', tag: tag({ id: 'tag-canon', name: 'canon' }) })
    const wrapper = await mountManager()

    await wrapper.find('input[placeholder="New tag name"]').setValue('canon')
    await wrapper.find('[data-testid="create-tag-form"]').trigger('submit')
    await flushPromises()

    expect(mockApi.createTag).toHaveBeenCalledWith('canon', undefined)
  })

  it('pre-fills the create-tag input when opened with a prefillName', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(TagManager, { global: { plugins: [pinia] }, props: { prefillName: 'era' } })
    await flushPromises()

    expect((wrapper.find('input[placeholder="New tag name"]').element as HTMLInputElement).value).toBe('era')
  })

  it('shows a tag\'s values on selection and adds a new value', async () => {
    mockApi.createTagValue.mockResolvedValue({ success: true, message: '', tagValue: new TagValue({ value: 'noire' }) })
    const wrapper = await mountManager()

    await wrapper.find('[data-testid="tag-list-item-tag-genre"]').trigger('click')
    expect((wrapper.find('input[data-testid="rename-value-input-fantasy"]').element as HTMLInputElement).value).toBe('fantasy')
    expect((wrapper.find('input[data-testid="rename-value-input-comedy"]').element as HTMLInputElement).value).toBe('comedy')

    await wrapper.find('input[placeholder="New value"]').setValue('noire')
    await wrapper.find('[data-testid="create-value-form"]').trigger('submit')
    await flushPromises()

    expect(mockApi.createTagValue).toHaveBeenCalledWith('tag-genre', 'noire')
  })

  it('requires confirmation before deleting a tag, showing its usage count', async () => {
    mockApi.deleteTag.mockResolvedValue({ success: true, message: '' })
    const wrapper = await mountManager()

    await wrapper.find('[data-testid="tag-list-item-tag-genre"]').trigger('click')
    await wrapper.find('[data-testid="delete-tag-button"]').trigger('click')

    expect(wrapper.text()).toContain('3')
    expect(mockApi.deleteTag).not.toHaveBeenCalled()

    await wrapper.find('[data-testid="confirm-delete-tag-button"]').trigger('click')
    await flushPromises()

    expect(mockApi.deleteTag).toHaveBeenCalledWith('tag-genre')
  })

  it('renames a tag via the inline rename form', async () => {
    mockApi.renameTag.mockResolvedValue({ success: true, message: '', tag: tag({ id: 'tag-genre', name: 'category' }) })
    const wrapper = await mountManager()

    await wrapper.find('[data-testid="tag-list-item-tag-genre"]').trigger('click')
    await wrapper.find('input[data-testid="rename-tag-input"]').setValue('category')
    await wrapper.find('[data-testid="rename-tag-form"]').trigger('submit')
    await flushPromises()

    expect(mockApi.renameTag).toHaveBeenCalledWith('tag-genre', 'category')
  })

  it('renames a tag value via its inline rename form, keyed by the value\'s own id', async () => {
    mockApi.renameTagValue.mockResolvedValue({ success: true, message: '' })
    const wrapper = await mountManager()

    await wrapper.find('[data-testid="tag-list-item-tag-genre"]').trigger('click')
    await wrapper.find('input[data-testid="rename-value-input-fantasy"]').setValue('high-fantasy')
    await wrapper.find('[data-testid="rename-value-form-fantasy"]').trigger('submit')
    await flushPromises()

    expect(mockApi.renameTagValue).toHaveBeenCalledWith('value-fantasy', 'high-fantasy')
  })

  it('requires confirmation before deleting a tag value, showing its usage count', async () => {
    mockApi.deleteTagValue.mockResolvedValue({ success: true, message: '' })
    const wrapper = await mountManager()

    await wrapper.find('[data-testid="tag-list-item-tag-genre"]').trigger('click')
    await wrapper.find('[data-testid="delete-value-button-fantasy"]').trigger('click')

    expect(mockApi.deleteTagValue).not.toHaveBeenCalled()

    await wrapper.find('[data-testid="confirm-delete-value-button-fantasy"]').trigger('click')
    await flushPromises()

    expect(mockApi.deleteTagValue).toHaveBeenCalledWith('value-fantasy')
  })
})
