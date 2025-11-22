<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'


const editor = useEditor({
  // walliþ nu, gaþankōz"
  // double consontant represented by single laguz
  content: "<p>ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ</p>",
  // the StarterKit extension loads all included extensions at once
  // https://tiptap.dev/docs/editor/extensions/functionality/starterkit#using-the-starterkit-extension
  extensions: [StarterKit],
})

</script>

<template>
<div class="max-w-max mx-auto">
  <h1 class="text-4xl font-bold mb-8">Journal</h1>
   <editor-content :editor="editor" />
</div>
</template>