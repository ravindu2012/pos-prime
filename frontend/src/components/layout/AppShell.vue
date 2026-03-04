<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { call } from 'frappe-ui'
import { useDraftsStore } from '@/stores/drafts'
import { usePosSessionStore } from '@/stores/posSession'
import { session as userSession } from '@/stores/session'
import {
  Grid3x3,
  ClipboardList,
  LogOut,
  Menu,
  X,
  PauseCircle,
  User,
  Maximize,
  Minimize,
  RotateCcw,
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const draftsStore = useDraftsStore()
const sessionStore = usePosSessionStore()
const sidebarOpen = ref(false)

const companyLogo = ref<string | null>(null)
const companyAbbr = ref('P')
const userFullName = ref('')
const userImage = ref<string | null>(null)

const navItems = [
  { name: 'POS', path: '/posify', icon: Grid3x3 },
  { name: 'Orders', path: '/posify/orders', icon: ClipboardList },
]

const currentPath = computed(() => route.path)
const draftCount = computed(() => draftsStore.drafts.length)

const userInitials = computed(() => {
  if (!userFullName.value) return '?'
  const parts = userFullName.value.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return parts[0][0].toUpperCase()
})

function setFavicon(url: string) {
  let link = document.querySelector<HTMLLinkElement>("link[rel~='icon']")
  if (!link) {
    link = document.createElement('link')
    link.rel = 'icon'
    document.head.appendChild(link)
  }
  link.href = url
}

function goToDesk() {
  window.location.href = '/app'
}

onMounted(async () => {
  if (sessionStore.posProfile) {
    await draftsStore.fetchDrafts(sessionStore.posProfile)
  }

  // Fetch company logo
  if (sessionStore.company) {
    try {
      const doc = await call('frappe.client.get_value', {
        doctype: 'Company',
        filters: { name: sessionStore.company },
        fieldname: ['company_logo', 'abbr'],
      })
      if (doc) {
        companyLogo.value = doc.company_logo || null
        companyAbbr.value = doc.abbr || sessionStore.company[0]
        if (doc.company_logo) {
          setFavicon(doc.company_logo)
        }
      }
    } catch { /* ignore */ }
  }

  // Fetch user info
  if (userSession.user?.data) {
    try {
      const doc = await call('frappe.client.get_value', {
        doctype: 'User',
        filters: { name: userSession.user.data },
        fieldname: ['full_name', 'user_image'],
      })
      if (doc) {
        userFullName.value = doc.full_name || userSession.user.data
        userImage.value = doc.user_image || null
      }
    } catch {
      userFullName.value = userSession.user.data
    }
  }
})

function navigate(path: string) {
  router.push(path)
  sidebarOpen.value = false
}

function closeShift() {
  router.push('/posify/close')
  sidebarOpen.value = false
}

const isFullscreen = ref(false)

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

if (typeof document !== 'undefined') {
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
}

const emit = defineEmits<{
  toggleHeldOrders: []
  toggleReturn: []
}>()
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
    <!-- Desktop Sidebar -->
    <aside
      class="hidden lg:flex lg:w-[60px] flex-col items-center bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800 py-3 gap-1"
    >
      <!-- Company Logo -->
      <button @click="goToDesk" class="mb-3 cursor-pointer" :title="`Back to ${sessionStore.company || 'Desk'}`">
        <img
          v-if="companyLogo"
          :src="companyLogo"
          :alt="sessionStore.company"
          class="w-9 h-9 rounded-xl object-contain"
        />
        <div v-else class="w-9 h-9 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-sm shadow-blue-600/20">
          <span class="text-white font-bold text-sm">{{ companyAbbr }}</span>
        </div>
      </button>

      <!-- Nav items -->
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigate(item.path)"
        :aria-label="item.name"
        class="relative flex flex-col items-center justify-center w-11 h-11 rounded-xl transition-all duration-200"
        :class="
          currentPath === item.path
            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
            : 'text-gray-400 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300'
        "
      >
        <component :is="item.icon" :size="18" :stroke-width="currentPath === item.path ? 2.5 : 2" />
        <span class="text-[9px] mt-0.5 font-semibold">{{ item.name }}</span>
      </button>

      <!-- Held orders -->
      <button
        @click="emit('toggleHeldOrders')"
        aria-label="Held Orders"
        class="relative flex flex-col items-center justify-center w-11 h-11 rounded-xl text-gray-400 dark:text-gray-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600 dark:hover:text-amber-400 transition-all duration-200"
      >
        <PauseCircle :size="18" />
        <span class="text-[9px] mt-0.5 font-semibold">Held</span>
        <span
          v-if="draftCount > 0"
          class="absolute -top-0.5 -right-0.5 bg-amber-500 text-white text-[8px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5 shadow-sm"
        >
          {{ draftCount > 9 ? '9+' : draftCount }}
        </span>
      </button>

      <!-- Return -->
      <button
        @click="emit('toggleReturn')"
        aria-label="Return"
        class="flex flex-col items-center justify-center w-11 h-11 rounded-xl text-gray-400 dark:text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 dark:hover:text-red-400 transition-all duration-200"
      >
        <RotateCcw :size="18" />
        <span class="text-[9px] mt-0.5 font-semibold">Return</span>
      </button>

      <div class="flex-1" />

      <!-- Fullscreen toggle -->
      <button
        @click="toggleFullscreen"
        :aria-label="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
        class="flex flex-col items-center justify-center w-11 h-11 rounded-xl text-gray-400 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 transition-all duration-200 mb-1"
      >
        <Minimize v-if="isFullscreen" :size="18" />
        <Maximize v-else :size="18" />
      </button>

      <!-- User profile -->
      <div class="flex flex-col items-center gap-1 mb-1" :title="userFullName || userSession.user?.data || ''">
        <img
          v-if="userImage"
          :src="userImage"
          :alt="userFullName"
          class="w-8 h-8 rounded-full object-cover border border-gray-200 dark:border-gray-700"
        />
        <div v-else class="w-8 h-8 bg-blue-100 dark:bg-blue-900/40 rounded-full flex items-center justify-center">
          <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400">{{ userInitials }}</span>
        </div>
        <span class="text-[8px] text-gray-400 dark:text-gray-500 font-medium text-center leading-tight max-w-[56px] truncate">
          {{ userFullName.split(' ')[0] || userSession.user?.data }}
        </span>
      </div>

      <!-- Close shift -->
      <button
        @click="closeShift"
        aria-label="Close Shift"
        class="flex flex-col items-center justify-center w-11 h-11 rounded-xl text-gray-400 dark:text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 dark:hover:text-red-400 transition-all duration-200"
      >
        <LogOut :size="18" />
        <span class="text-[9px] mt-0.5 font-semibold">Close</span>
      </button>
    </aside>

    <!-- Main content area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Mobile header -->
      <header class="lg:hidden flex items-center justify-between bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 px-4 h-12">
        <button @click="goToDesk" class="flex items-center gap-2 cursor-pointer" :title="`Back to ${sessionStore.company || 'Desk'}`">
          <img
            v-if="companyLogo"
            :src="companyLogo"
            :alt="sessionStore.company"
            class="w-6 h-6 rounded-lg object-contain"
          />
          <div v-else class="w-6 h-6 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-[10px]">{{ companyAbbr }}</span>
          </div>
          <span class="font-bold text-gray-800 dark:text-gray-200 text-sm">{{ sessionStore.company || 'Posify' }}</span>
        </button>
        <div class="flex items-center gap-1">
          <button
            @click="emit('toggleHeldOrders')"
            aria-label="Held Orders"
            class="relative w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 dark:text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors"
          >
            <PauseCircle :size="18" />
            <span
              v-if="draftCount > 0"
              class="absolute top-0.5 right-0.5 bg-amber-500 text-white text-[7px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center"
            >
              {{ draftCount }}
            </span>
          </button>
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle menu"
          >
            <Menu v-if="!sidebarOpen" :size="18" />
            <X v-else :size="18" />
          </button>
        </div>
      </header>

      <!-- Mobile menu overlay -->
      <Transition name="fade">
        <div
          v-if="sidebarOpen"
          class="lg:hidden fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
          @click="sidebarOpen = false"
        />
      </Transition>
      <Transition name="slide-right">
        <nav
          v-if="sidebarOpen"
          class="lg:hidden fixed right-0 top-12 z-50 bg-white dark:bg-gray-900 shadow-xl rounded-bl-2xl w-52 border-l border-gray-100 dark:border-gray-800"
        >
          <div class="py-1">
            <button
              v-for="item in navItems"
              :key="item.path"
              @click="navigate(item.path)"
              class="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-colors"
              :class="
                currentPath === item.path
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
              "
            >
              <component :is="item.icon" :size="16" />
              {{ item.name }}
            </button>
            <button
              @click="emit('toggleReturn'); sidebarOpen = false"
              class="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400"
            >
              <RotateCcw :size="16" />
              Return
            </button>
            <div class="mx-4 my-1 border-t border-gray-100 dark:border-gray-800" />
            <button
              @click="closeShift"
              class="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <LogOut :size="16" />
              Close Shift
            </button>
          </div>
        </nav>
      </Transition>

      <main class="flex-1 overflow-hidden">
        <slot />
      </main>

      <!-- Mobile bottom nav -->
      <nav class="lg:hidden flex items-center justify-around bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 h-14">
        <button
          v-for="item in navItems"
          :key="item.path"
          @click="navigate(item.path)"
          class="flex flex-col items-center justify-center flex-1 h-full transition-colors"
          :class="
            currentPath === item.path
              ? 'text-blue-600 dark:text-blue-400'
              : 'text-gray-400 dark:text-gray-500'
          "
        >
          <component :is="item.icon" :size="18" :stroke-width="currentPath === item.path ? 2.5 : 2" />
          <span class="text-[9px] mt-0.5 font-semibold">{{ item.name }}</span>
        </button>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-right-enter-active {
  transition: transform 0.2s ease-out, opacity 0.2s ease-out;
}
.slide-right-leave-active {
  transition: transform 0.15s ease-in, opacity 0.15s ease-in;
}
.slide-right-enter-from {
  transform: translateX(100%);
  opacity: 0;
}
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
