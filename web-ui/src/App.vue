<template>
	<div class="min-h-screen">
		<Sidebar />
		<main class="ml-16 p-8">
			<router-view />
		</main>
	</div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
</script>
