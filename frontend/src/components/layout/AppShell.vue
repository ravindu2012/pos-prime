<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { call } from 'frappe-ui'
import { useDraftsStore } from '@/stores/drafts'
import { usePosSessionStore } from '@/stores/posSession'
import { session as userSession } from '@/stores/session'
import { useDeskMode } from '@/composables/useDeskMode'
import {
  Grid3x3,
  ClipboardList,
  LogOut,
  Menu,
  X,
  PauseCircle,
  User,
  Users,
  Maximize,
  Minimize,
  RotateCcw,
  Monitor,
} from 'lucide-vue-next'
import DisplayControls from '@/components/display/DisplayControls.vue'

const { isDeskMode } = useDeskMode()
const router = useRouter()
const route = useRoute()
const draftsStore = useDraftsStore()
const sessionStore = usePosSessionStore()
const sidebarOpen = ref(false)
const showDisplayPopover = ref(false)

const companyLogo = ref<string | null>(null)
const companyAbbr = ref('P')
const userFullName = ref('')
const userImage = ref<string | null>(null)

const navItems = [
  { name: __('POS'), routeName: 'POS', icon: Grid3x3 },
  { name: __('Orders'), routeName: 'Orders', icon: ClipboardList },
  { name: __('Customers'), routeName: 'Customers', icon: Users },
]

const currentRouteName = computed(() => {
  if (route.name === 'CustomerDetail') return 'Customers'
  return route.name as string
})
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

  // Fetch app logo & favicon via backend endpoint (no Website Settings permission needed)
  try {
    const branding = await call('pos_prime.api.pos_session.get_branding', {
      company: sessionStore.company || '',
    })
    if (branding?.app_logo) {
      companyLogo.value = branding.app_logo
    } else if (branding?.company_logo) {
      companyLogo.value = branding.company_logo
    }
    if (branding?.favicon) {
      setFavicon(branding.favicon)
    } else if (branding?.company_logo) {
      setFavicon(branding.company_logo)
    }
    if (branding?.company_abbr) {
      companyAbbr.value = branding.company_abbr
    }
    if (!companyLogo.value && sessionStore.company) {
      companyAbbr.value = sessionStore.company[0]
    }
  } catch { /* ignore */ }

  // Fetch user info via backend endpoint (skip in desk mode — navbar shows user)
  if (!isDeskMode.value && userSession.user?.data) {
    try {
      const userInfo = await call('pos_prime.api.pos_session.get_user_info')
      if (userInfo) {
        userFullName.value = userInfo.full_name || userSession.user.data
        userImage.value = userInfo.user_image || null
      }
    } catch {
      userFullName.value = userSession.user.data
    }
  }
})

function navigate(routeName: string) {
  router.push({ name: routeName })
  sidebarOpen.value = false
}

function closeShift() {
  router.push({ name: 'CloseShift' })
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

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

if (typeof document !== 'undefined') {
  document.addEventListener('fullscreenchange', onFullscreenChange)
}

onUnmounted(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('fullscreenchange', onFullscreenChange)
  }
})

const emit = defineEmits<{
  toggleHeldOrders: []
  toggleReturn: []
}>()
</script>

