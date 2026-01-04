<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ChunkEditor from '../components/ChunkEditor.vue'

const route = useRoute()
const documentId = ref<string | null>(null)

onMounted(() => {
  // Get document ID from route params or query
  documentId.value = (route.params.id as string) || (route.query.id as string) || null
})
</script>

<template>
  <div class="container mx-auto p-4 h-screen">
    <div v-if="!documentId" class="alert alert-warning">
      <span>No document ID provided. Use /chunks?id=YOUR_DOCUMENT_ID</span>
    </div>

    <ChunkEditor v-else :document-id="documentId" />
  </div>
</template>
