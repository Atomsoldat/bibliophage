import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// separate from vite.config.ts so tests don't pull in vite-plugin-vue-devtools,
// which opens a dev-only websocket connection
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  test: {
    environment: 'jsdom',
  },
})
