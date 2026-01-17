<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, ref, watch } from 'vue'

import { DocumentType } from '../bibliophage/v1alpha3/document_pb.ts'

const props = defineProps<Props>()

/**
 * All document types with their human-readable labels
 */
const allDocumentTypes = [
  { value: DocumentType.DOCUMENT_TYPE_UNSPECIFIED, label: 'Unspecified' },
  { value: DocumentType.NOTE, label: 'Note' },
  { value: DocumentType.LORE_FRAGMENT, label: 'Lore Fragment' },
  { value: DocumentType.CHARACTER, label: 'Character' },
  { value: DocumentType.LOCATION, label: 'Location' },
  { value: DocumentType.OBJECT, label: 'Object' },
  { value: DocumentType.QUEST, label: 'Quest' },
  { value: DocumentType.SESSION_LOG, label: 'Session Log' },
  { value: DocumentType.RULEBOOK, label: 'Rulebook' },
  { value: DocumentType.EXPANSION, label: 'Expansion' },
  { value: DocumentType.ADVENTURE, label: 'Adventure' },
  { value: DocumentType.BESTIARY, label: 'Bestiary' },
] as const

interface Props {
  /**
   * Optional: restrict which document types are shown in the filter.
   * If not provided, all types are shown.
   */
  allowedTypes?: DocumentType[]
}

/**
 * v-model binding for the enabled document types.
 * Parent receives an array of DocumentType values that are enabled.
 */
const modelValue = defineModel<DocumentType[]>({ required: true })

/**
 * Available document types based on allowedTypes prop
 */
const availableTypes = computed(() => {
  if (!props.allowedTypes || props.allowedTypes.length === 0) {
    return allDocumentTypes
  }
  return allDocumentTypes.filter(t => props.allowedTypes!.includes(t.value))
})

/**
 * Internal state: tracks which types are enabled (as a Set for O(1) lookups)
 */
const enabledTypesSet = ref<Set<DocumentType>>(new Set(modelValue.value))

// Sync internal state when model value changes externally
watch(modelValue, (newValue) => {
  enabledTypesSet.value = new Set(newValue)
}, { deep: true })

// Sync model value when internal state changes
watch(enabledTypesSet, (newSet) => {
  modelValue.value = Array.from(newSet)
}, { deep: true })

/**
 * Track dropdown state
 */
const isOpen = ref(false)

/**
 * Toggle dropdown visibility
 */
function toggleDropdown() {
  isOpen.value = !isOpen.value
}

/**
 * Check if a type is enabled
 */
function isTypeEnabled(type: DocumentType): boolean {
  return enabledTypesSet.value.has(type)
}

/**
 * Toggle a single type on/off
 */
function toggleType(type: DocumentType) {
  if (enabledTypesSet.value.has(type)) {
    enabledTypesSet.value.delete(type)
  }
  else {
    enabledTypesSet.value.add(type)
  }
  // Trigger reactivity
  enabledTypesSet.value = new Set(enabledTypesSet.value)
}

/**
 * Count of enabled types
 */
const enabledCount = computed(() => enabledTypesSet.value.size)

/**
 * Toggle all types on/off
 */
function toggleAll() {
  const allEnabled = availableTypes.value.every(t => enabledTypesSet.value.has(t.value))
  if (allEnabled) {
    enabledTypesSet.value.clear()
  }
  else {
    enabledTypesSet.value = new Set(availableTypes.value.map(t => t.value))
  }
}

/**
 * Convert DocumentType enum value to human-readable label
 */
function formatDocumentType(type: DocumentType): string {
  const typeEntry = allDocumentTypes.find(t => t.value === type)
  return typeEntry?.label || 'Unknown'
}

// Expose formatDocumentType for external use (e.g., table columns)
defineExpose({
  formatDocumentType,
})
</script>

<template>
  <div class="card bg-base-200 shadow-xl p-6">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-4">
        <h3 class="font-semibold text-lg">
          Document Type Filter
        </h3>
        <span class="badge badge-primary">
          {{ enabledCount }} / {{ availableTypes.length }} types shown
        </span>
      </div>
      <div class="relative">
        <button
          type="button"
          class="btn btn-sm btn-primary gap-2"
          @click="toggleDropdown"
        >
          <Icon icon="heroicons:funnel" />
          {{ isOpen ? 'Hide' : 'Show' }} Filters
        </button>
      </div>
    </div>

    <!-- Type filter checkboxes (collapsible) -->
    <div v-if="isOpen" class="mt-4 pt-4 border-t border-base-300">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <label
          v-for="docType in availableTypes"
          v-bind:key="docType.value"
          class="label cursor-pointer justify-start gap-2 hover:bg-base-300 rounded-lg px-2"
        >
          <input
            type="checkbox"
            class="checkbox checkbox-sm checkbox-primary"
            v-bind:checked="isTypeEnabled(docType.value)"
            @change="toggleType(docType.value)"
          >
          <span class="label-text">{{ docType.label }}</span>
        </label>
      </div>
      <div class="mt-4 flex justify-end">
        <button
          type="button"
          class="btn btn-ghost btn-xs"
          @click="toggleAll"
        >
          Toggle All
        </button>
      </div>
    </div>
  </div>
</template>
