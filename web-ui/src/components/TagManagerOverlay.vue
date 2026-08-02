<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { onMounted, onUnmounted } from 'vue'
import TagManager from './TagManager.vue'

const props = defineProps<{
  show: boolean
  /** Pre-fill the create-tag form, e.g. when opened from TagInput's "no tag called '…'" affordance */
  prefillName?: string
}>()

const emit = defineEmits<{
  close: []
}>()

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
      <div class="modal-content bg-base-100 text-base-content rounded-lg shadow-xl w-full h-full max-w-4xl max-h-[85vh] flex flex-col">
        <div class="modal-header flex justify-between items-center p-4 border-b border-base-300">
          <h2 class="text-xl font-bold">
            <Icon icon="heroicons:tag" class="inline-block mr-2" />
            Manage Tags
          </h2>
          <button
            data-testid="close-tag-manager"
            class="btn btn-sm btn-circle btn-ghost"
            @click="emit('close')"
          >
            <Icon icon="heroicons:x-mark" class="text-xl" />
          </button>
        </div>

        <div class="modal-body flex-1 overflow-hidden p-4">
          <TagManager v-bind:prefill-name="prefillName" />
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
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

.modal-backdrop {
  backdrop-filter: blur(2px);
}
</style>
