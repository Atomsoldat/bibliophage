import { defineConfig } from 'vite'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from "@tailwindcss/vite";

// this plugin tells typescript to treat any imported .vue files as DefineComponent
// (Typescript wants types for everything, hence the name)
// only works for vite itself, hence the additional shims-vue.d.ts declaration file for everything else
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools({
      launchEditor: 'codium'
    }),
    tailwindcss(),
  ],
})
