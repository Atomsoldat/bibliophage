import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Home,
    },
    {
      path: '/pdf-upload',
      component: () => import('../views/PdfUpload.vue'),
    },
    {
      path: '/library',
      component: () => import('../views/Library.vue'),
    },
    {
      path: '/chat',
      component: () => import('../views/Chat.vue'),
    },
    {
      path: '/graph',
      component: () => import('../views/GraphView.vue'),
    },
    {
      path: '/chunks',
      component: () => import('../views/Chunks.vue'),
    },
    {
      path: '/graph',
      component: () => import('../views/GraphView.vue'),
    },
    {
      path: '/sandbox',
      component: () => import('../views/Sandbox.vue'),
    },
    {
      path: '/settings',
      component: () => import('../views/Settings.vue'),
    },
  ],
})

export default router
