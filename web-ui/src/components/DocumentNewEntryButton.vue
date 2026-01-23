<script setup lang="ts">
import { Icon } from '@iconify/vue'

import { useEditorWindows } from '../composables/useEditorWindows.ts'
import { useLogger } from '../composables/useLogger.ts'

const { openWindow } = useEditorWindows()
const logger = useLogger()

function handleNewEntry() {
  openWindow({
    title: 'New Journal Entry',
    content: '',
    documentId: '',
    isNew: true,
  })
  logger.info('Opened new journal entry')
}
</script>

<template>
  <!-- Create New Document Button -->
  <button
    type="button"
    class="btn btn-primary btn-lg gap-2"
    @click="handleNewEntry"
  >
    <Icon icon="heroicons:plus" />
    New Entry
  </button>
</template>
