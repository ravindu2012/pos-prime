<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { session } from './stores/session'
import { useRTL } from './composables/useRTL'
import { useDeskMode } from './composables/useDeskMode'
import ToastContainer from './components/layout/ToastContainer.vue'

const { isRTL } = useRTL()
const { isDeskMode } = useDeskMode()
const initialized = ref(false)

onMounted(async () => {
  if (isDeskMode.value) {
    // In desk mode, user is already authenticated
    try { await session.user.reload() } catch { /* ignore */ }
    initialized.value = true
    return
  }

  // Standalone mode — verify authentication
  try {
    await session.user.reload()
    if (!session.isLoggedIn) {
      window.location.href = '/login?redirect-to=/pos-prime'
      return
    }
  } catch {
    window.location.href = '/login?redirect-to=/pos-prime'
    return
  }
  initialized.value = true
})
</script>

<template>
  <div :dir="isRTL ? 'rtl' : 'ltr'" :class="isDeskMode ? 'h-full' : ''">
    <router-view v-if="initialized" />
    <div v-else class="flex items-center justify-center bg-white dark:bg-gray-900" :class="isDeskMode ? 'h-full' : 'h-screen'">
      <div class="text-gray-500 dark:text-gray-400">{{ __('Loading...') }}</div>
    </div>
    <ToastContainer />
  </div>
</template>
