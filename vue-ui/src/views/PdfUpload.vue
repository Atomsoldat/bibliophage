<script setup lang="ts">
import { ref } from 'vue'

// Form state
const serverAddress = ref('localhost')
const serverPort = ref(50051)
const pdfName = ref('')
const rpgSystem = ref('PATHFINDER_1E')
const publicationType = ref('BESTIARY')
const chunkSize = ref(600)
const chunkOverlap = ref(50)
const pdfFile = ref<File | null>(null)
const loading = ref(false)
const output = ref('')

// File input handler
function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    pdfFile.value = target.files[0]
    // Auto-fill PDF name from filename if empty
    if (!pdfName.value) {
      pdfName.value = target.files[0].name.replace('.pdf', '')
    }
  }
}

// Form submission handler
async function handleSubmit() {
  if (!pdfFile.value) {
    alert('Please select a PDF file')
    return
  }

  loading.value = true
  output.value = `Connecting to server at ${serverAddress.value}:${serverPort.value}...\n`
  output.value += `File: ${pdfFile.value.name}\n`
  output.value += `PDF Name: ${pdfName.value}\n`
  output.value += `System: ${rpgSystem.value}\n`
  output.value += `Type: ${publicationType.value}\n`
  output.value += `\n[Connect-RPC integration pending - server connection will be added next]\n`

  // TODO: Add actual Connect-RPC call here
  setTimeout(() => {
    loading.value = false
    output.value += '\nReady for Connect-RPC integration!'
  }, 1000)
}
</script>

<template>
  <div id="app">

    <!-- Main Content -->
    <main class="container-fluid">
      <form @submit.prevent="handleSubmit">

        <!-- Card Grid Layout -->
        <div class="card-grid">

          <!-- Server Configuration -->
          <div class="card">
            <div class="card-header">
              <i class="bi bi-server"></i> Server Configuration
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">Server Address</label>
                <input v-model="serverAddress" type="text" class="form-control" placeholder="localhost">
              </div>
              <div class="mb-3">
                <label class="form-label">Server Port</label>
                <input v-model.number="serverPort" type="number" class="form-control" placeholder="50051" min="1" max="65535">
              </div>
            </div>
          </div>

          <!-- PDF File -->
          <div class="card">
            <div class="card-header">
              <i class="bi bi-file-earmark-pdf"></i> PDF File
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">PDF File</label>
                <input type="file" class="form-control" accept=".pdf" @change="handleFileChange">
                <div class="form-text">Select a PDF file to upload (max 50MB)</div>
              </div>
              <div class="mb-3">
                <label class="form-label">PDF Name</label>
                <input v-model="pdfName" type="text" class="form-control" placeholder="e.g., Monster Manual, Core Rulebook">
              </div>
            </div>
          </div>

          <!-- Metadata -->
          <div class="card">
            <div class="card-header">
              <i class="bi bi-tags"></i> Metadata
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">RPG System</label>
                <select v-model="rpgSystem" class="form-select">
                  <option value="DND_35">D&D 3.5</option>
                  <option value="PATHFINDER_1E">Pathfinder 1e</option>
                  <option value="PATHFINDER_2E">Pathfinder 2e</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Publication Type</label>
                <select v-model="publicationType" class="form-select">
                  <option value="CORE_RULEBOOK">Core Rulebook</option>
                  <option value="BESTIARY">Bestiary</option>
                  <option value="SUPPLEMENT">Supplement</option>
                  <option value="ADVENTURE">Adventure</option>
                  <option value="SETTING">Setting</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Chunking Parameters -->
          <div class="card">
            <div class="card-header">
              <i class="bi bi-sliders"></i> Chunking Parameters
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">Chunk Size</label>
                <input v-model.number="chunkSize" type="number" class="form-control" min="100" max="2000">
                <div class="form-text">100-2000</div>
              </div>
              <div class="mb-3">
                <label class="form-label">Chunk Overlap</label>
                <input v-model.number="chunkOverlap" type="number" class="form-control" min="0" max="500">
                <div class="form-text">0-500</div>
              </div>
            </div>
          </div>

        </div>

        <!-- Submit Button -->
        <div class="submit-section">
          <button type="submit" class="btn btn-primary btn-lg" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-upload"></i>
            {{ loading ? 'Loading...' : 'Load PDF' }}
          </button>
        </div>

        <!-- Output Area -->
        <div v-if="output" class="card output-card">
          <div class="card-header">
            <i class="bi bi-terminal"></i> Output
          </div>
          <div class="card-body">
            <div class="output-area">{{ output }}</div>
          </div>
        </div>

      </form>
    </main>

  </div>
</template>

<style lang="scss" scoped>
// Card grid layout - automatically responsive without media queries
.card-grid {
  display: grid;
  // Auto-fit: automatically wraps cards when they don't fit
  // minmax(320px, 1fr): cards are at least 320px, grow equally to fill space
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
  // Equal height rows - all cards in a row have same height
  grid-auto-rows: 1fr;

  .card {
    display: flex;
    flex-direction: column;

    .card-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
    }
  }
}

// Submit button section
.submit-section {
  max-width: 600px;
  margin: 0 auto 2rem auto;

  button {
    width: 100%;
  }
}

// Output display area
.output-card {
  max-width: 1200px;
  margin: 0 auto;
}

.output-area {
  background-color: var(--dark-bg);
  color: var(--primary);
  font-family: 'Courier New', monospace;
  padding: 1rem;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  min-height: 100px;
  border: 1px solid var(--dark-alt);
  line-height: 1.5;
}
</style>
