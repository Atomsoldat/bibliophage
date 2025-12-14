<script setup lang="ts">
// import stuff from our  component library
import Sidebar from './components/Sidebar.vue'
import GlobalConsole from './components/GlobalConsole.vue'
</script>

<template>
	<div class="min-h-screen">
		<Sidebar />
		<main class="ml-16 p-8">
			<router-view />
		</main>
		<!-- Global console - available everywhere -->
		<GlobalConsole />
	</div>
</template>

