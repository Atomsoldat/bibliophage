import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TagManagerOverlay from './TagManagerOverlay.vue'

vi.mock('../composables/useTagApi', () => ({
  useTagApi: () => ({
    initialise: vi.fn().mockResolvedValue(undefined),
    listTags: vi.fn().mockResolvedValue({ success: true, message: '', tags: [] }),
  }),
}))

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('tagManagerOverlay', () => {
  it('renders nothing when show is false', () => {
    const wrapper = mount(TagManagerOverlay, { props: { show: false } })
    expect(wrapper.find('.modal-backdrop').exists()).toBe(false)
  })

  it('renders TagManager and forwards prefillName when shown', () => {
    const wrapper = mount(TagManagerOverlay, { props: { show: true, prefillName: 'era' } })
    expect(wrapper.findComponent({ name: 'TagManager' }).props('prefillName')).toBe('era')
  })

  it('emits close on backdrop click', async () => {
    const wrapper = mount(TagManagerOverlay, { props: { show: true } })
    await wrapper.find('.modal-backdrop').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close on the header close button', async () => {
    const wrapper = mount(TagManagerOverlay, { props: { show: true } })
    await wrapper.find('[data-testid="close-tag-manager"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
