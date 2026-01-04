<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, onMounted, ref } from 'vue'
import type { ChunkBoundary } from '../bibliophage/v1alpha3/embedding_pb'
import { ChunkingConfig, ChunkingStrategy } from '../bibliophage/v1alpha3/embedding_pb'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useEmbeddingApi } from '../composables/useEmbeddingApi'
import TextEditor from './TextEditor.vue'

const props = defineProps<{
  documentId: string
}>()

// API composables
const documentApi = useDocumentApi()
const embeddingApi = useEmbeddingApi()

// State
const documentContent = ref('')
const documentName = ref('')
const boundaries = ref<ChunkBoundary[]>([])
const selectedStrategy = ref<ChunkingStrategy>(ChunkingStrategy.MARKDOWN_STRUCTURE)
const tokenChunkSize = ref(600)
const tokenChunkOverlap = ref(50)
const maxHeadingLevel = ref(3)
const isProposing = ref(false)
const isEmbedding = ref(false)
const selectedChunkId = ref<string | null>(null)
const embeddingStatus = ref<{
  isEmbedded: boolean
  embeddingsCurrent: boolean
  totalChunks: number
} | null>(null)

// Editor ref
const textEditorRef = ref<InstanceType<typeof TextEditor> | null>(null)

// Chunk statistics
const chunkStats = computed(() => {
  if (boundaries.value.length === 0) {
    return null
  }

  const sizes = boundaries.value.map(b => b.charEnd - b.charStart)
  const total = sizes.reduce((sum, size) => sum + size, 0)
  const avg = Math.round(total / sizes.length)
  const min = Math.min(...sizes)
  const max = Math.max(...sizes)

  return {
    count: boundaries.value.length,
    avg,
    min,
    max,
  }
})

// Strategy options
const strategyOptions = [
  { value: ChunkingStrategy.MARKDOWN_STRUCTURE, label: 'Markdown Structure' },
  { value: ChunkingStrategy.TOKEN_BASED, label: 'Token-Based' },
  { value: ChunkingStrategy.MARKDOWN_WITH_TOKEN_LIMIT, label: 'Markdown + Token Limit' },
  { value: ChunkingStrategy.PDF_PAGE_BASED, label: 'PDF Page-Based' },
]

// Load document content
async function loadDocument() {
  try {
    const response = await documentApi.getDocument(props.documentId)
    if (response.document) {
      documentContent.value = response.document.content || ''
      documentName.value = response.document.name
    }
  }
  catch (error) {
    console.error('Failed to load document:', error)
  }
}

// Load existing chunk boundaries
async function loadChunkBoundaries() {
  try {
    const response = await embeddingApi.getChunkBoundaries(props.documentId)
    if (response.boundaries) {
      boundaries.value = response.boundaries
    }
    if (response.embeddingStatus) {
      embeddingStatus.value = {
        isEmbedded: response.embeddingStatus.isEmbedded,
        embeddingsCurrent: response.embeddingStatus.embeddingsCurrent,
        totalChunks: response.embeddingStatus.totalChunks,
      }
    }
  }
  catch (error) {
    console.error('Failed to load chunk boundaries:', error)
  }
}

// Propose chunks based on selected strategy
async function proposeChunks() {
  isProposing.value = true
  try {
    const config: Partial<ChunkingConfig> = {
      strategy: selectedStrategy.value,
    }

    // Add strategy-specific config
    if (selectedStrategy.value === ChunkingStrategy.TOKEN_BASED
      || selectedStrategy.value === ChunkingStrategy.MARKDOWN_WITH_TOKEN_LIMIT) {
      config.tokenChunkSize = tokenChunkSize.value
      config.tokenChunkOverlap = tokenChunkOverlap.value
    }

    if (selectedStrategy.value === ChunkingStrategy.MARKDOWN_STRUCTURE
      || selectedStrategy.value === ChunkingStrategy.MARKDOWN_WITH_TOKEN_LIMIT) {
      config.maxHeadingLevel = maxHeadingLevel.value
    }

    const response = await embeddingApi.proposeChunks(props.documentId, config)

    if (response.proposal && response.proposal.boundaries.length > 0) {
      boundaries.value = response.proposal.boundaries
      console.log(`Successfully proposed ${response.proposal.boundaries.length} chunks`)
    }
    else {
      console.error('Failed to propose chunks:', response.message || 'No boundaries returned')
      console.error(response)
    }
  }
  catch (error) {
    console.error('Error proposing chunks:', error)
  }
  finally {
    isProposing.value = false
  }
}

