<script setup lang="ts">
import type { DecorationSet } from '@codemirror/view'
import type { ChunkBoundary } from '../bibliophage/v1alpha3/embedding_pb'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { EditorState, StateEffect, StateField } from '@codemirror/state'
import { Decoration, EditorView, keymap, WidgetType } from '@codemirror/view'
import { Icon } from '@iconify/vue'
import { marked } from 'marked'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  boundaries?: ChunkBoundary[]
  selectedChunkId?: string | null
}>()

const defaultContent = defineModel('defaultContent', { type: String, default: '' })

// Track view mode: 'edit' or 'preview'
type ViewMode = 'edit' | 'preview'
const viewMode = ref<ViewMode>('edit')

// CodeMirror refs
const editorContainer = ref<HTMLElement | null>(null)
const editorView = ref<EditorView | null>(null)
const renderedMarkdown = ref<string>('')

// State effect for updating chunk boundaries
const updateBoundariesEffect = StateEffect.define<ChunkBoundary[]>()

// State effect for updating selected chunk
const updateSelectedChunkEffect = StateEffect.define<string | null>()

// StateField to track currently selected chunk ID
const selectedChunkIdField = StateField.define<string | null>({
  create() {
    return null
  },
  update(value, tr) {
    for (const effect of tr.effects) {
      if (effect.is(updateSelectedChunkEffect)) {
        return effect.value
      }
    }
    return value
  },
})

// StateField to track current boundaries
const boundariesField = StateField.define<ChunkBoundary[]>({
  create() {
    return []
  },
  update(value, tr) {
    for (const effect of tr.effects) {
      if (effect.is(updateBoundariesEffect)) {
        return effect.value
      }
    }
    return value
  },
})

// Chunk boundary widget for visual overlays
class ChunkBoundaryWidget extends WidgetType {
  constructor(readonly boundary: ChunkBoundary) {
    super()
  }

  toDOM() {
    const div = document.createElement('div')
    div.className = 'chunk-boundary-widget'
    div.textContent = `═══ ${this.boundary.description || this.boundary.chunkId} ═══`
    div.setAttribute('data-chunk-id', this.boundary.chunkId)
    return div
  }

  eq(other: ChunkBoundaryWidget) {
    return this.boundary.chunkId === other.boundary.chunkId
  }
}

// TODO: Future enhancement - derive colors from DaisyUI theme variables
// Currently using static dark colors for good contrast with light text on dark backgrounds
// Would be nice to compute from --p, --s, --a, --in, --su, --wa theme variables

// Chunk background colors - dark with transparency for light text on dark backgrounds
const chunkHighlightTheme = EditorView.baseTheme({
  '.cm-chunk-bg-0': { backgroundColor: 'rgba(80, 60, 120, 0.25)' }, // Dark purple
  '.cm-chunk-bg-1': { backgroundColor: 'rgba(120, 60, 100, 0.25)' }, // Dark pink
  '.cm-chunk-bg-2': { backgroundColor: 'rgba(60, 100, 120, 0.25)' }, // Dark cyan
  '.cm-chunk-bg-3': { backgroundColor: 'rgba(60, 80, 120, 0.25)' }, // Dark blue
  '.cm-chunk-bg-4': { backgroundColor: 'rgba(60, 120, 80, 0.25)' }, // Dark green
  '.cm-chunk-bg-5': { backgroundColor: 'rgba(120, 80, 60, 0.25)' }, // Dark orange
  '.cm-chunk-bg-selected': { backgroundColor: 'rgba(100, 80, 140, 0.4)' }, // Selected (more prominent)
})

// Helper function to build decorations from boundaries
function buildDecorations(boundaries: ChunkBoundary[], selectedChunkId: string | null, doc: any) {
  const newDecos: any[] = []

  for (let i = 0; i < boundaries.length; i++) {
    const boundary = boundaries[i]

    try {
      // Determine CSS class based on selection state
      const isSelected = boundary.chunkId === selectedChunkId
      const cssClass = isSelected ? 'cm-chunk-bg-selected' : `cm-chunk-bg-${i % 6}`

      // Add mark decoration with CSS class
      newDecos.push(
        Decoration.mark({
          class: cssClass,
          attributes: { 'data-chunk-id': boundary.chunkId },
        }).range(boundary.charStart, boundary.charEnd),
      )

      // Add widget decoration for boundary marker
      const line = doc.lineAt(boundary.charStart)
      newDecos.push(
        Decoration.widget({
          widget: new ChunkBoundaryWidget(boundary),
          block: true,
          side: -1,
        }).range(line.from),
      )
    }
    catch (e) {
      // Boundary position out of range, skip
      console.warn(`Chunk boundary ${boundary.chunkId} out of range`, e)
    }
  }

  return Decoration.set(newDecos, true)
}

