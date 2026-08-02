import type { Tag } from '../bibliophage/v1alpha3/tag_pb'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface EditorWindowConfig {
  id: string
  documentId: string
  title: string
  content: string
  isNew: boolean
  tags: Tag[]
  x: number
  y: number
  zIndex: number
  isMinimized: boolean
}

const INITIAL_OFFSET = { x: 100, y: 100 }
const CASCADE_OFFSET = 30

export const useEditorWindowStore = defineStore('editorWindows', () => {
  const windows = ref<EditorWindowConfig[]>([])
  let nextWindowId = 1
  let nextZIndex = 10

  function calculatePosition(index: number): { x: number, y: number } {
    const offset = index * CASCADE_OFFSET
    return { x: INITIAL_OFFSET.x + offset, y: INITIAL_OFFSET.y + offset }
  }

  function openWindow(config: {
    documentId?: string
    title?: string
    content?: string
    isNew?: boolean
    tags?: Tag[]
    x?: number
    y?: number
  }): string {
    const windowId = `editor-window-${nextWindowId++}`
    const position = config.x !== undefined && config.y !== undefined
      ? { x: config.x, y: config.y }
      : calculatePosition(windows.value.length)

    windows.value.push({
      id: windowId,
      documentId: config.documentId || '',
      title: config.title || 'New Document',
      content: config.content || '',
      isNew: config.isNew ?? true,
      tags: config.tags ?? [],
      x: position.x,
      y: position.y,
      zIndex: nextZIndex++,
      isMinimized: false,
    })
    console.log(`[EditorWindows] Opened window ${windowId} - Total: ${windows.value.length}`)
    return windowId
  }

  function closeWindow(windowId: string): void {
    const index = windows.value.findIndex(w => w.id === windowId)
    if (index !== -1) {
      windows.value.splice(index, 1)
      console.log(`[EditorWindows] Closed window ${windowId} - Total: ${windows.value.length}`)
    }
  }

  function bringToFront(windowId: string): void {
    const win = windows.value.find(w => w.id === windowId)
    if (win)
      win.zIndex = nextZIndex++
  }

  function toggleMinimize(windowId: string): void {
    const win = windows.value.find(w => w.id === windowId)
    if (win)
      win.isMinimized = !win.isMinimized
  }

  function updatePosition(windowId: string, x: number, y: number): void {
    const win = windows.value.find(w => w.id === windowId)
    if (win) {
      win.x = x
      win.y = y
    }
  }

  function updateDocument(windowId: string, updates: {
    documentId?: string
    title?: string
    content?: string
    isNew?: boolean
    tags?: Tag[]
  }): void {
    const win = windows.value.find(w => w.id === windowId)
    if (!win)
      return
    if (updates.documentId !== undefined)
      win.documentId = updates.documentId
    if (updates.title !== undefined)
      win.title = updates.title
    if (updates.content !== undefined)
      win.content = updates.content
    if (updates.isNew !== undefined)
      win.isNew = updates.isNew
    if (updates.tags !== undefined)
      win.tags = updates.tags
  }

  function getWindow(windowId: string): EditorWindowConfig | undefined {
    return windows.value.find(w => w.id === windowId)
  }

  function closeAll(): void {
    const count = windows.value.length
    windows.value = []
    if (count > 0)
      console.log(`[EditorWindows] Closed all ${count} windows`)
  }

  return {
    windows,
    openWindow,
    closeWindow,
    bringToFront,
    toggleMinimize,
    updatePosition,
    updateDocument,
    getWindow,
    closeAll,
  }
})
