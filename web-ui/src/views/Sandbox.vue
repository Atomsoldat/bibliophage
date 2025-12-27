<script setup lang="ts">
import { useEditorWindows } from '../composables/useEditorWindows'
import { ref } from 'vue'

const { openWindow, windows, closeAll } = useEditorWindows()

const demoTitle = ref('My Document')
const demoContent = ref('Start typing here...')

function createNewDocument() {
  openWindow({
    title: 'New Document',
    content: '',
    isNew: true,
  })
}

function createDocumentWithData() {
  openWindow({
    title: demoTitle.value,
    content: demoContent.value,
    isNew: false,
    documentId: `demo-${Date.now()}`,
  })
}

function createMultipleWindows() {
  for (let i = 1; i <= 3; i++) {
    openWindow({
      title: `Document ${i}`,
      content: `This is document number ${i}`,
      isNew: true,
    })
  }
}
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">
      Sandbox
    </h1>
    <p class="text-lg mb-6">
      Testing ground for experimental features
    </p>

    <!-- Editor Windows Demo -->
    <div class="card bg-base-200 shadow-xl p-6 mb-6">
      <h2 class="text-2xl font-bold mb-4">
        Global Editor Windows Demo
      </h2>
      <p class="mb-4">
        The editor windows are global - they persist across view changes!
        Try navigating to another view and back.
      </p>

      <div class="stats shadow mb-4">
        <div class="stat">
          <div class="stat-title">
            Active Windows
          </div>
          <div class="stat-value">
            {{ windows.length }}
          </div>
          <div class="stat-desc">
            {{ windows.length === 0 ? 'No windows open' : windows.map(w => w.title).join(', ') }}
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Simple window creation -->
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h3 class="card-title">
              Create New Document
            </h3>
            <p class="text-sm">
              Opens a blank editor window
            </p>
            <button class="btn btn-primary" @click="createNewDocument">
              New Document
            </button>
          </div>
        </div>

        <!-- Custom data -->
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h3 class="card-title">
              Create with Custom Data
            </h3>
            <input
              v-model="demoTitle"
              type="text"
              placeholder="Document title"
              class="input input-bordered input-sm mb-2"
            >
            <textarea
              v-model="demoContent"
              placeholder="Initial content"
              class="textarea textarea-bordered textarea-sm mb-2"
              rows="2"
            />
            <button class="btn btn-secondary" @click="createDocumentWithData">
              Create
            </button>
          </div>
        </div>

        <!-- Multiple windows -->
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h3 class="card-title">
              Create Multiple
            </h3>
            <p class="text-sm">
              Opens 3 windows with cascade positioning
            </p>
            <button class="btn btn-accent" @click="createMultipleWindows">
              Create 3 Windows
            </button>
          </div>
        </div>

        <!-- Close all -->
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h3 class="card-title">
              Close All
            </h3>
            <p class="text-sm">
              Closes all open editor windows
            </p>
            <button
              class="btn btn-error"
              @click="closeAll"
              :disabled="windows.length === 0"
            >
              Close All Windows
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