// Embed document with current boundaries
async function embedDocument() {
  isEmbedding.value = true
  try {
    const config: Partial<ChunkingConfig> = {
      strategy: selectedStrategy.value,
      tokenChunkSize: tokenChunkSize.value,
      tokenChunkOverlap: tokenChunkOverlap.value,
      maxHeadingLevel: maxHeadingLevel.value,
    }

    const response = await embeddingApi.embedDocument(
      props.documentId,
      config,
      boundaries.value,
    )

    if (response.success && response.embeddingStatus) {
      embeddingStatus.value = {
        isEmbedded: response.embeddingStatus.isEmbedded,
        embeddingsCurrent: response.embeddingStatus.embeddingsCurrent,
        totalChunks: response.embeddingStatus.totalChunks,
      }
    }
    else {
      console.error('Failed to embed document:', response.message)
    }
  }
  catch (error) {
    console.error('Error embedding document:', error)
  }
  finally {
    isEmbedding.value = false
  }
}

// Handle chunk click - scroll to position in editor
function handleChunkClick(boundary: ChunkBoundary) {
  selectedChunkId.value = boundary.chunkId
  textEditorRef.value?.scrollToPosition(boundary.charStart)
}

// Initialize
onMounted(async () => {
  await documentApi.initialise()
  await embeddingApi.initialise()
  await loadDocument()
  await loadChunkBoundaries()
})
</script>

