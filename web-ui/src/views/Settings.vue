<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-4xl font-bold mb-8">Settings</h1>

    <div class="card bg-base-200 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">
          <Icon icon="heroicons:paint-brush" class="text-xl" />
          Appearance
        </h2>

        <div class="flex justify-between items-center py-4">
          <div>
            <label for="darkModeToggle" class="font-semibold">Dark Mode</label>
            <p class="text-sm opacity-70">Enable dark color scheme</p>
          </div>
          <input
            type="checkbox"
            id="darkModeToggle"
            class="toggle toggle-primary"
            v-model="darkMode"
            @change="toggleDarkMode"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'

const darkMode = ref(true)

onMounted(() => {
  const savedMode = localStorage.getItem('darkMode')
  darkMode.value = savedMode !== 'false'
  applyDarkMode()
})

function toggleDarkMode() {
  localStorage.setItem('darkMode', darkMode.value.toString())
  applyDarkMode()
}

function applyDarkMode() {
  if (darkMode.value) {
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    document.documentElement.setAttribute('data-theme', 'light')
  }
}
</script>
