<script setup lang="ts">
import { Icon } from '@iconify/vue'

defineProps<{
  title: string
  icon: string
}>()
</script>

<template>
  <div class="card bg-base-200 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">
        <Icon v-bind:icon="icon" class="text-xl" />
        {{ title }}
      </h2>
      <slot />
    </div>
  </div>
</template>