// StateField for managing chunk boundary decorations
const chunkBoundaryField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none
  },

  update(decorations, tr) {
    // Map existing decorations through document changes
    decorations = decorations.map(tr.changes)

    let needsRebuild = false

    // Check for effects that require decoration rebuild
    for (const effect of tr.effects) {
      if (effect.is(updateBoundariesEffect) || effect.is(updateSelectedChunkEffect)) {
        needsRebuild = true
        break
      }
    }

    // Rebuild decorations if needed
    if (needsRebuild) {
      const boundaries = tr.state.field(boundariesField)
      const selectedChunkId = tr.state.field(selectedChunkIdField)
      decorations = buildDecorations(boundaries, selectedChunkId, tr.state.doc)
    }

    return decorations
  },

  provide: f => EditorView.decorations.from(f),
})

// Initialize CodeMirror editor
onMounted(() => {
  if (!editorContainer.value)
    return

  const state = EditorState.create({
    doc: defaultContent.value,
    extensions: [
      markdown(),
      history(),
      keymap.of([...defaultKeymap, ...historyKeymap]),
      boundariesField,
      selectedChunkIdField,
      chunkBoundaryField,
      chunkHighlightTheme,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          defaultContent.value = update.state.doc.toString()
        }
      }),
      EditorView.lineWrapping,
      EditorView.theme({
        '&': {
          backgroundColor: 'transparent',
          color: 'inherit',
          fontSize: '14px',
        },
        '.cm-content': {
          fontFamily: 'ui-monospace, monospace',
          padding: '0',
        },
        '.cm-line': {
          padding: '0 4px',
        },
        '.cm-cursor': {
          borderLeftColor: 'oklch(var(--p))',
        },
        '.cm-selectionBackground': {
          backgroundColor: 'oklch(var(--p) / 0.2)',
        },
        '&.cm-focused .cm-selectionBackground': {
          backgroundColor: 'oklch(var(--p) / 0.3)',
        },
      }),
    ],
  })

  editorView.value = new EditorView({
    state,
    parent: editorContainer.value,
  })
})

// Watch for external content changes
watch(defaultContent, (newContent) => {
  if (editorView.value && editorView.value.state.doc.toString() !== newContent) {
    editorView.value.dispatch({
      changes: {
        from: 0,
        to: editorView.value.state.doc.length,
        insert: newContent,
      },
    })
  }
})

// Watch for boundary changes
watch(() => props.boundaries, (newBoundaries) => {
  if (editorView.value && newBoundaries) {
    editorView.value.dispatch({
      effects: updateBoundariesEffect.of(newBoundaries),
    })
  }
}, { deep: true })

// Watch for selected chunk changes
watch(() => props.selectedChunkId, (newSelectedId) => {
  if (editorView.value) {
    editorView.value.dispatch({
      effects: updateSelectedChunkEffect.of(newSelectedId ?? null),
    })
  }
}, { immediate: true })

// Toggle between edit and preview modes
function toggleViewMode() {
  viewMode.value = viewMode.value === 'edit' ? 'preview' : 'edit'
  if (viewMode.value === 'preview') {
    updatePreview()
  }
}

// Update preview rendering
function updatePreview() {
  const content = editorView.value?.state.doc.toString() || defaultContent.value
  renderedMarkdown.value = marked.parse(content) as string
}

// Cleanup on unmount
onBeforeUnmount(() => {
  if (editorView.value) {
    editorView.value.destroy()
  }
})

// Expose methods that parent components can call
defineExpose({
  resetContent(passedContent?: string) {
    defaultContent.value = passedContent ?? ''
    if (editorView.value) {
      editorView.value.dispatch({
        changes: {
          from: 0,
          to: editorView.value.state.doc.length,
          insert: passedContent ?? '',
        },
      })
    }
  },
  setViewMode(mode: ViewMode) {
    viewMode.value = mode
    if (mode === 'preview') {
      updatePreview()
    }
  },
  getEditor() {
    return editorView.value
  },
  scrollToPosition(pos: number) {
    if (editorView.value) {
      editorView.value.dispatch({
        selection: { anchor: pos },
        scrollIntoView: true,
      })
      editorView.value.focus()
    }
  },
})
</script>

