import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{
			path: '/',
			component: Home
		},
		{
			path: '/pdf-upload',
			component: () => import('../views/PdfUpload.vue')
		},
		{
			path: '/journal',
			component: () => import('../views/Journal.vue')
		},
		{
			path: '/settings',
			component: () => import('../views/Settings.vue')
		},
	],
})

export default router