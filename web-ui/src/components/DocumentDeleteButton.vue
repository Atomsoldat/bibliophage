<script setup lang="ts">
import type { BulkDeleteComposable } from '../composables/useBulkDelete.ts'

import { Icon } from '@iconify/vue'

const props = defineProps<{
  bulkDelete: BulkDeleteComposable
}>()
</script>

<template>
  <button type="button" class="btn btn-sm btn-error gap-1" @click="props.bulkDelete.openModal">
    <Icon icon="heroicons:trash" />
    Delete
  </button>

  <!-- Delete Confirmation Modal -->
  <dialog class="modal" :class="{ 'modal-open': props.bulkDelete.showModal.value }">
    <div class="modal-box">
      <h3 class="text-lg font-bold">
        Confirm Deletion
      </h3>
      <p class="py-4">
        Are you sure you want to delete
        <strong>{{ props.bulkDelete.selectedCount.value }}</strong>
        document{{ props.bulkDelete.selectedCount.value > 1 ? 's' : '' }}?
      </p>

      <!-- List affected documents -->
      <ul v-if="props.bulkDelete.selectedDocumentNames.value.length > 0" class="list-disc list-inside mb-4 max-h-40 overflow-y-auto">
        <li v-for="name in props.bulkDelete.selectedDocumentNames.value" :key="name" class="truncate">
          {{ name }}
        </li>
      </ul>

      <p class="text-warning text-sm">
        <Icon icon="heroicons:exclamation-triangle" class="inline" />
        This action cannot be undone.
      </p>

      <div class="modal-action">
        <button
          type="button"
          class="btn btn-ghost"
          :disabled="props.bulkDelete.loading.value"
          @click="props.bulkDelete.closeModal"
        >
          Cancel
        </button>
        <button
          type="button"
          class="btn btn-error gap-1"
          :disabled="props.bulkDelete.loading.value"
          @click="props.bulkDelete.handleDelete"
        >
          <span v-if="props.bulkDelete.loading.value" class="loading loading-spinner loading-sm" />
          <Icon v-else icon="heroicons:trash" />
          Delete {{ props.bulkDelete.selectedCount.value > 1 ? 'All' : '' }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop" @click="props.bulkDelete.closeModal">
      <button type="button">close</button>
    </form>
  </dialog>
</template>
