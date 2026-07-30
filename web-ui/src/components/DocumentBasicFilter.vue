<script setup lang="ts">

/**
 * Filter values exposed via v-model
 */
export interface DocumentBasicFilterValue {
  nameQuery: string,
}

/**
 * v-model binding for the filter values
 */
const modelValue = defineModel<DocumentBasicFilterValue>({ required: true })



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

    </div>
  </div>
</template>
