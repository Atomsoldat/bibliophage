<script setup lang="ts">

import { useDraggable } from '@vueuse/core'
import { useTemplateRef, ref } from 'vue'


import TextEditorCard from '../components/TextEditorCard.vue'


const el = useTemplateRef('el')

// `style` will be a helper computed for `left: ?px; top: ?px;`
const { x, y, style } = useDraggable(el, {
  initialValue: { x: 400, y: 400 },
})

const editorContent = ref<"lol">
const documentName = ref<"lol">

</script>

<template>
    <div ref="el" :style="style" style="position: fixed">
      <!-- If we ever need to access the coordinates -->
      <!--Drag me! I am at {{ x }}, {{ y }}   -->
      Drag me! I am at {{ x }}, {{ y }}   
      <!--TODO: should the minimise / open be a toggle button instead? -->
      <button class="btn">Minimise</button>
      <button class="btn">Open</button>
      <button class="btn">Maximise</button>
      <button class="btn" onclick="this.dialog.close()">Close</button>
      <dialog draggable open closedby="closerequest">
        <TextEditorCard
          ref="editorCardRef"
          v-model:content="editorContent"
          v-model:title="documentName"
          icon="heroicons:document-text"
        />

      </dialog>



    </div>
</template>
