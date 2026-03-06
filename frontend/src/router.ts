import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/pos-prime',
    component: () => import('./views/POS.vue'),
    name: 'POS',
    meta: { requiresShift: true },
  },
  {
    path: '/pos-prime/open',
    component: () => import('./views/OpenShift.vue'),
    name: 'OpenShift',
  },
  {
    path: '/pos-prime/close',
    component: () => import('./views/CloseShift.vue'),
    name: 'CloseShift',
    meta: { requiresShift: true },
  },
  {
    path: '/pos-prime/orders',
    component: () => import('./views/Orders.vue'),
    name: 'Orders',
    meta: { requiresShift: true },
  },
  {
    path: '/pos-prime/display',
    component: () => import('./views/CustomerPoleDisplay.vue'),
    name: 'PoleDisplay',
  },
  {
    path: '/pos-prime/customers',
    component: () => import('./views/CustomerDisplay.vue'),
    name: 'Customers',
  },
  {
    path: '/pos-prime/customers/:id',
    component: () => import('./views/CustomerDisplay.vue'),
    name: 'CustomerDetail',
  },
  {
    path: '/pos-prime/kiosk',
    component: () => import('./views/SelfCheckout.vue'),
    name: 'SelfCheckout',
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
