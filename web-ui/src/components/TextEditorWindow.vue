<script setup lang="ts">

import { useDraggable } from '@vueuse/core'
import { useTemplateRef, ref } from 'vue'


import TextEditorCard from '../components/TextEditorCard.vue'


const el = useTemplateRef('el')

// `style` will be a helper computed for `left: ?px; top: ?px;`
const { x, y, style } = useDraggable(el, {
  initialValue: { x: 400, y: 400 },
})

const editorContent = ref("lolEditorContent")
const documentName = ref("lolDocumentName")
const isOpen = ref(true)

</script>

<template>
    <div ref="el" :style="style" style="position: fixed">
      <!-- If we ever need to access the coordinates -->
      <!--Drag me! I am at {{ x }}, {{ y }}   -->
      {{ documentName }}
      <!--TODO: should the minimise / open be a toggle button instead? -->
      <button class="btn">Minimise</button>
      <button class="btn" @click="isOpen = true">Open</button>
      <button class="btn">Maximise</button>
      <button class="btn" @click="isOpen = false">Close</button>
      <dialog v-if="isOpen" draggable open>
        <TextEditorCard
          ref="editorCardRef"
          v-model:content="editorContent"
          v-model:title="documentName"
          icon="heroicons:document-text"
        />
      </dialog>
    </div>
</template>
