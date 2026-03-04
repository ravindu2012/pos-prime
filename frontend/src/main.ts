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

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)

app.mount('#app')
