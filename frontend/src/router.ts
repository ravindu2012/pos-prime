import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/posify',
    component: () => import('./views/POS.vue'),
    name: 'POS',
    meta: { requiresShift: true },
  },
  {
    path: '/posify/open',
    component: () => import('./views/OpenShift.vue'),
    name: 'OpenShift',
  },
  {
    path: '/posify/close',
    component: () => import('./views/CloseShift.vue'),
    name: 'CloseShift',
    meta: { requiresShift: true },
  },
  {
    path: '/posify/orders',
    component: () => import('./views/Orders.vue'),
    name: 'Orders',
    meta: { requiresShift: true },
  },
  {
    path: '/posify/customers',
    component: () => import('./views/CustomerDisplay.vue'),
    name: 'Customers',
  },
  {
    path: '/posify/customers/:id',
    component: () => import('./views/CustomerDisplay.vue'),
    name: 'CustomerDetail',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.requiresShift) {
    const { usePosSessionStore } = await import('./stores/posSession')
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
  }
})

export default router
