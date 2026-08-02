import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Tag } from '../bibliophage/v1alpha3/tag_pb'
import MetadataEditModal from './MetadataEditModal.vue'
import TagInput from './TagInput.vue'

vi.mock('../composables/useTagApi', () => ({
  useTagApi: () => ({
    initialise: vi.fn().mockResolvedValue(undefined),
    listTags: vi.fn().mockResolvedValue({ success: true, message: '', tags: [] }),
  }),
}))

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('metadataEditModal', () => {
  it('renders two TagInputs in collect mode, for tags to add and tags to remove', () => {
    const wrapper = mount(MetadataEditModal, {
      props: { show: true, selectedCount: 2 },
    })

    const tagInputs = wrapper.findAllComponents(TagInput)
    expect(tagInputs).toHaveLength(2)
    expect(tagInputs[0]!.props('mode')).toBe('collect')
    expect(tagInputs[1]!.props('mode')).toBe('collect')
  })

  it('emits submit with the collected tagsToAdd and tagsToRemove', async () => {
    const wrapper = mount(MetadataEditModal, {
      props: { show: true, selectedCount: 2 },
    })

    const [addInput, removeInput] = wrapper.findAllComponents(TagInput)
    const addedTags = [new Tag({ id: 'tag-genre', name: 'genre' })]
    const removedTags = [new Tag({ id: 'tag-era', name: 'era' })]
    await addInput!.vm.$emit('update:modelValue', addedTags)
    await removeInput!.vm.$emit('update:modelValue', removedTags)

    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('submit')?.[0]).toEqual([{ tagsToAdd: addedTags, tagsToRemove: removedTags }])
  })
})