<template>
  <div class="chunk-editor h-full flex flex-col">
    <!-- Header -->
    <div class="mb-4">
      <h2 class="text-2xl font-bold mb-4">
        {{ documentName }}
      </h2>

      <!-- Controls Row -->
      <div class="flex gap-4 items-end mb-4">
        <!-- Strategy Selector -->
        <div class="form-control flex-1">
          <label class="label">
            <span class="label-text font-semibold">Chunking Strategy</span>
          </label>
          <select v-model="selectedStrategy" class="select select-bordered">
            <option v-for="opt in strategyOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <!-- Token-based config -->
        <div
          v-if="selectedStrategy === ChunkingStrategy.TOKEN_BASED || selectedStrategy === ChunkingStrategy.MARKDOWN_WITH_TOKEN_LIMIT"
          class="form-control"
        >
          <label class="label">
            <span class="label-text font-semibold">Chunk Size</span>
          </label>
          <input
            v-model.number="tokenChunkSize"
            type="number"
            class="input input-bordered w-32"
            min="100"
            max="2000"
          >
        </div>

        <div
          v-if="selectedStrategy === ChunkingStrategy.TOKEN_BASED || selectedStrategy === ChunkingStrategy.MARKDOWN_WITH_TOKEN_LIMIT"
          class="form-control"
        >
          <label class="label">
            <span class="label-text font-semibold">Overlap</span>
          </label>
          <input
            v-model.number="tokenChunkOverlap"
            type="number"
            class="input input-bordered w-32"
            min="0"
            max="500"
          >
        </div>

        <!-- Markdown-based config -->
        <div
          v-if="selectedStrategy === ChunkingStrategy.MARKDOWN_STRUCTURE || selectedStrategy === ChunkingStrategy.MARKDOWN_WITH_TOKEN_LIMIT"
          class="form-control"
        >
          <label class="label">
            <span class="label-text font-semibold">Max Heading Level</span>
          </label>
          <input
            v-model.number="maxHeadingLevel"
            type="number"
            class="input input-bordered w-32"
            min="1"
            max="6"
          >
        </div>

        <!-- Propose Button -->
        <button
          class="btn btn-primary"
          :disabled="isProposing"
          @click="proposeChunks"
        >
          <Icon v-if="!isProposing" icon="heroicons:sparkles" />
          <span v-if="isProposing" class="loading loading-spinner loading-sm" />
          {{ isProposing ? 'Proposing...' : 'Propose Chunks' }}
        </button>
      </div>

      <!-- Status Row -->
      <div v-if="chunkStats || embeddingStatus" class="flex gap-4 items-center">
        <!-- Chunk stats -->
        <div v-if="chunkStats" class="stats shadow">
          <div class="stat py-2 px-4">
            <div class="stat-title text-xs">
              Chunks
            </div>
            <div class="stat-value text-lg">
              {{ chunkStats.count }}
            </div>
          </div>
          <div class="stat py-2 px-4">
            <div class="stat-title text-xs">
              Avg Size
            </div>
            <div class="stat-value text-lg">
              {{ chunkStats.avg }}
            </div>
            <div class="stat-desc text-xs">
              {{ chunkStats.min }}-{{ chunkStats.max }} chars
            </div>
          </div>
        </div>

        <!-- Embedding status -->
        <div v-if="embeddingStatus" class="flex gap-2 items-center">
          <div
            v-if="!embeddingStatus.isEmbedded"
            class="alert alert-info py-2 px-4"
          >
            <Icon icon="heroicons:information-circle" />
            <span>Not embedded</span>
          </div>
          <div
            v-else-if="!embeddingStatus.embeddingsCurrent"
            class="alert alert-warning py-2 px-4"
          >
            <Icon icon="heroicons:exclamation-triangle" />
            <span>Embeddings out of date</span>
          </div>
          <div
            v-else
            class="alert alert-success py-2 px-4"
          >
            <Icon icon="heroicons:check-circle" />
            <span>Embeddings current ({{ embeddingStatus.totalChunks }} chunks)</span>
          </div>

          <button
            class="btn btn-accent"
            :disabled="isEmbedding || boundaries.length === 0"
            @click="embedDocument"
          >
            <Icon v-if="!isEmbedding" icon="heroicons:cube" />
            <span v-if="isEmbedding" class="loading loading-spinner loading-sm" />
            {{ isEmbedding ? 'Embedding...' : (embeddingStatus.isEmbedded ? 'Re-embed' : 'Embed Document') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Editor and Chunk List -->
    <div class="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 overflow-hidden">
      <!-- Editor (2/3 width on large screens) -->
      <div class="lg:col-span-2 overflow-hidden">
        <TextEditor
          ref="textEditorRef"
          v-model:default-content="documentContent"
          :boundaries="boundaries"
        />
      </div>

      <!-- Chunk List (1/3 width on large screens) -->
      <div class="overflow-y-auto border border-base-300 rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-4">
          Chunks
        </h3>

        <div v-if="boundaries.length === 0" class="text-center text-base-content/60 py-8">
          <Icon icon="heroicons:inbox" class="text-4xl mb-2" />
          <p>No chunks yet</p>
          <p class="text-sm">
            Select a strategy and propose chunks
          </p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="(boundary, index) in boundaries"
            :key="boundary.chunkId"
            class="card bg-base-200 p-3 hover:bg-base-300 transition-colors cursor-pointer"
            :class="{ 'ring-2 ring-primary': selectedChunkId === boundary.chunkId }"
            @click="handleChunkClick(boundary)"
          >
            <div class="flex justify-between items-start mb-2">
              <div class="font-semibold">
                {{ index + 1 }}. {{ boundary.description || boundary.chunkId }}
              </div>
              <div class="badge badge-sm">
                {{ boundary.charEnd - boundary.charStart }} chars
              </div>
            </div>
            <div class="text-xs text-base-content/60 truncate">
              {{ boundary.preview }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chunk-editor {
  max-height: calc(100vh - 8rem);
}
</style>
