<script setup lang="ts">
/**
 * Reusable form select component with label and dropdown
 */
defineProps<{
  label: string
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="form-control">
    <label class="label">
      <span class="label-text font-semibold">{{ label }}</span>
    </label>
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      class="select select-bordered"
    >
      <slot />
    </select>
  </div>
</template>