<template>
  <div :class="['flex overflow-hidden bg-gray-50 dark:bg-gray-900', isDeskMode ? 'h-full' : 'h-screen']">
    <!-- Desktop Sidebar -->
    <aside
      class="hidden lg:flex flex-col items-center bg-white dark:bg-gray-900 border-e border-gray-100 dark:border-gray-800"
      :class="isDeskMode ? 'lg:w-[60px] py-1.5 gap-1' : 'lg:w-[68px] py-3 gap-1.5'"
    >
      <!-- Company Logo (hidden in desk mode — ERPNext navbar has it) -->
      <button v-if="!isDeskMode" @click="goToDesk" class="mb-3 cursor-pointer" :title="`Back to ${sessionStore.company || 'Desk'}`">
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
        :key="item.routeName"
        @click="navigate(item.routeName)"
        :aria-label="item.name"
        class="relative flex flex-col items-center justify-center rounded-xl transition-all duration-150"
        :class="[
          isDeskMode ? 'w-11 h-11' : 'w-12 h-12',
          currentRouteName === item.routeName
            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 shadow-sm shadow-blue-100 dark:shadow-blue-900/20'
            : 'text-gray-400 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300'
        ]"
      >
        <component :is="item.icon" :size="isDeskMode ? 18 : 20" :stroke-width="currentRouteName === item.routeName ? 2.5 : 2" />
        <span class="text-[10px] mt-0.5 font-semibold leading-none">{{ item.name }}</span>
      </button>

      <!-- Held orders -->
      <button
        @click="emit('toggleHeldOrders')"
        aria-label="Held Orders"
        class="relative flex flex-col items-center justify-center rounded-xl text-gray-400 dark:text-gray-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600 dark:hover:text-amber-400 transition-all duration-150"
        :class="isDeskMode ? 'w-11 h-11' : 'w-12 h-12'"
      >
        <PauseCircle :size="isDeskMode ? 18 : 20" />
        <span class="text-[10px] mt-0.5 font-semibold leading-none">{{ __('Held') }}</span>
        <span
          v-if="draftCount > 0"
          class="absolute -top-0.5 -end-0.5 bg-amber-500 text-white text-[8px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5 shadow-sm"
        >
          {{ draftCount > 9 ? '9+' : draftCount }}
        </span>
      </button>

      <!-- Return -->
      <button
        @click="emit('toggleReturn')"
        aria-label="Return"
        class="flex flex-col items-center justify-center rounded-xl text-gray-400 dark:text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 dark:hover:text-red-400 transition-all duration-150"
        :class="isDeskMode ? 'w-11 h-11' : 'w-12 h-12'"
      >
        <RotateCcw :size="isDeskMode ? 18 : 20" />
        <span class="text-[10px] mt-0.5 font-semibold leading-none">{{ __('Return') }}</span>
      </button>

      <!-- Display -->
      <div class="relative">
        <button
          @click="showDisplayPopover = !showDisplayPopover"
          aria-label="Customer Display"
          class="flex flex-col items-center justify-center rounded-xl text-gray-400 dark:text-gray-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 hover:text-purple-500 dark:hover:text-purple-400 transition-all duration-150"
          :class="[
            isDeskMode ? 'w-11 h-11' : 'w-12 h-12',
            showDisplayPopover ? 'bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400' : ''
          ]"
        >
          <Monitor :size="isDeskMode ? 18 : 20" />
          <span class="text-[10px] mt-0.5 font-semibold leading-none">{{ __('Display') }}</span>
        </button>
        <Transition name="fade">
          <div
            v-if="showDisplayPopover"
            class="fixed inset-0 z-40"
            @click="showDisplayPopover = false"
          />
        </Transition>
        <Transition name="fade">
          <div
            v-if="showDisplayPopover"
            class="absolute left-full top-0 ml-2 z-50"
          >
            <DisplayControls />
          </div>
        </Transition>
      </div>

      <div class="flex-1" />

      <!-- Fullscreen toggle -->
      <button
        @click="toggleFullscreen"
        :aria-label="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
        class="flex flex-col items-center justify-center rounded-xl text-gray-400 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 transition-all duration-150 mb-0.5"
        :class="isDeskMode ? 'w-11 h-11' : 'w-12 h-12'"
      >
        <Minimize v-if="isFullscreen" :size="isDeskMode ? 18 : 20" />
        <Maximize v-else :size="isDeskMode ? 18 : 20" />
      </button>

      <!-- User profile (hidden in desk mode — ERPNext navbar has it) -->
      <div v-if="!isDeskMode" class="flex flex-col items-center gap-1 mb-1" :title="userFullName || userSession.user?.data || ''">
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
        class="flex flex-col items-center justify-center rounded-xl text-gray-400 dark:text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 dark:hover:text-red-400 transition-all duration-150"
        :class="isDeskMode ? 'w-11 h-11' : 'w-12 h-12'"
      >
        <LogOut :size="isDeskMode ? 18 : 20" />
        <span class="text-[10px] mt-0.5 font-semibold leading-none">{{ __('Close') }}</span>
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
          <span class="font-bold text-gray-800 dark:text-gray-200 text-sm">{{ sessionStore.company || 'POS Prime' }}</span>
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
              class="absolute top-0.5 end-0.5 bg-amber-500 text-white text-[7px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center"
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
          class="lg:hidden fixed end-0 top-12 z-50 bg-white dark:bg-gray-900 shadow-xl rounded-bl-2xl w-52 border-s border-gray-100 dark:border-gray-800"
        >
          <div class="py-1">
            <button
              v-for="item in navItems"
              :key="item.routeName"
              @click="navigate(item.routeName)"
              class="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-colors"
              :class="
                currentRouteName === item.routeName
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
              {{ __('Return') }}
            </button>
            <div class="mx-4 my-1 border-t border-gray-100 dark:border-gray-800" />
            <button
              @click="closeShift"
              class="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <LogOut :size="16" />
              {{ __('Close Shift') }}
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
          :key="item.routeName"
          @click="navigate(item.routeName)"
          class="flex flex-col items-center justify-center flex-1 h-full transition-colors"
          :class="
            currentRouteName === item.routeName
              ? 'text-blue-600 dark:text-blue-400'
              : 'text-gray-400 dark:text-gray-500'
          "
        >
          <component :is="item.icon" :size="18" :stroke-width="currentRouteName === item.routeName ? 2.5 : 2" />
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
