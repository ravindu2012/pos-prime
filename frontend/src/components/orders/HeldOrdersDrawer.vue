<script setup lang="ts">
import { onMounted } from 'vue'
import { useDraftsStore } from '@/stores/drafts'
import { usePosSessionStore } from '@/stores/posSession'
import { useCurrency } from '@/composables/useCurrency'
import { X, Play, Trash2, PauseCircle, Loader2 } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
  resume: [invoiceName: string]
}>()

const draftsStore = useDraftsStore()
const sessionStore = usePosSessionStore()
const { formatCurrency } = useCurrency()

onMounted(async () => {
  if (sessionStore.posProfile) {
    await draftsStore.fetchDrafts(sessionStore.posProfile)
  }
})

async function resumeOrder(name: string) {
  emit('resume', name)
}

async function deleteOrder(name: string) {
  await draftsStore.deleteDraft(name)
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="emit('close')" />

      <!-- Drawer -->
      <Transition name="drawer">
        <div class="relative ml-auto w-full max-w-sm bg-white dark:bg-gray-900 shadow-2xl dark:shadow-black/30 flex flex-col h-full animate-slide-left">
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 bg-amber-50 dark:bg-amber-900/20 rounded-lg flex items-center justify-center">
                <PauseCircle :size="16" class="text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h3 class="text-sm font-bold text-gray-900 dark:text-gray-100">Held Orders</h3>
                <span v-if="draftsStore.drafts.length > 0" class="text-[10px] text-gray-400 dark:text-gray-500">
                  {{ draftsStore.drafts.length }} order{{ draftsStore.drafts.length !== 1 ? 's' : '' }}
                </span>
              </div>
            </div>
            <button
              @click="emit('close')"
              class="w-8 h-8 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center justify-center transition-colors"
            >
              <X :size="16" />
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto">
            <!-- Loading -->
            <div v-if="draftsStore.loading" class="flex items-center justify-center py-16">
              <Loader2 :size="24" class="text-gray-300 dark:text-gray-600 animate-spin" />
            </div>

            <!-- Empty -->
            <div
              v-else-if="draftsStore.drafts.length === 0"
              class="flex flex-col items-center justify-center py-16"
            >
              <div class="w-14 h-14 bg-gray-50 dark:bg-gray-800 rounded-2xl flex items-center justify-center mb-3">
                <PauseCircle :size="28" class="text-gray-200 dark:text-gray-600" />
              </div>
              <span class="text-sm font-medium text-gray-400 dark:text-gray-500">No held orders</span>
              <span class="text-xs text-gray-300 dark:text-gray-600 mt-0.5">Hold orders to save them for later</span>
            </div>

            <!-- Drafts list -->
            <div v-else class="p-3 space-y-2">
              <div
                v-for="draft in draftsStore.drafts"
                :key="draft.name"
                class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-3 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
              >
                <div class="flex items-start justify-between mb-2.5">
                  <div class="min-w-0 flex-1">
                    <div class="text-xs font-bold text-gray-900 dark:text-gray-100">{{ draft.name }}</div>
                    <div class="text-xs text-gray-600 dark:text-gray-400 font-medium mt-0.5 truncate">
                      {{ draft.customer_name || draft.customer }}
                    </div>
                    <div v-if="draft.owner" class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                      by {{ draft.owner }}
                    </div>
                  </div>
                  <div class="text-right shrink-0 ml-2">
                    <div class="text-sm font-bold text-gray-900 dark:text-gray-100">
                      {{ formatCurrency(draft.grand_total) }}
                    </div>
                    <div class="text-[10px] text-gray-400 dark:text-gray-500 font-medium">
                      {{ draft.item_count }} item{{ draft.item_count !== 1 ? 's' : '' }}
                    </div>
                  </div>
                </div>
                <div class="flex gap-1.5">
                  <button
                    @click="resumeOrder(draft.name)"
                    class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-1.5 shadow-sm shadow-blue-600/20"
                  >
                    <Play :size="12" />
                    Resume
                  </button>
                  <button
                    @click="deleteOrder(draft.name)"
                    class="py-2 px-3 bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 rounded-lg text-xs font-bold hover:bg-red-100 dark:hover:bg-red-900/40 active:scale-95 transition-all duration-150 flex items-center justify-center"
                  >
                    <Trash2 :size="12" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes slide-left {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.animate-slide-left { animation: slide-left 0.25s ease-out; }
</style>
