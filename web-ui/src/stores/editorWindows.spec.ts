import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { Tag } from '../bibliophage/v1alpha3/tag_pb'
import { useEditorWindowStore } from './editorWindows'

describe('useEditorWindowStore tags', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('opens a window with no tags by default', () => {
    const store = useEditorWindowStore()
    const id = store.openWindow({})
    expect(store.getWindow(id)?.tags).toEqual([])
  })

  it('opens a window carrying the tags it was given', () => {
    const store = useEditorWindowStore()
    const tags = [new Tag({ id: 'tag-genre', name: 'genre' })]
    const id = store.openWindow({ tags })
    expect(store.getWindow(id)?.tags).toEqual(tags)
  })

  it('updateDocument updates a window\'s tags', () => {
    const store = useEditorWindowStore()
    const id = store.openWindow({})
    const tags = [new Tag({ id: 'tag-genre', name: 'genre' })]

    store.updateDocument(id, { tags })

    expect(store.getWindow(id)?.tags).toEqual(tags)
  })
})
