<script setup lang="ts">
/**
 * Reusable form field component with label and input
 * Supports text and number input types with validation attributes
 */
defineProps<{
  label: string
  modelValue: string | number
  type?: 'text' | 'number'
  placeholder?: string
  min?: number
  max?: number
}>()

defineEmits<{
  'update:modelValue': [value: string | number]
}>()
</script>

<template>
  <div class="form-control">
    <label class="label">
      <span class="label-text font-semibold">{{ label }}</span>
    </label>
    <input
      :value="modelValue"
      @input="$emit('update:modelValue', type === 'number' ? Number(($event.target as HTMLInputElement).value) : ($event.target as HTMLInputElement).value)"
      :type="type || 'text'"
      :placeholder="placeholder"
      :min="min"
      :max="max"
      class="input input-bordered"
    >
  </div>
</template>
