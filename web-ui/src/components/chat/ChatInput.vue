<script setup lang="ts">
import { Icon } from '@iconify/vue'
import Placeholder from '@tiptap/extension-placeholder'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { onBeforeUnmount, watch } from 'vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

// Tiptap editor setup
const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: 'Type your message...',
    }),
  ],
  editorProps: {
    attributes: {
      class: 'prose prose-sm max-w-none focus:outline-none min-h-[60px] p-3',
    },
  },
})

// Cleanup on unmount
onBeforeUnmount(() => {
  editor.value?.destroy()
})

// Disable editor when streaming
watch(
  () => props.disabled,
  (disabled) => {
    editor.value?.setEditable(!disabled)
  },
)

function handleSend() {
  if (!editor.value)
    return

  const text = editor.value.getText().trim()
  if (!text)
    return

  emit('send', text)

  // Clear editor after sending
  editor.value.commands.clearContent()
}

function handleKeydown(event: KeyboardEvent) {
  // Send on Cmd+Enter or Ctrl+Enter
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="border border-base-300 rounded-lg bg-base-100">
    <EditorContent
      v-bind:editor="editor"
      class="min-h-[80px] max-h-[200px] overflow-y-auto"
      @keydown="handleKeydown"
    />
    <div class="border-t border-base-300 p-2 flex justify-between items-center">
      <span class="text-xs text-base-content/50"> Press Cmd+Enter to send </span>
      <button class="btn btn-primary btn-sm" v-bind:disabled="disabled" @click="handleSend">
        <Icon icon="heroicons:paper-airplane" />
        Send
      </button>
    </div>
  </div>
</template>
