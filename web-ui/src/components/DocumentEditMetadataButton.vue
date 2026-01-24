<script setup lang="ts">
import type { BulkMetadataEditComposable } from '../composables/useBulkMetadataEdit.ts'

import { Icon } from '@iconify/vue'
import MetadataEditModal from './MetadataEditModal.vue'

const props = defineProps<{
  bulkEdit: BulkMetadataEditComposable
}>()
</script>

<template>
  <button type="button" class="btn btn-sm btn-primary gap-1" @click="props.bulkEdit.openModal">
    <Icon icon="heroicons:pencil" />
    Edit Metadata
  </button>

  <!-- Bulk Edit Modal -->
  <MetadataEditModal
    :show="props.bulkEdit.showModal.value"
    :loading="props.bulkEdit.loading.value"
    :selected-count="props.bulkEdit.selectedCount.value"
    :initial-document="props.bulkEdit.initialDocument.value"
    @close="props.bulkEdit.closeModal"
    @submit="props.bulkEdit.handleUpdate"
  />
</template>
