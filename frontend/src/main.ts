// globals must be imported FIRST — before any Vue component that uses __()
import './globals'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  FrappeUI,
  setConfig,
  frappeRequest,
  resourcesPlugin,
} from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './index.css'

const pinia = createPinia()
const app = createApp(App)

setConfig('resourceFetcher', frappeRequest)

// Make __() available in all Vue templates
app.config.globalProperties.__ = window.__

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)

app.mount('#app')
