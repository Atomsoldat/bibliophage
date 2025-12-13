<template>
	<div class="fixed left-0 top-0 bottom-0 w-16 bg-base-200 border-r border-base-300 flex flex-col items-center py-4 gap-2 z-50">
		<!-- Navigation icons -->
		<router-link to="/">
			<button class="btn btn-ghost btn-square">
				<Icon icon="heroicons:home" class="text-3xl" />
			</button>
		</router-link>

		<router-link to="/pdf-upload">
			<button class="btn btn-ghost btn-square">
				<Icon icon="heroicons:document" class="text-3xl" />
			</button>
		</router-link>

		<router-link to="/document-list">
			<button class="btn btn-ghost btn-square">
				<Icon icon="game-icons:bookshelf" class="text-3xl" />
			</button>
		</router-link>

		<router-link to="/journal">
			<button class="btn btn-ghost btn-square">
				<!--<Icon icon="heroicons:pencil-square" class="text-3xl" />-->
				<Icon icon="game-icons:scroll-quill" class="text-3xl" />
			</button>
		</router-link>

		<div class="flex-1"></div>

		<!-- Settings at bottom -->
		<router-link to="/settings">
			<button class="btn btn-ghost btn-square">
				<Icon icon="heroicons:cog-6-tooth" class="text-3xl" />
			</button>
		</router-link>
	</div>
</template>

<script setup>
import { Icon } from '@iconify/vue'
</script>
