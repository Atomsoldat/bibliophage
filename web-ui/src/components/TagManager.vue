<script setup lang="ts">
import type { Tag, TagValue } from '../bibliophage/v1alpha3/tag_pb'
import { Icon } from '@iconify/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useLogger } from '../composables/useLogger'
import { useTagStore } from '../stores/tags'

const props = defineProps<{
  /** Pre-fill the create-tag form, e.g. when opened from TagInput's "no tag called '…'" affordance */
  prefillName?: string
}>()

const tagStore = useTagStore()
const logger = useLogger()

const searchQuery = ref('')
const selectedTagId = ref<string | null>(null)

const newTagName = ref(props.prefillName ?? '')
const newTagColour = ref('')
const creatingTag = ref(false)

const renameTagInput = ref('')
const renamingTag = ref(false)
const colourInput = ref('')
const confirmingTagDelete = ref(false)
const deletingTag = ref(false)

const newValueInput = ref('')
const creatingValue = ref(false)
const renameValueInputs = ref<Record<string, string>>({})
const renamingValueId = ref<string | null>(null)
const confirmingValueDeleteId = ref<string | null>(null)
const deletingValueId = ref<string | null>(null)

onMounted(() => {
  tagStore.reload()
})

watch(() => props.prefillName, (name) => {
  if (name) {
    newTagName.value = name
  }
})

const visibleTags = computed<Tag[]>(() => tagStore.matchingTags(searchQuery.value))

const selectedTag = computed<Tag | undefined>(() =>
  tagStore.tags.find(t => t.id === selectedTagId.value),
)

watch(selectedTag, (tag) => {
  renameTagInput.value = tag?.name ?? ''
  colourInput.value = tag?.colour ?? ''
  confirmingTagDelete.value = false
  renameValueInputs.value = {}
  for (const value of tag?.values ?? []) {
    renameValueInputs.value[value.id] = value.value
  }
})

function selectTag(tag: Tag) {
  selectedTagId.value = selectedTagId.value === tag.id ? null : tag.id
}

async function handleCreateTag() {
  const name = newTagName.value.trim()
  if (!name) {
    return
  }
  creatingTag.value = true
  try {
    const response = await tagStore.createTag(name, newTagColour.value.trim() || undefined)
    if (response.success) {
      logger.success(`Tag "${name}" created`)
      newTagName.value = ''
      newTagColour.value = ''
    }
    else {
      logger.error(`Failed to create tag: ${response.message}`)
    }
  }
  finally {
    creatingTag.value = false
  }
}

async function handleRenameTag() {
  const tag = selectedTag.value
  const name = renameTagInput.value.trim()
  if (!tag || !name || name === tag.name) {
    return
  }
  renamingTag.value = true
  try {
    const response = await tagStore.renameTag(tag.id, name)
    if (!response.success) {
      logger.error(`Failed to rename tag: ${response.message}`)
    }
  }
  finally {
    renamingTag.value = false
  }
}

async function handleUpdateColour() {
  const tag = selectedTag.value
  if (!tag) {
    return
  }
  const response = await tagStore.updateTagColour(tag.id, colourInput.value)
  if (!response.success) {
    logger.error(`Failed to update tag colour: ${response.message}`)
  }
}

async function handleDeleteTag() {
  const tag = selectedTag.value
  if (!tag) {
    return
  }
  deletingTag.value = true
  try {
    const response = await tagStore.deleteTag(tag.id)
    if (response.success) {
      logger.success(`Tag "${tag.name}" deleted`)
      selectedTagId.value = null
    }
    else {
      logger.error(`Failed to delete tag: ${response.message}`)
    }
  }
  finally {
    deletingTag.value = false
    confirmingTagDelete.value = false
  }
}

async function handleCreateValue() {
  const tag = selectedTag.value
  const value = newValueInput.value.trim()
  if (!tag || !value) {
    return
  }
  creatingValue.value = true
  try {
    const response = await tagStore.createTagValue(tag.id, value)
    if (response.success) {
      newValueInput.value = ''
    }
    else {
      logger.error(`Failed to create tag value: ${response.message}`)
    }
  }
  finally {
    creatingValue.value = false
  }
}

async function handleRenameValue(value: TagValue) {
  const newValue = (renameValueInputs.value[value.id] ?? '').trim()
  if (!newValue || newValue === value.value) {
    return
  }
  renamingValueId.value = value.id
  try {
    const response = await tagStore.renameTagValue(value.id, newValue)
    if (!response.success) {
      logger.error(`Failed to rename tag value: ${response.message}`)
    }
  }
  finally {
    renamingValueId.value = null
  }
}

async function handleDeleteValue(value: TagValue) {
  deletingValueId.value = value.id
  try {
    const response = await tagStore.deleteTagValue(value.id)
    if (!response.success) {
      logger.error(`Failed to delete tag value: ${response.message}`)
    }
  }
  finally {
    deletingValueId.value = null
    confirmingValueDeleteId.value = null
  }
}
</script>

