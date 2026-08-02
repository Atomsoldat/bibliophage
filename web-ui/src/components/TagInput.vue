<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, ref } from 'vue'
import { Tag, TagValue } from '../bibliophage/v1alpha3/tag_pb'
import { useDocumentApi } from '../composables/useDocumentApi'
import { useLogger } from '../composables/useLogger'
import { useTagStore } from '../stores/tags'
import TagManagerOverlay from './TagManagerOverlay.vue'

const props = defineProps<{
  /** "assign" mutates documentId's tags directly, per chip. "collect" only tracks local state for the parent to submit later. */
  mode: 'assign' | 'collect'
  documentId?: string
  modelValue: Tag[]
}>()

const emit = defineEmits<{
  'update:modelValue': [tags: Tag[]]
}>()

const tagStore = useTagStore()
const documentApi = useDocumentApi()
const logger = useLogger()

tagStore.ensureLoaded()

const keyInput = ref('')
const keyDropdownOpen = ref(false)
const lockedTag = ref<Tag | null>(null)
const valueInput = ref('')
const valueDropdownOpen = ref(false)

const managerOpen = ref(false)
const managerPrefillName = ref<string | undefined>(undefined)

interface Chip {
  tagId: string
  tagName: string
  value: string
}

const chips = computed<Chip[]>(() =>
  props.modelValue.flatMap(tag =>
    tag.values.map(v => ({ tagId: tag.id, tagName: tag.name, value: v.value })),
  ),
)

const keyMatches = computed(() => tagStore.matchingTags(keyInput.value))
const valueMatches = computed(() =>
  lockedTag.value ? tagStore.matchingValues(lockedTag.value.name, valueInput.value) : [],
)

function lockTag(tag: Tag) {
  lockedTag.value = tag
  keyInput.value = ''
  keyDropdownOpen.value = false
  valueDropdownOpen.value = true
}

function unlockTag() {
  lockedTag.value = null
  valueInput.value = ''
  valueDropdownOpen.value = false
}

function openManager(prefillName?: string) {
  managerPrefillName.value = prefillName
  managerOpen.value = true
  keyDropdownOpen.value = false
}

function closeManager() {
  managerOpen.value = false
  managerPrefillName.value = undefined
}

function updateModel(next: Chip[]) {
  const tags: Tag[] = []
  const byTagId = new Map<string, Tag>()
  for (const chip of next) {
    let tag = byTagId.get(chip.tagId)
    if (!tag) {
      tag = new Tag({ id: chip.tagId, name: chip.tagName, values: [] })
      byTagId.set(chip.tagId, tag)
      tags.push(tag)
    }
    tag.values.push(new TagValue({ value: chip.value }))
  }
  emit('update:modelValue', tags)
}

async function commitValue(value: string) {
  const tag = lockedTag.value
  const trimmed = value.trim()
  if (!tag || !trimmed) {
    return
  }
  if (chips.value.some(c => c.tagId === tag.id && c.value === trimmed)) {
    valueInput.value = ''
    return
  }

  updateModel([...chips.value, { tagId: tag.id, tagName: tag.name, value: trimmed }])
  valueInput.value = ''

  if (props.mode === 'assign' && props.documentId) {
    try {
      const response = await documentApi.assignTagValue([props.documentId], tag.id, [trimmed])
      if (!response.success) {
        logger.error(`Failed to assign tag value: ${response.message}`)
      }
    }
    catch (error) {
      logger.error(`Failed to assign tag value: ${(error as Error).message}`)
    }
  }
}

async function removeChip(chip: Chip) {
  updateModel(chips.value.filter(c => !(c.tagId === chip.tagId && c.value === chip.value)))

  if (props.mode === 'assign' && props.documentId) {
    try {
      const response = await documentApi.removeTagValue([props.documentId], chip.tagId, [chip.value])
      if (!response.success) {
        logger.error(`Failed to remove tag value: ${response.message}`)
      }
    }
    catch (error) {
      logger.error(`Failed to remove tag value: ${(error as Error).message}`)
    }
  }
}
</script>

<template>
  <div class="tag-input flex flex-col gap-2">
    <div class="flex flex-wrap gap-1">
      <span
        v-for="chip in chips"
        v-bind:key="`${chip.tagId}-${chip.value}`"
        class="badge gap-1"
      >
        {{ chip.tagName }}: {{ chip.value }}
        <button
          type="button"
          v-bind:data-testid="`remove-chip-${chip.tagId}-${chip.value}`"
          class="btn btn-ghost btn-xs btn-circle"
          @click="removeChip(chip)"
        >
          <Icon icon="heroicons:x-mark" class="text-xs" />
        </button>
      </span>
    </div>

    <div class="flex items-center gap-2 relative">
      <template v-if="!lockedTag">
        <input
          v-model="keyInput"
          data-testid="tag-key-input"
          type="text"
          placeholder="Tag name..."
          class="input input-bordered input-sm"
          @focus="keyDropdownOpen = true"
          @blur="keyDropdownOpen = false"
        >
        <ul
          v-if="keyDropdownOpen"
          class="dropdown-menu absolute top-full left-0 mt-1 z-10 menu bg-base-200 rounded-box shadow-lg w-56"
        >
          <li v-for="tag in keyMatches" v-bind:key="tag.id">
            <a v-bind:data-testid="`tag-key-option-${tag.id}`" @mousedown.prevent="lockTag(tag)">{{ tag.name }}</a>
          </li>
          <li v-if="keyInput.trim() && keyMatches.length === 0">
            <a data-testid="no-tag-match" @mousedown.prevent="openManager(keyInput.trim())">
              no tag called "{{ keyInput.trim() }}" — manage tags
            </a>
          </li>
        </ul>
      </template>

      <template v-else>
        <span class="badge badge-outline gap-1">
          {{ lockedTag.name }}
          <button type="button" class="btn btn-ghost btn-xs btn-circle" @click="unlockTag">
            <Icon icon="heroicons:x-mark" class="text-xs" />
          </button>
        </span>
        <input
          v-model="valueInput"
          data-testid="tag-value-input"
          type="text"
          placeholder="Value..."
          class="input input-bordered input-sm"
          @focus="valueDropdownOpen = true"
          @keydown.enter.prevent="commitValue(valueInput)"
        >
        <ul
          v-if="valueDropdownOpen"
          class="dropdown-menu absolute top-full left-0 mt-1 z-10 menu bg-base-200 rounded-box shadow-lg w-56"
        >
          <li v-for="value in valueMatches" v-bind:key="value.id || value.value">
            <a @mousedown.prevent="commitValue(value.value)">{{ value.value }}</a>
          </li>
          <li v-if="valueInput.trim() && !valueMatches.some(v => v.value === valueInput.trim())">
            <a @mousedown.prevent="commitValue(valueInput)">add "{{ valueInput.trim() }}"</a>
          </li>
        </ul>
      </template>

      <button type="button" class="btn btn-ghost btn-xs" @click="openManager()">
        manage tags
      </button>
    </div>

    <TagManagerOverlay
      v-bind:show="managerOpen"
      v-bind:prefill-name="managerPrefillName"
      @close="closeManager"
    />
  </div>
</template>
