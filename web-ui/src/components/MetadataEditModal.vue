<script setup lang="ts">
import type { DocumentListItem } from '../bibliophage/v1alpha3/document_pb.ts'

import { Icon } from '@iconify/vue'
import { onMounted, onUnmounted, ref, watch } from 'vue'

export interface MetadataEditFormData {
  type: string | null
  tags: { name: string, values: string[] }[] | null
}

const props = defineProps<{
  show: boolean
  loading?: boolean
  selectedCount: number
  /** When single document is selected, pass it for pre-population */
  initialDocument?: DocumentListItem | null
}>()

const emit = defineEmits<{
  close: []
  submit: [data: MetadataEditFormData]
}>()

// Form state
const typeInput = ref('')
const tagsInput = ref('')

// Pre-populate form when a single document is provided
watch(() => props.initialDocument, (doc) => {
  if (doc) {
    typeInput.value = doc.metadata?.publicationType || ''
    tagsInput.value = doc.tags.map(tag => `${tag.name}:${tag.values.join('|')}`).join(', ')
  }
  else {
    // Clear fields for multiple selection
    typeInput.value = ''
    tagsInput.value = ''
  }
}, { immediate: true })

// Reset form when modal opens
watch(() => props.show, (isVisible) => {
  if (!isVisible) {
    // Reset on close
    typeInput.value = ''
    tagsInput.value = ''
  }
})

function parseFormData(): MetadataEditFormData {

  // Parse type: trimmed string, null if empty
  const type = typeInput.value.trim() || null

  // Parse tags: "name:value1|value2, name2:value3" format
  const tagsTrimmed = tagsInput.value.trim()
  const tags = tagsTrimmed
    ? tagsTrimmed.split(',').map((tagStr) => {
        const colonIndex = tagStr.indexOf(':')
        if (colonIndex === -1)
          return null
        const name = tagStr.slice(0, colonIndex).trim()
        const valuesStr = tagStr.slice(colonIndex + 1)
        if (!name || !valuesStr)
          return null
        const values = valuesStr.split('|').map(v => v.trim()).filter(v => v.length > 0)
        if (values.length === 0)
          return null
        return { name, values }
      }).filter((tag): tag is { name: string, values: string[] } => tag !== null)
    : null

  return { type, tags }
}

function handleSubmit() {
  const data = parseFormData()
  emit('submit', data)
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
            Edit Metadata for {{ selectedCount }} Document{{ selectedCount > 1 ? 's' : '' }}
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
          <div class="alert alert-warning mb-4">
            <Icon icon="heroicons:exclamation-triangle" class="text-xl" />
            <span>Only non-empty fields will be updated. Leave a field empty to keep existing values.</span>
          </div>

          <form id="bulk-edit-form" class="space-y-4" @submit.prevent="handleSubmit">

            <!-- Type Input -->
            <div class="form-control">
              <label class="label" for="bulk-type">
                <span class="label-text">Type</span>
                <span class="label-text-alt text-base-content/50">e.g., Core Rulebook, Adventure</span>
              </label>
              <input
                id="bulk-type"
                v-model="typeInput"
                type="text"
                placeholder="Leave empty to keep existing values"
                class="input input-bordered w-full"
                v-bind:disabled="loading"
              >
            </div>

            <!-- Tags Input -->
            <div class="form-control">
              <label class="label" for="bulk-tags">
                <span class="label-text">Tags (format: name:value1|value2, name2:value3)</span>
                <span class="label-text-alt text-base-content/50">e.g., genre:fantasy|horror, campaign:storm-king</span>
              </label>
              <input
                id="bulk-tags"
                v-model="tagsInput"
                type="text"
                placeholder="Leave empty to keep existing values"
                class="input input-bordered w-full"
                v-bind:disabled="loading"
              >
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