<template>
  <div class="flex gap-4 h-full">
    <!-- Tag list -->
    <div class="w-72 flex-shrink-0 flex flex-col gap-3">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search tags..."
        class="input input-bordered input-sm w-full"
      >

      <ul class="menu bg-base-200 rounded-box p-0 flex-1 overflow-y-auto flex-nowrap">
        <li v-for="tag in visibleTags" v-bind:key="tag.id">
          <a
            v-bind:data-testid="`tag-list-item-${tag.id}`"
            v-bind:class="{ active: tag.id === selectedTagId }"
            @click="selectTag(tag)"
          >
            <span
              v-if="tag.colour"
              class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
              v-bind:style="{ backgroundColor: tag.colour }"
            />
            <span class="flex-1 truncate">{{ tag.name }}</span>
            <span class="badge badge-sm badge-ghost">{{ tag.documentCount ?? 0 }}</span>
          </a>
        </li>
        <li v-if="visibleTags.length === 0" class="p-2 text-sm text-base-content/60">
          No tags found
        </li>
      </ul>

      <form data-testid="create-tag-form" class="flex flex-col gap-2 border-t border-base-300 pt-3" @submit.prevent="handleCreateTag">
        <div class="flex gap-2">
          <input
            v-model="newTagName"
            type="text"
            placeholder="New tag name"
            class="input input-bordered input-sm flex-1"
          >
          <input
            v-model="newTagColour"
            type="color"
            class="w-10 h-9 p-0 border-0 bg-transparent"
            title="Tag colour (optional)"
          >
        </div>
        <button type="submit" class="btn btn-sm btn-primary gap-1" v-bind:disabled="!newTagName.trim() || creatingTag">
          <Icon icon="heroicons:plus" />
          Create Tag
        </button>
      </form>
    </div>

    <!-- Selected tag detail -->
    <div v-if="selectedTag" class="flex-1 flex flex-col gap-4 overflow-y-auto">
      <div class="flex flex-col gap-2">
        <form data-testid="rename-tag-form" class="flex gap-2 items-center" @submit.prevent="handleRenameTag">
          <input
            v-model="renameTagInput"
            data-testid="rename-tag-input"
            type="text"
            class="input input-bordered input-sm flex-1"
          >
          <input
            v-model="colourInput"
            type="color"
            class="w-9 h-9 p-0 border-0 bg-transparent"
            title="Tag colour"
            @change="handleUpdateColour"
          >
          <button type="submit" class="btn btn-sm" v-bind:disabled="renamingTag">
            Rename
          </button>
        </form>

        <div class="text-sm text-base-content/60">
          {{ selectedTag.documentCount ?? 0 }} document{{ (selectedTag.documentCount ?? 0) === 1 ? '' : 's' }},
          {{ selectedTag.valueCount ?? selectedTag.values.length }} value{{ (selectedTag.valueCount ?? selectedTag.values.length) === 1 ? '' : 's' }}
        </div>

        <div v-if="!confirmingTagDelete">
          <button type="button" data-testid="delete-tag-button" class="btn btn-sm btn-error btn-outline gap-1" @click="confirmingTagDelete = true">
            <Icon icon="heroicons:trash" />
            Delete Tag
          </button>
        </div>
        <div v-else class="alert alert-warning flex items-center justify-between">
          <span>Delete "{{ selectedTag.name }}"? This affects {{ selectedTag.documentCount ?? 0 }} document{{ (selectedTag.documentCount ?? 0) === 1 ? '' : 's' }} and deletes {{ selectedTag.valueCount ?? selectedTag.values.length }} value{{ (selectedTag.valueCount ?? selectedTag.values.length) === 1 ? '' : 's' }}.</span>
          <div class="flex gap-2">
            <button type="button" class="btn btn-sm" v-bind:disabled="deletingTag" @click="confirmingTagDelete = false">
              Cancel
            </button>
            <button type="button" data-testid="confirm-delete-tag-button" class="btn btn-sm btn-error" v-bind:disabled="deletingTag" @click="handleDeleteTag">
              Confirm Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Values -->
      <div class="flex flex-col gap-2">
        <h3 class="font-semibold text-sm text-base-content/70">
          Values
        </h3>

        <div v-for="value in selectedTag.values" v-bind:key="value.id" class="flex items-center gap-2">
          <form v-bind:data-testid="`rename-value-form-${value.value}`" class="flex-1 flex gap-2" @submit.prevent="handleRenameValue(value)">
            <input
              v-model="renameValueInputs[value.id]"
              v-bind:data-testid="`rename-value-input-${value.value}`"
              type="text"
              class="input input-bordered input-xs flex-1"
            >
            <button type="submit" class="btn btn-xs" v-bind:disabled="renamingValueId === value.id">
              Rename
            </button>
          </form>
          <span class="badge badge-sm badge-ghost">{{ value.documentCount ?? 0 }}</span>

          <template v-if="confirmingValueDeleteId === value.id">
            <span class="text-xs text-base-content/60">{{ value.documentCount ?? 0 }} doc{{ (value.documentCount ?? 0) === 1 ? '' : 's' }}?</span>
            <button type="button" class="btn btn-xs" @click="confirmingValueDeleteId = null">
              Cancel
            </button>
            <button
              type="button"
              v-bind:data-testid="`confirm-delete-value-button-${value.value}`"
              class="btn btn-xs btn-error"
              v-bind:disabled="deletingValueId === value.id"
              @click="handleDeleteValue(value)"
            >
              Confirm
            </button>
          </template>
          <button
            v-else
            type="button"
            v-bind:data-testid="`delete-value-button-${value.value}`"
            class="btn btn-xs btn-ghost text-error"
            @click="confirmingValueDeleteId = value.id"
          >
            <Icon icon="heroicons:trash" />
          </button>
        </div>

        <form data-testid="create-value-form" class="flex gap-2 mt-2" @submit.prevent="handleCreateValue">
          <input
            v-model="newValueInput"
            type="text"
            placeholder="New value"
            class="input input-bordered input-xs flex-1"
          >
          <button type="submit" class="btn btn-xs btn-primary" v-bind:disabled="!newValueInput.trim() || creatingValue">
            Add Value
          </button>
        </form>
      </div>
    </div>

    <div v-else class="flex-1 flex items-center justify-center text-base-content/50 text-sm">
      Select a tag to manage its values
    </div>
  </div>
</template>
