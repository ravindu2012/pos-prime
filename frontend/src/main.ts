// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

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
import { createAppRouter } from './router'
import { setDeskMode } from './composables/useDeskMode'
import './index.css'

// Detect desk mode: #pos-prime-app = inside Frappe desk page
// Standalone mode: #app exists AND we're on a /pos-prime/* URL
// (Frappe desk also has a #app element, so we must check the URL to avoid conflicts)
const deskMount = document.getElementById('pos-prime-app')
const isStandalonePath = window.location.pathname.startsWith('/pos-prime')
const standaloneMount = isStandalonePath ? document.getElementById('app') : null
const mountTarget = deskMount || standaloneMount

if (mountTarget) {
  const isDeskMode = !!deskMount
  setDeskMode(isDeskMode)

  const pinia = createPinia()
  const app = createApp(App)
  const router = createAppRouter(isDeskMode)

  setConfig('resourceFetcher', frappeRequest)

  // Make __() available in all Vue templates
  app.config.globalProperties.__ = window.__

  app.use(pinia)
  app.use(router)
  app.use(resourcesPlugin)

  app.mount(mountTarget)
}
