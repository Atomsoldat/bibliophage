import { computed, ref } from 'vue'

/**
 * Configuration for an editor window instance
 */
export interface EditorWindowConfig {
  id: string
  documentId: string
  title: string
  content: string
  isNew: boolean
  x: number
  y: number
  zIndex: number
  isMinimized: boolean
}

// Global state for window management
const windows = ref<EditorWindowConfig[]>([])
let nextWindowId = 1
let nextZIndex = 10

// Positioning constants
const INITIAL_OFFSET = { x: 100, y: 100 }
const CASCADE_OFFSET = 30

/**
 * Composable for global editor window management
 *
 * Provides a singleton-like system for managing floating editor windows
 * that persist across view changes. Windows are managed globally and
 * rendered by the GlobalEditorWindows component in App.vue.
 *
 * @example
 * const { openWindow, closeWindow } = useEditorWindows()
 * openWindow({ title: 'My Document', content: 'Hello world!' })
 */
export function useEditorWindows() {
  function calculatePosition(index: number): { x: number; y: number } {
    const offset = index * CASCADE_OFFSET
    return {
      x: INITIAL_OFFSET.x + offset,
      y: INITIAL_OFFSET.y + offset,
    }
  }

  function openWindow(config: {
    documentId?: string
    title?: string
    content?: string
    isNew?: boolean
    x?: number
    y?: number
  }): string {
    const windowId = `editor-window-${nextWindowId++}`
    const position = config.x !== undefined && config.y !== undefined
      ? { x: config.x, y: config.y }
      : calculatePosition(windows.value.length)

    const newWindow: EditorWindowConfig = {
      id: windowId,
      documentId: config.documentId || '',
      title: config.title || 'New Document',
      content: config.content || '',
      isNew: config.isNew ?? true,
      x: position.x,
      y: position.y,
      zIndex: nextZIndex++,
      isMinimized: false,
    }

    windows.value.push(newWindow)
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
    const window = windows.value.find(w => w.id === windowId)
    if (window) {
      window.zIndex = nextZIndex++
    }
  }

  function toggleMinimize(windowId: string): void {
    const window = windows.value.find(w => w.id === windowId)
    if (window) {
      window.isMinimized = !window.isMinimized
    }
  }

  function updatePosition(windowId: string, x: number, y: number): void {
    const window = windows.value.find(w => w.id === windowId)
    if (window) {
      window.x = x
      window.y = y
    }
  }

  function updateDocument(windowId: string, updates: {
    documentId?: string
    title?: string
    content?: string
    isNew?: boolean
  }): void {
    const window = windows.value.find(w => w.id === windowId)
    if (window) {
      if (updates.documentId !== undefined) window.documentId = updates.documentId
      if (updates.title !== undefined) window.title = updates.title
      if (updates.content !== undefined) window.content = updates.content
      if (updates.isNew !== undefined) window.isNew = updates.isNew
    }
  }

  function getWindow(windowId: string): EditorWindowConfig | undefined {
    return windows.value.find(w => w.id === windowId)
  }

  function closeAll(): void {
    const count = windows.value.length
    windows.value = []
    if (count > 0) {
      console.log(`[EditorWindows] Closed all ${count} windows`)
    }
  }

  return {
    windows: computed(() => windows.value),
    openWindow,
    closeWindow,
    bringToFront,
    toggleMinimize,
    updatePosition,
    updateDocument,
    getWindow,
    closeAll,
  }
}
