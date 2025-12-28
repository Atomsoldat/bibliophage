<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { marked } from 'marked'
import { computed, ref } from 'vue'

const defaultContent = defineModel('defaultContent', { type: String, default: '' })

// Track view mode: 'edit' or 'preview'
type ViewMode = 'edit' | 'preview'
const viewMode = ref<ViewMode>('edit')

// Rendered HTML from markdown
const renderedHtml = computed(() => {
  try {
    return marked.parse(defaultContent.value)
  }
  catch (error) {
    return `<p class="text-error">Error rendering markdown: ${(error as Error).message}</p>`
  }
})

// Toggle between edit and preview modes
function toggleViewMode() {
  viewMode.value = viewMode.value === 'edit' ? 'preview' : 'edit'
}

// Handle textarea input
function handleMarkdownInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  defaultContent.value = target.value
}

// Expose methods that parent components can call
defineExpose({
  resetContent(passedContent?: string) {
    defaultContent.value = passedContent ?? ''
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

        <!-- Edit Mode: Plain textarea -->
        <textarea
          v-if="viewMode === 'edit'"
          name="markdown-editor"
          v-bind:value="defaultContent"
          class="textarea textarea-bordered w-full h-96 font-mono text-sm p-4 bg-transparent rounded-none border-0 focus:outline-none resize-none relative z-10 overflow-y-auto"
          spellcheck="false"
          placeholder="Start writing markdown..."
          @input="handleMarkdownInput"
        />

        <!-- Preview Mode: Rendered HTML -->
        <div
          v-else
          class="prose max-w-none p-4 h-96 bg-transparent relative z-10 overflow-y-auto"
          v-html="renderedHtml"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Prose styles for rendered markdown */
:deep(.prose) {
  color: inherit;
}

:deep(.prose h1) {
  font-size: 1.8rem;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(.prose h2) {
  font-size: 1.5rem;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(.prose h3) {
  font-size: 1.25rem;
  font-weight: bold;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

:deep(.prose h4),
:deep(.prose h5),
:deep(.prose h6) {
  font-weight: bold;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

:deep(.prose p) {
  margin-bottom: 1rem;
}

:deep(.prose ul),
:deep(.prose ol) {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

:deep(.prose li) {
  margin: 0.25rem 0;
}

:deep(.prose blockquote) {
  border-left: 3px solid oklch(var(--bc) / 0.3);
  margin: 1.5rem 0;
  padding-left: 1rem;
  color: oklch(var(--bc) / 0.7);
}

:deep(.prose code) {
  background-color: oklch(var(--b2));
  border-radius: 0.25rem;
  padding: 0.15em 0.3em;
  font-size: 0.875em;
  font-family: ui-monospace, monospace;
}

:deep(.prose pre) {
  background: oklch(var(--b3));
  color: oklch(var(--bc));
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}

:deep(.prose pre code) {
  background: none;
  padding: 0;
  font-size: 0.875rem;
}

:deep(.prose a) {
  color: oklch(var(--p));
  text-decoration: underline;
}

:deep(.prose a:hover) {
  color: oklch(var(--pf));
}

:deep(.prose img) {
  max-width: 100%;
  height: auto;
  margin: 1rem 0;
}

:deep(.prose table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

:deep(.prose th),
:deep(.prose td) {
  border: 1px solid oklch(var(--bc) / 0.2);
  padding: 0.5rem;
  text-align: left;
}

:deep(.prose th) {
  background-color: oklch(var(--b2));
  font-weight: bold;
}

:deep(.prose hr) {
  border: none;
  border-top: 1px solid oklch(var(--bc) / 0.2);
  margin: 2rem 0;
}
</style>
