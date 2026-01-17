<script setup lang="ts">
import { ref, watch } from 'vue'

/**
 * Filter values exposed via v-model
 */
export interface DocumentBasicFilterValue {
  nameQuery: string
  systemFilters: string[]
}

/**
 * v-model binding for the filter values
 */
const modelValue = defineModel<DocumentBasicFilterValue>({ required: true })

/**
 * Internal state for the raw system filters input (comma-separated string)
 */
const systemFiltersInput = ref('')

// Initialize internal input from model value
if (modelValue.value.systemFilters.length > 0) {
  systemFiltersInput.value = modelValue.value.systemFilters.join(', ')
}

/**
 * Parse comma-separated input into array and update model
 */
watch(systemFiltersInput, (newValue) => {
  if (!newValue.trim()) {
    modelValue.value = {
      ...modelValue.value,
      systemFilters: [],
    }
    return
  }

  // Split by comma, trim whitespace, and filter out empty strings
  const parsed = newValue
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)

  modelValue.value = {
    ...modelValue.value,
    systemFilters: parsed,
  }
})

/**
 * Handle name query changes
 */
function handleNameChange(event: Event) {
  const target = event.target as HTMLInputElement
  modelValue.value = {
    ...modelValue.value,
    nameQuery: target.value,
  }
}
</script>

<template>
  <div class="card bg-base-200 shadow-xl p-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Name Search Input -->
      <div class="form-control">
        <label class="label" for="name-search">
          <span class="label-text">Document Name</span>
        </label>
        <input
          id="name-search"
          type="text"
          placeholder="Search by name..."
          class="input input-bordered w-full"
          v-bind:value="modelValue.nameQuery"
          @input="handleNameChange"
        >
      </div>

      <!-- System Filters Input -->
      <div class="form-control">
        <label class="label" for="system-search">
          <span class="label-text">Systems (comma-separated)</span>
        </label>
        <input
          id="system-search"
          v-model="systemFiltersInput"
          type="text"
          placeholder="e.g., Pathfinder 1e, Call of Cthulhu"
          class="input input-bordered w-full"
        >
      </div>
    </div>
  </div>
</template>