<template>
  <div class="markdown-editor w-full">
    <!-- Toolbar -->
    <div class="mb-4 p-3 bg-base-200 rounded-t-lg flex gap-2">
      <!-- View Mode Toggle -->
      <button
        class="btn btn-sm btn-primary"
        v-bind:title="viewMode === 'edit' ? 'Switch to preview' : 'Switch to edit'"
        @click="toggleViewMode"
      >
        <Icon v-if="viewMode === 'edit'" icon="mdi:eye" />
        <Icon v-else icon="mdi:pencil" />
        <span>{{ viewMode === 'edit' ? 'Preview' : 'Edit' }}</span>
      </button>

      <div class="text-sm text-base-content/60 flex items-center ml-2">
        {{ viewMode === 'edit' ? 'Editing markdown source' : 'Preview rendering' }}
      </div>
    </div>

    <!-- Editor/Preview Area -->
    <div class="border border-t-0 border-base-300 rounded-b-lg overflow-hidden">
      <div class="relative bg-base-100">
        <!-- Runic watermark -->
        <!-- walliþ nu, gaþankōz" -->
        <!-- double consontant represented by single laguz -->
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
          <div class="text-base-200 font-serif text-3xl font-light tracking-[0.3em]">
            ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ
          </div>
        </div>

        <!-- CodeMirror Editor (edit mode) -->
        <div
          v-show="viewMode === 'edit'"
          ref="editorContainer"
          class="codemirror-wrapper w-full h-96 bg-transparent relative z-10 overflow-y-auto"
        />

        <!-- Markdown Preview (preview mode) -->
        <div
          v-show="viewMode === 'preview'"
          class="markdown-preview w-full h-96 p-4 bg-transparent relative z-10 overflow-y-auto prose prose-sm max-w-none"
          v-html="renderedMarkdown"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* CodeMirror base styling */
:deep(.codemirror-wrapper) {
  outline: none;
}

:deep(.codemirror-wrapper .cm-editor) {
  outline: none;
  height: 100%;
}

:deep(.cm-scroller) {
  overflow: auto;
}

/* Chunk boundary widget styling */
:deep(.chunk-boundary-widget) {
  border-top: 2px dashed oklch(var(--bc) / 0.3);
  padding: 0.5rem 0;
  margin: 1rem 0;
  text-align: center;
  color: oklch(var(--bc) / 0.5);
  font-family: monospace;
  font-size: 0.875rem;
  user-select: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

:deep(.chunk-boundary-widget:hover) {
  border-color: oklch(var(--p));
  color: oklch(var(--p));
  background-color: oklch(var(--p) / 0.05);
}

/* Markdown preview prose styles */
:deep(.markdown-preview) {
  color: inherit;
}

:deep(.markdown-preview h1) {
  font-size: 1.8rem;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(.markdown-preview h2) {
  font-size: 1.5rem;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(.markdown-preview h3) {
  font-size: 1.25rem;
  font-weight: bold;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

:deep(.markdown-preview h4),
:deep(.markdown-preview h5),
:deep(.markdown-preview h6) {
  font-weight: bold;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

:deep(.markdown-preview p) {
  margin-bottom: 1rem;
}

:deep(.markdown-preview ul),
:deep(.markdown-preview ol) {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

:deep(.markdown-preview li) {
  margin: 0.25rem 0;
}

:deep(.markdown-preview blockquote) {
  border-left: 3px solid oklch(var(--bc) / 0.3);
  margin: 1.5rem 0;
  padding-left: 1rem;
  color: oklch(var(--bc) / 0.7);
}

:deep(.markdown-preview code) {
  background-color: oklch(var(--b2));
  border-radius: 0.25rem;
  padding: 0.15em 0.3em;
  font-size: 0.875em;
  font-family: ui-monospace, monospace;
}

:deep(.markdown-preview pre) {
  background: oklch(var(--b3));
  color: oklch(var(--bc));
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}

:deep(.markdown-preview pre code) {
  background: none;
  padding: 0;
  font-size: 0.875rem;
}

:deep(.markdown-preview a) {
  color: oklch(var(--p));
  text-decoration: underline;
}

:deep(.markdown-preview a:hover) {
  color: oklch(var(--pf));
}

:deep(.markdown-preview img) {
  max-width: 100%;
  height: auto;
  margin: 1rem 0;
}

:deep(.markdown-preview table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

:deep(.markdown-preview th),
:deep(.markdown-preview td) {
  border: 1px solid oklch(var(--bc) / 0.2);
  padding: 0.5rem;
  text-align: left;
}

:deep(.markdown-preview th) {
  background-color: oklch(var(--b2));
  font-weight: bold;
}

:deep(.markdown-preview hr) {
  border: none;
  border-top: 1px solid oklch(var(--bc) / 0.2);
  margin: 2rem 0;
}
</style>
