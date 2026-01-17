<script setup lang="ts">
import GlobalConsole from './components/GlobalConsole.vue'
import GlobalEditorWindows from './components/GlobalEditorWindows.vue'
import Sidebar from './components/Sidebar.vue'
import { useAppConsole } from './composables/useAppConsole'

const { isVisible } = useAppConsole()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <Sidebar />
    <!-- Main content area that adjusts height based on console visibility -->
    <main
      class="ml-16 p-8 overflow-auto transition-all duration-300"
      v-bind:style="{ height: isVisible ? '50vh' : '100vh' }"
    >
      <router-view />
    </main>
    <GlobalConsole />
    <GlobalEditorWindows />
  </div>
</template>
