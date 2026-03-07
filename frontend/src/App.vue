<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { session } from './stores/session'
import { useRTL } from './composables/useRTL'
import ToastContainer from './components/layout/ToastContainer.vue'

const { isRTL } = useRTL()
const initialized = ref(false)

onMounted(async () => {
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
  <div :dir="isRTL ? 'rtl' : 'ltr'">
    <router-view v-if="initialized" />
    <div v-else class="flex h-screen items-center justify-center bg-white dark:bg-gray-900">
      <div class="text-gray-500 dark:text-gray-400">{{ __('Loading...') }}</div>
    </div>
    <ToastContainer />
  </div>
</template>
