<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { session } from './stores/session'
import ToastContainer from './components/layout/ToastContainer.vue'

const router = useRouter()

onMounted(async () => {
  try {
    await session.user.reload()
    if (!session.isLoggedIn) {
      window.location.href = '/login?redirect-to=/posify'
    }
  } catch {
    window.location.href = '/login?redirect-to=/posify'
  }
})
</script>

<template>
  <router-view v-if="session.isLoggedIn" />
  <div v-else class="flex h-screen items-center justify-center bg-white dark:bg-gray-900">
    <div class="text-gray-500 dark:text-gray-400">Loading...</div>
  </div>
  <ToastContainer />
</template>
