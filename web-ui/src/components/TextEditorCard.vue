<script setup lang="ts">
import { ref } from 'vue'
import BaseCard from './BaseCard.vue'
import TextEditor from './TextEditor.vue'

// Props for card configuration
defineProps<{
  icon?: string
}>()

// v-model for editor content - allows parent to control and react to changes
const editorContent = defineModel('content', {
  type: String,
  default: '',
})

const title = defineModel('title', {
  type: String,
  default: '<p>New Document<p>',
})

const isNew = defineModel('isNew', {
  type: Boolean,
  default: false,
})

const documentId = defineModel('documentId', {
  type: String,
  default: '',
})

// Template ref to access the TextEditor component instance
const textEditorRef = ref<InstanceType<typeof TextEditor> | null>(null)

// Expose methods that parent components can call
defineExpose({
  // Reset editor to specific content or default
  resetEditor(content?: string) {
    textEditorRef.value?.resetContent(content)
  },
  // Switch to preview mode
  switchToPreview() {
    textEditorRef.value?.setViewMode('preview')
  },
})
</script>

<template>
  <BaseCard
    v-model:title="title"
    v-bind:icon="icon || 'heroicons:document-text'"
    class="col-span-1 md:col-span-2 xl:col-span-3"
  >
    <input v-model="title" type="text" v-bind:min="100" v-bind:max="2000" class="input input-bordered">
    <!-- Editor with two-way binding to parent's content -->
    <TextEditor ref="textEditorRef" v-model:default-content="editorContent" />
  </BaseCard>
</template>
