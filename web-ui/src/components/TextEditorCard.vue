<script setup lang="ts">
import { ref } from 'vue'
import BaseCard from './BaseCard.vue'
import TextEditor from './TextEditor.vue'

// Props for card configuration
defineProps<{
  icon?: string
}>()

// Define events that parent components can listen to
const emit = defineEmits<{
  save: []
  abort: []
}>()

// v-model for editor content - allows parent to control and react to changes
const editorContent = defineModel('content', {
  type: String,
  default: '<p>ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ<p>',
})

const title = defineModel('title', {
  type: String,
  default: '<p>New Document<p>',
})

// Template ref to access the TextEditor component instance
const textEditorRef = ref<InstanceType<typeof TextEditor> | null>(null)

// Event handlers that emit to parent
function handleSave() {
  emit('save')
}

function handleAbort() {
  emit('abort')
}

// Expose methods that parent components can call
defineExpose({
  // Reset editor to specific content or default
  resetEditor(content?: string) {
    textEditorRef.value?.resetContent(content)
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
    <form @submit.prevent="handleSave" @reset.prevent="handleAbort">
      <!-- Editor with two-way binding to parent's content -->
      <TextEditor ref="textEditorRef" v-model:default-content="editorContent" />

      <div class="flex center-safe justify-between">
        <button
          type="submit"
          class="btn btn-primary btn-lg w-fit gap-2 justify-items-start"
        >
          <p>Save</p>
        </button>
        <button
          type="reset"
          class="btn btn-error btn-lg w-fit gap-2 justify-items-end"
        >
          <p>Abort</p>
        </button>
      </div>
    </form>
  </BaseCard>
</template>
