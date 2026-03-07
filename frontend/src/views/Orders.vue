<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOrdersStore } from '@/stores/orders'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import AppShell from '@/components/layout/AppShell.vue'
import OrderList from '@/components/orders/OrderList.vue'
import OrderDetail from '@/components/orders/OrderDetail.vue'
import ReturnDialog from '@/components/orders/ReturnDialog.vue'
import { ArrowLeft, Search, X } from 'lucide-vue-next'

const router = useRouter()
const ordersStore = useOrdersStore()
const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()

const searchInput = ref('')
const showReturnDialog = ref(false)
const returnOrder = ref<Record<string, any> | null>(null)
const mobileShowDetail = ref(false)

let debounceTimer: ReturnType<typeof setTimeout>

onUnmounted(() => {
  clearTimeout(debounceTimer)
})

const statusTabs = [
  { label: __('All'), value: '' },
  { label: __('Paid'), value: 'Paid' },
  { label: __('Return'), value: 'Return' },
  { label: __('Draft'), value: 'Draft' },
]

onMounted(() => {
  if (sessionStore.posProfile) {
    ordersStore.fetchOrders(sessionStore.posProfile)
  }
})

watch(searchInput, (term) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    ordersStore.setSearchTerm(term)
    ordersStore.fetchOrders(sessionStore.posProfile)
  }, 300)
})

function selectStatus(status: string) {
  ordersStore.setStatusFilter(status)
  ordersStore.fetchOrders(sessionStore.posProfile)
}

async function selectOrder(name: string) {
  await ordersStore.loadOrderDetail(name)
  mobileShowDetail.value = true
}

function handleReturn(name: string) {
  returnOrder.value = ordersStore.selectedOrder
  showReturnDialog.value = true
}

function onReturnCompleted() {
  showReturnDialog.value = false
  returnOrder.value = null
  ordersStore.fetchOrders(sessionStore.posProfile)
}

function clearSearch() {
  searchInput.value = ''
  ordersStore.setSearchTerm('')
  ordersStore.fetchOrders(sessionStore.posProfile)
}

function handlePrint(invoiceName: string) {
  const printFormat = settingsStore.posProfile?.print_format
  if (printFormat) {
    const url = `/printview?doctype=POS+Invoice&name=${encodeURIComponent(invoiceName)}&format=${encodeURIComponent(printFormat)}&no_letterhead=0`
    window.open(url, '_blank')
  } else {
    window.print()
  }
}
</script>

<template>
  <AppShell>
    <div class="h-full flex flex-col">
      <div class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center gap-3">
        <button
          @click="mobileShowDetail ? (mobileShowDetail = false) : router.push('/pos-prime')"
          class="lg:hidden text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ __('Past Orders') }}</h2>
      </div>

      <div class="flex-1 flex overflow-hidden">
        <!-- Left: Search + List -->
        <div
          class="w-full lg:w-[360px] shrink-0 flex flex-col border-e border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900"
          :class="{ 'hidden lg:flex': mobileShowDetail }"
        >
          <!-- Search -->
          <div class="p-3 border-b border-gray-200 dark:border-gray-800">
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" :size="14" />
              <input
                v-model="searchInput"
                type="text"
                :placeholder="__('Search orders...')"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 pl-8 pr-8 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
              />
              <button
                v-if="searchInput"
                @click="clearSearch"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X :size="14" />
              </button>
            </div>
          </div>

          <!-- Status tabs -->
          <div class="flex gap-1 px-3 py-2 border-b border-gray-200 dark:border-gray-800">
            <button
              v-for="tab in statusTabs"
              :key="tab.value"
              @click="selectStatus(tab.value)"
              class="px-3 py-1 rounded-full text-xs font-medium transition-colors"
              :class="
                ordersStore.statusFilter === tab.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              "
            >
              {{ tab.label }}
            </button>
          </div>

          <!-- Order list -->
          <div class="flex-1 overflow-y-auto p-3">
            <OrderList
              :orders="ordersStore.orders"
              :selected-name="ordersStore.selectedOrder?.name || null"
              :loading="ordersStore.loading"
              @select="selectOrder"
            />
          </div>
        </div>

        <!-- Right: Detail -->
        <div
          class="flex-1 bg-gray-50 dark:bg-gray-900"
          :class="{ 'hidden lg:block': !mobileShowDetail }"
        >
          <OrderDetail
            :order="ordersStore.selectedOrder"
            :loading="ordersStore.loadingDetail"
            @print="handlePrint"
            @return="handleReturn"
          />
        </div>
      </div>
    </div>

    <!-- Return dialog -->
    <ReturnDialog
      v-if="showReturnDialog && returnOrder"
      :order="returnOrder"
      @close="showReturnDialog = false"
      @completed="onReturnCompleted"
    />
  </AppShell>
</template>
