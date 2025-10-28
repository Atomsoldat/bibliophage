import { createApp } from 'vue'
import './style.css'
import router from './router'
import App from './App.vue'

// Initialize dark mode from localStorage
const savedDarkMode = localStorage.getItem('darkMode')
if (savedDarkMode !== 'false') {
  document.documentElement.setAttribute('data-theme', 'dark')
} else {
  document.documentElement.setAttribute('data-theme', 'light')
}

const app = createApp(App)

app.use(router)
app.mount('#app')
