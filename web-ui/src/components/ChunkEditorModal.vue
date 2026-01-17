<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { onMounted, onUnmounted } from 'vue'
import ChunkEditor from './ChunkEditor.vue'

const props = defineProps<{
  documentId: string
  show: boolean
}>()

const emit = defineEmits<{
  close: []
}>()
// Handle ESC key to close
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.show) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

function handleBackdropClick(event: MouseEvent) {
  // Only close if clicking the backdrop, not the modal content
  if (event.target === event.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <Transition name="modal">
    <div
      v-if="show"
      class="modal-backdrop fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click="handleBackdropClick"
    >
      <div class="modal-content bg-base-100 text-base-content rounded-lg shadow-xl w-full h-full max-w-7xl max-h-[90vh] flex flex-col">
        <!-- Modal Header -->
        <div class="modal-header flex justify-between items-center p-4 border-b border-base-300">
          <h2 class="text-xl font-bold">
            <Icon icon="heroicons:cube" class="inline-block mr-2" />
            Chunk & Embed Document
          </h2>
          <button
            class="btn btn-sm btn-circle btn-ghost"
            @click="emit('close')"
          >
            <Icon icon="heroicons:x-mark" class="text-xl" />
          </button>
        </div>

        <!-- Modal Body -->
        <div class="modal-body flex-1 overflow-hidden p-4">
          <ChunkEditor v-bind:document-id="documentId" />
        </div>

        <!-- Modal Footer -->
        <div class="modal-footer flex justify-end gap-2 p-4 border-t border-base-300">
          <button class="btn btn-ghost" @click="emit('close')">
            Close
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95);
}

/* Ensure modal is above everything */
.modal-backdrop {
  backdrop-filter: blur(2px);
}
</style>
