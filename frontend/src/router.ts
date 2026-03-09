import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('./views/POS.vue'),
    name: 'POS',
    meta: { requiresShift: true },
  },
  {
    path: '/open',
    component: () => import('./views/OpenShift.vue'),
    name: 'OpenShift',
  },
  {
    path: '/close',
    component: () => import('./views/CloseShift.vue'),
    name: 'CloseShift',
    meta: { requiresShift: true },
  },
  {
    path: '/orders',
    component: () => import('./views/Orders.vue'),
    name: 'Orders',
    meta: { requiresShift: true },
  },
  {
    path: '/display',
    component: () => import('./views/CustomerPoleDisplay.vue'),
    name: 'PoleDisplay',
  },
  {
    path: '/customers',
    component: () => import('./views/CustomerDisplay.vue'),
    name: 'Customers',
  },
  {
    path: '/customers/:id',
    component: () => import('./views/CustomerDisplay.vue'),
    name: 'CustomerDetail',
  },
  {
    path: '/kiosk',
    component: () => import('./views/SelfCheckout.vue'),
    name: 'SelfCheckout',
  },
]

export function createAppRouter(isDeskMode: boolean) {
  // Desk mode: memory history — URL stays as /app/pos-terminal, routing is in-memory
  // Standalone mode: history routing with /pos-prime base
  const router = createRouter({
    history: isDeskMode ? createMemoryHistory() : createWebHistory('/pos-prime'),
    routes,
  })

  router.beforeEach(async (to) => {
    if (to.meta.requiresShift) {
      const { usePosSessionStore } = await import('./stores/posSession')
      const { useSettingsStore } = await import('./stores/settings')
      const sessionStore = usePosSessionStore()
      if (!sessionStore.hasOpenShift && !sessionStore.loading) {
        try {
          await sessionStore.checkOpeningEntry()
        } catch {
          // ignore
        }
        if (!sessionStore.hasOpenShift) {
          return { name: 'OpenShift' }
        }
      }
      // Ensure POS Profile (and currency) is loaded for all shift-required pages
      const settingsStore = useSettingsStore()
      if (!settingsStore.posProfile && sessionStore.posProfile) {
        try {
          await settingsStore.loadPOSProfile(sessionStore.posProfile)
        } catch {
          // ignore — POS view will retry
        }
      }
    }
  })

  return router
}