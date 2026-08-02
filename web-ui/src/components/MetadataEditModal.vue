<script setup lang="ts">
import type { Tag } from '../bibliophage/v1alpha3/tag_pb.ts'

import { Icon } from '@iconify/vue'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import TagInput from './TagInput.vue'

export interface MetadataEditFormData {
  tagsToAdd: Tag[]
  tagsToRemove: Tag[]
}

const props = defineProps<{
  show: boolean
  loading?: boolean
  selectedCount: number
}>()

const emit = defineEmits<{
  close: []
  submit: [data: MetadataEditFormData]
}>()

const tagsToAdd = ref<Tag[]>([])
const tagsToRemove = ref<Tag[]>([])

// Reset form when modal opens
watch(() => props.show, (isVisible) => {
  if (!isVisible) {
    tagsToAdd.value = []
    tagsToRemove.value = []
  }
})

function handleSubmit() {
  emit('submit', { tagsToAdd: tagsToAdd.value, tagsToRemove: tagsToRemove.value })
}

// Handle ESC key to close
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.show && !props.loading) {
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
  if (event.target === event.currentTarget && !props.loading) {
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
      <div class="modal-content bg-base-100 text-base-content rounded-lg shadow-xl w-full max-w-2xl flex flex-col">
        <!-- Modal Header -->
        <div class="modal-header flex justify-between items-center p-4 border-b border-base-300">
          <h3 class="text-xl font-bold">
            <Icon icon="heroicons:pencil-square" class="inline-block mr-2" />
            Edit Tags for {{ selectedCount }} Document{{ selectedCount > 1 ? 's' : '' }}
          </h3>
          <button
            class="btn btn-sm btn-circle btn-ghost"
            v-bind:disabled="loading"
            @click="emit('close')"
          >
            <Icon icon="heroicons:x-mark" class="text-xl" />
          </button>
        </div>

        <!-- Modal Body -->
        <div class="modal-body flex-1 overflow-y-auto p-4">
          <form id="bulk-edit-form" class="space-y-4" @submit.prevent="handleSubmit">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Tags to add</span>
                <span class="label-text-alt text-base-content/50">applied to every selected document</span>
              </label>
              <TagInput v-model="tagsToAdd" mode="collect" />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Tags to remove</span>
                <span class="label-text-alt text-base-content/50">removed from every selected document, if present</span>
              </label>
              <TagInput v-model="tagsToRemove" mode="collect" />
            </div>
          </form>
        </div>

        <!-- Modal Footer -->
        <div class="modal-footer flex justify-end gap-2 p-4 border-t border-base-300">
          <button
            type="button"
            class="btn btn-ghost"
            v-bind:disabled="loading"
            @click="emit('close')"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="bulk-edit-form"
            class="btn btn-primary"
            v-bind:disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm" />
            {{ loading ? 'Updating...' : 'Update Documents' }}
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

.modal-backdrop {
  backdrop-filter: blur(2px);
}
</style>
