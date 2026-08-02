import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag, TagValue } from '../bibliophage/v1alpha3/tag_pb'
import TagInput from './TagInput.vue'

const mockTagApi = {
  initialise: vi.fn().mockResolvedValue(undefined),
  listTags: vi.fn(),
}

const mockDocumentApi = {
  initialise: vi.fn().mockResolvedValue(undefined),
  assignTagValue: vi.fn().mockResolvedValue({ success: true, message: '' }),
  removeTagValue: vi.fn().mockResolvedValue({ success: true, message: '' }),
}

vi.mock('../composables/useTagApi', () => ({
  useTagApi: () => mockTagApi,
}))
vi.mock('../composables/useDocumentApi', () => ({
  useDocumentApi: () => mockDocumentApi,
}))

function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

interface TagInputTestProps {
  mode: 'assign' | 'collect'
  documentId?: string
  modelValue: Tag[]
}

async function mountInput(props: TagInputTestProps) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(TagInput, { global: { plugins: [pinia] }, props })
  await flushPromises()
  return wrapper
}

describe('tagInput', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockTagApi.listTags.mockResolvedValue({
      success: true,
      message: '',
      tags: [
        new Tag({ id: 'tag-genre', name: 'genre', values: [new TagValue({ id: 'v1', value: 'fantasy' })] }),
        new Tag({ id: 'tag-world', name: 'world', values: [] }),
      ],
    })
  })

  it('shows matching tag keys as the user types', async () => {
    const wrapper = await mountInput({ mode: 'collect', modelValue: [] })

    const keyInput = wrapper.find('[data-testid="tag-key-input"]')
    await keyInput.trigger('focus')
    await keyInput.setValue('gen')

    expect(wrapper.text()).toContain('genre')
    expect(wrapper.text()).not.toContain('world')
  })

  it('shows a "no tag called" affordance instead of a dropdown when nothing matches', async () => {
    const wrapper = await mountInput({ mode: 'collect', modelValue: [] })

    const keyInput = wrapper.find('[data-testid="tag-key-input"]')
    await keyInput.trigger('focus')
    await keyInput.setValue('nonexistent')

    expect(wrapper.find('[data-testid="no-tag-match"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('no tag called "nonexistent"')
  })

  it('opening the manager from the no-match affordance pre-fills the typed name', async () => {
    const wrapper = await mountInput({ mode: 'collect', modelValue: [] })

    const keyInput = wrapper.find('[data-testid="tag-key-input"]')
    await keyInput.trigger('focus')
    await keyInput.setValue('era')
    await wrapper.find('[data-testid="no-tag-match"]').trigger('mousedown')

    expect(wrapper.findComponent({ name: 'TagManagerOverlay' }).props('show')).toBe(true)
    expect(wrapper.findComponent({ name: 'TagManagerOverlay' }).props('prefillName')).toBe('era')
  })

  it('locks a tag key from the dropdown, then commits a value as a chip (collect mode)', async () => {
    const wrapper = await mountInput({ mode: 'collect', modelValue: [] })

    const keyInput = wrapper.find('[data-testid="tag-key-input"]')
    await keyInput.trigger('focus')
    await keyInput.setValue('genre')
    await wrapper.find('[data-testid="tag-key-option-tag-genre"]').trigger('mousedown')

    const valueInput = wrapper.find('[data-testid="tag-value-input"]')
    expect(valueInput.exists()).toBe(true)
    await valueInput.setValue('noire')
    await valueInput.trigger('keydown.enter')

    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()
    const lastEmit = emitted![emitted!.length - 1]![0] as Tag[]
    expect(lastEmit).toHaveLength(1)
    expect(lastEmit[0]!.name).toBe('genre')
    expect(lastEmit[0]!.values.map(v => v.value)).toEqual(['noire'])
    expect(mockDocumentApi.assignTagValue).not.toHaveBeenCalled()
  })

  it('calls assignTagValue immediately in assign mode', async () => {
    const wrapper = await mountInput({ mode: 'assign', documentId: 'doc-1', modelValue: [] })

    const keyInput = wrapper.find('[data-testid="tag-key-input"]')
    await keyInput.trigger('focus')
    await keyInput.setValue('genre')
    await wrapper.find('[data-testid="tag-key-option-tag-genre"]').trigger('mousedown')

    const valueInput = wrapper.find('[data-testid="tag-value-input"]')
    await valueInput.setValue('noire')
    await valueInput.trigger('keydown.enter')
    await flushPromises()

    expect(mockDocumentApi.assignTagValue).toHaveBeenCalledWith(['doc-1'], 'tag-genre', ['noire'])
  })

  it('removes a chip, emitting the updated set (collect mode)', async () => {
    const existing = [new Tag({ id: 'tag-genre', name: 'genre', values: [new TagValue({ value: 'fantasy' }), new TagValue({ value: 'comedy' })] })]
    const wrapper = await mountInput({ mode: 'collect', modelValue: existing })

    await wrapper.find('[data-testid="remove-chip-tag-genre-fantasy"]').trigger('click')

    const emitted = wrapper.emitted('update:modelValue')
    const lastEmit = emitted![emitted!.length - 1]![0] as Tag[]
    expect(lastEmit[0]!.values.map(v => v.value)).toEqual(['comedy'])
    expect(mockDocumentApi.removeTagValue).not.toHaveBeenCalled()
  })

  it('drops the tag entirely once its last chip is removed', async () => {
    const existing = [new Tag({ id: 'tag-genre', name: 'genre', values: [new TagValue({ value: 'fantasy' })] })]
    const wrapper = await mountInput({ mode: 'collect', modelValue: existing })

    await wrapper.find('[data-testid="remove-chip-tag-genre-fantasy"]').trigger('click')

    const emitted = wrapper.emitted('update:modelValue')
    const lastEmit = emitted![emitted!.length - 1]![0] as Tag[]
    expect(lastEmit).toEqual([])
  })

  it('calls removeTagValue immediately in assign mode', async () => {
    const existing = [new Tag({ id: 'tag-genre', name: 'genre', values: [new TagValue({ value: 'fantasy' })] })]
    const wrapper = await mountInput({ mode: 'assign', documentId: 'doc-1', modelValue: existing })

    await wrapper.find('[data-testid="remove-chip-tag-genre-fantasy"]').trigger('click')
    await flushPromises()

    expect(mockDocumentApi.removeTagValue).toHaveBeenCalledWith(['doc-1'], 'tag-genre', ['fantasy'])
  })
})
