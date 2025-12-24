<script setup lang="ts">

import { useDraggable } from '@vueuse/core'
import { useTemplateRef, ref } from 'vue'


import TextEditorCard from '../components/TextEditorCard.vue'


const floatingEditorWindow = useTemplateRef('floatingEditorWindow')

// `style` will be a helper computed for `left: ?px; top: ?px;`
// https://vueuse.org/core/useDraggable/
const { x, y, style } = useDraggable(floatingEditorWindow, {
  initialValue: { x: 400, y: 400 },
})

const editorContent = ref("lolEditorContent")
const documentName = ref("lolDocumentName")
const documentIsNew = ref(true)
const documentId = ref("123456")
const isOpen = ref(true)

</script>

<template>
    <div ref="floatingEditorWindow" :style="style" style="position: fixed" class="min-w-lg">
      <!-- Menu Bar -->
      <div class="flex items-center justify-between gap-4 p-2 bg-base-200 border border-base-300 rounded-t-lg">
        <!-- Document Title (Left) -->
        <div class="flex-1 font-semibold truncate">
          <!-- If we ever need to access the coordinates -->
          <!-- I am at {{ x }}, {{ y }} -->
          {{ documentName }}
        </div>

        <!-- Buttons (Right) -->
        <div class="flex gap-2 flex-shrink-0">
          <!--TODO: should the minimise / open be a toggle button instead? -->
          <!--<button class="btn btn-sm">Minimise</button>-->
          <button class="btn btn-sm" @click="isOpen = true">Open</button>
          <!--<button class="btn btn-sm">Maximise</button>-->
          <button class="btn btn-sm" @click="isOpen = false">Close</button>
        </div>
      </div>

      <!-- Editor Dialog -->
      <dialog v-if="isOpen" open class="w-full">
        <TextEditorCard
          ref="editorCardRef"
          v-model:content="editorContent"
          v-model:title="documentName"
          v-model:isNew= "documentIsNew"
          v-model:documentId="documentId"
          icon="heroicons:document-text"
        />
      </dialog>
    </div>
</template>
