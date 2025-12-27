<script setup lang="ts">
import GlobalConsole from './components/GlobalConsole.vue'
import GlobalEditorWindows from './components/GlobalEditorWindows.vue'
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <div class="min-h-screen">
    <Sidebar />
    <main class="ml-16 p-8">
      <router-view />
    </main>
    <GlobalConsole />
    <GlobalEditorWindows />
  </div>
</template>
