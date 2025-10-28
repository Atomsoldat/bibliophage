<template>
	<div class="app">
		<!-- Sidebar -->
		<Sidebar />

		<!-- Content -->
		<router-view />
	</div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
</script>

<style lang="scss">
:root {
	--primary: #4ade80;
	--primary-alt: #22c55e;
	--grey: #64748b;
	--dark: #1e293b;
	--dark-alt: #334155;
	--dark-bg: #0f172a;
	--light: #f1f5f9;
	--sidebar-width: 250px;

	// Typography
	font-family: system-ui, -apple-system, 'Segoe UI', 'Fira sans', Roboto, Helvetica, Arial, sans-serif;
	line-height: 1.5;
	font-weight: 400;

	// Font rendering optimizations
	font-synthesis: none;
	text-rendering: optimizeLegibility;
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
}

* {
	margin: 0;
	padding: 0;
	box-sizing: border-box;
}

body {
	background: var(--dark-bg);
	color: var(--light);
	min-width: 320px;
	min-height: 100vh;
}

// Typography
h1, h2, h3, h4, h5, h6 {
	line-height: 1.2;
	font-weight: 600;
	color: var(--light);
}

h1 { font-size: 2.5em; }
h2 { font-size: 2em; }
h3 { font-size: 1.5em; }

// Links
a {
	color: var(--primary);
	text-decoration: none;
	font-weight: 500;
	transition: color 0.2s ease-in-out;

	&:hover {
		color: var(--primary-alt);
	}
}

// Layout
.app {
	display: flex;

	main {
		flex: 1 1 0;
		padding: 2rem;
		min-width: 0; // Allows flex item to shrink below content size

		@media (max-width: 1024px) {
			// Sidebar is absolute, so main takes full width
			margin-left: 0;
			width: 100%;
		}
	}
}

// Cards
.card {
	background-color: var(--dark);
	border: 1px solid var(--dark-alt);
	border-radius: 8px;
	margin-bottom: 1.5rem;
	overflow: hidden;

	.card-header {
		background-color: var(--dark-alt);
		color: var(--light);
		padding: 1rem 1.25rem;
		font-weight: 600;
		border-bottom: 1px solid var(--dark-alt);

		i {
			color: var(--primary);
			margin-right: 0.5rem;
		}
	}

	.card-body {
		padding: 1.5rem 1.25rem;
	}
}

// Forms
.form-label {
	color: var(--light);
	font-weight: 500;
	margin-bottom: 0.5rem;
	display: block;
}

.form-control, .form-select {
	background-color: var(--dark-alt);
	border: 1px solid var(--grey);
	color: var(--light);
	padding: 0.5rem 0.75rem;
	border-radius: 4px;
	width: 100%;
	transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;

	&:focus {
		outline: none;
		border-color: var(--primary);
		box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.1);
	}

	&::placeholder {
		color: var(--grey);
	}
}

.form-text {
	color: var(--grey);
	font-size: 0.875rem;
	margin-top: 0.25rem;
}

// Buttons
button, .btn {
	padding: 0.75rem 1.5rem;
	border-radius: 6px;
	font-weight: 500;
	font-family: inherit;
	transition: all 0.2s ease-in-out;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.5rem;
	cursor: pointer;
	border: none;
	appearance: none;
	outline: none;
	background: none;

	&:focus-visible {
		outline: 2px solid var(--primary);
		outline-offset: 2px;
	}
}

.btn-primary {
	background-color: var(--primary);
	color: var(--dark);

	&:hover:not(:disabled) {
		background-color: var(--primary-alt);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(74, 222, 128, 0.3);
	}

	&:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
}

.btn-lg {
	padding: 1rem 2rem;
	font-size: 1.1rem;
}

// Utilities
.container-fluid {
	width: 100%;
	padding-right: 15px;
	padding-left: 15px;
	margin-right: auto;
	margin-left: auto;
}

.mb-3 { margin-bottom: 1rem; }
.me-2 { margin-right: 0.5rem; }

.spinner-border {
	display: inline-block;
	width: 1rem;
	height: 1rem;
	vertical-align: text-bottom;
	border: 0.2em solid currentColor;
	border-right-color: transparent;
	border-radius: 50%;
	animation: spinner-border 0.75s linear infinite;

	&.spinner-border-sm {
		width: 0.875rem;
		height: 0.875rem;
		border-width: 0.15em;
	}
}

@keyframes spinner-border {
	to { transform: rotate(360deg); }
}
</style>