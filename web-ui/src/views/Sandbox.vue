<script setup lang="ts">
import TextEditorWindow from '../components/TextEditorWindow.vue';
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold mb-4">
      Sandbox
    </h1>
    <p class="text-lg">
      Testing ground for experimental features
    </p>
  </div>
  
  <!-- Test out Floating Text editor windows-->
  <div>
    <TextEditorWindow />
  </div>

</template>
