i<script setup lang="ts">
import { ref } from 'vue'

import TextEditor from '../components/TextEditor.vue';

const content = ref('')


</script>

<template>
  <div class="max-w-max mx-auto">
    <!-- mb for spacing underneath heading-->
    <h1 class="text-4xl font-bold mb-8">PDF Upload</h1>
    
    <text-editor v-model="content" />
  </div>
</template>