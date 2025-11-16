import { createApp } from 'vue'

// user our styling
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

// instantiate App.vue
const app = createApp(App)

//install the Vue router so we can move between views using the sidebar
// we imported ./router above
app.use(router)

// mount our instantiated App to the <div id="app"></div> element in index.html
app.mount('#app')
