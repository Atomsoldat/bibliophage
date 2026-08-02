import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag } from '../bibliophage/v1alpha3/tag_pb'
import TextEditorCard from './TextEditorCard.vue'

vi.mock('../composables/useTagApi', () => ({
  useTagApi: () => ({
    initialise: vi.fn().mockResolvedValue(undefined),
    listTags: vi.fn().mockResolvedValue({ success: true, message: '', tags: [] }),
  }),
}))
vi.mock('../composables/useDocumentApi', () => ({
  useDocumentApi: () => ({
    initialise: vi.fn().mockResolvedValue(undefined),
    assignTagValue: vi.fn().mockResolvedValue({ success: true, message: '' }),
    removeTagValue: vi.fn().mockResolvedValue({ success: true, message: '' }),
  }),
}))

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('textEditorCard tags', () => {
  it('does not render TagInput for a document with no id yet', () => {
    const wrapper = mount(TextEditorCard, {
      props: { documentId: '', tags: [] },
    })
    expect(wrapper.findComponent({ name: 'TagInput' }).exists()).toBe(false)
  })

  it('renders TagInput bound to the document once it has an id', () => {
    const tags = [new Tag({ id: 'tag-genre', name: 'genre' })]
    const wrapper = mount(TextEditorCard, {
      props: { documentId: 'doc-1', tags },
    })

    const tagInput = wrapper.findComponent({ name: 'TagInput' })
    expect(tagInput.exists()).toBe(true)
    expect(tagInput.props('mode')).toBe('assign')
    expect(tagInput.props('documentId')).toBe('doc-1')
    expect(tagInput.props('modelValue')).toEqual(tags)
  })

  it('emits update:tags when TagInput emits an updated tag set', async () => {
    const wrapper = mount(TextEditorCard, {
      props: { documentId: 'doc-1', tags: [] },
    })

    const newTags = [new Tag({ id: 'tag-genre', name: 'genre' })]
    await wrapper.findComponent({ name: 'TagInput' }).vm.$emit('update:modelValue', newTags)

    expect(wrapper.emitted('update:tags')?.[0]).toEqual([newTags])
  })
})
