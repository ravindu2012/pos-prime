<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { call } from 'frappe-ui'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import { useCustomerStore } from '@/stores/customer'
import { useCurrency } from '@/composables/useCurrency'
import { X, Search, RotateCcw, Loader2, Plus, Minus, Trash2 } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
  completed: []
}>()

const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()
const customerStore = useCustomerStore()
const { formatCurrency } = useCurrency()

// Item search
const searchInput = ref('')
const searchResults = ref<any[]>([])
const searchLoading = ref(false)
let debounceTimer: ReturnType<typeof setTimeout>

// Return items
interface ReturnItem {
  item_code: string
  item_name: string
  qty: number
  rate: number
}
const returnItems = ref<ReturnItem[]>([])

// Payment
const selectedPaymentMethod = ref(
  settingsStore.paymentMethods.find((p: any) => p.allow_in_returns)?.mode_of_payment ||
  settingsStore.defaultPaymentMethod
)

// Processing
const processing = ref(false)
const error = ref('')

const returnTotal = computed(() =>
  returnItems.value.reduce((sum, item) => sum + item.qty * item.rate, 0)
)

// Item search
async function searchItems() {
  if (!searchInput.value.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const data = await call('posify.api.items.get_items', {
      start: 0,
      page_length: 10,
      search_term: searchInput.value,
      pos_profile: sessionStore.posProfile,
    })
    searchResults.value = data?.items || []
  } catch {
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

watch(searchInput, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(searchItems, 300)
})

onUnmounted(() => {
  clearTimeout(debounceTimer)
})

function addItem(item: any) {
  const existing = returnItems.value.find((i) => i.item_code === item.item_code)
  if (existing) {
    existing.qty++
  } else {
    returnItems.value.push({
      item_code: item.item_code,
      item_name: item.item_name,
      qty: 1,
      rate: item.rate || 0,
    })
  }
  searchInput.value = ''
  searchResults.value = []
}

function removeItem(index: number) {
  returnItems.value.splice(index, 1)
}

function incrementQty(index: number) {
  returnItems.value[index].qty++
}

function decrementQty(index: number) {
  if (returnItems.value[index].qty > 1) {
    returnItems.value[index].qty--
  }
}

async function processReturn() {
  error.value = ''

  if (returnItems.value.length === 0) {
    error.value = 'Add at least one item to return'
    return
  }

  for (const item of returnItems.value) {
    if (item.qty <= 0) {
      error.value = `Qty for ${item.item_name} must be greater than 0`
      return
    }
    if (item.rate <= 0) {
      error.value = `Rate for ${item.item_name} must be greater than 0`
      return
    }
  }

  const customer = customerStore.customer?.name
  if (!customer) {
    error.value = 'No customer selected'
    return
  }

  processing.value = true
  try {
    await call('posify.api.orders.create_manual_return', {
      customer,
      pos_profile: sessionStore.posProfile,
      items: returnItems.value.map((item) => ({
        item_code: item.item_code,
        qty: item.qty,
        rate: item.rate,
      })),
      mode_of_payment: selectedPaymentMethod.value,
    })
    emit('completed')
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || 'Failed to process return'
  } finally {
    processing.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-label="Manual Return">
    <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="emit('close')" />
    <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-xl dark:shadow-black/30 w-full max-w-lg max-h-[90vh] flex flex-col">
      <!-- Header -->
      <div class="border-b border-gray-200 dark:border-gray-800 px-5 py-3 flex items-center justify-between rounded-t-xl shrink-0">
        <div class="flex items-center gap-2">
          <RotateCcw :size="18" class="text-red-600 dark:text-red-400" />
          <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">Return Items</h3>
        </div>
        <button @click="emit('close')" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
          <X :size="18" />
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div class="p-5 space-y-4">
          <!-- Error -->
          <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-sm">
            {{ error }}
          </div>

          <!-- Customer info -->
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Customer: <span class="font-medium text-gray-700 dark:text-gray-300">{{ customerStore.customer?.customer_name || customerStore.customer?.name || 'Not selected' }}</span>
          </div>

          <!-- Item search -->
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" :size="14" />
            <input
              v-model="searchInput"
              type="text"
              placeholder="Search items to return..."
              autofocus
              class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 placeholder-gray-400 dark:placeholder-gray-500"
            />

            <!-- Search dropdown -->
            <div
              v-if="searchInput.trim() && (searchResults.length > 0 || searchLoading)"
              class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto"
            >
              <div v-if="searchLoading" class="flex items-center justify-center py-4">
                <Loader2 :size="16" class="animate-spin text-gray-400" />
              </div>
              <button
                v-else
                v-for="item in searchResults"
                :key="item.item_code"
                @click="addItem(item)"
                class="w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
              >
                <div class="min-w-0">
                  <div class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{{ item.item_name }}</div>
                  <div class="text-xs text-gray-400 dark:text-gray-500">{{ item.item_code }}</div>
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-300 shrink-0 ml-2">{{ formatCurrency(item.rate) }}</div>
              </button>
            </div>
          </div>

          <!-- Return items list -->
          <div v-if="returnItems.length === 0" class="text-center py-6 text-sm text-gray-400 dark:text-gray-500">
            Search and add items to return
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="(item, index) in returnItems"
              :key="item.item_code"
              class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ item.item_name }}</div>
                  <div class="text-xs text-gray-400 dark:text-gray-500">{{ item.item_code }}</div>
                </div>
                <button @click="removeItem(index)" class="text-gray-400 hover:text-red-500 shrink-0">
                  <Trash2 :size="14" />
                </button>
              </div>
              <div class="flex items-center gap-3 mt-2">
                <!-- Qty controls -->
                <div class="flex items-center gap-1">
                  <button
                    @click="decrementQty(index)"
                    class="w-7 h-7 rounded-md border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Minus :size="12" />
                  </button>
                  <input
                    v-model.number="returnItems[index].qty"
                    type="number"
                    min="1"
                    class="w-14 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-2 py-1 text-sm text-center focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                  <button
                    @click="incrementQty(index)"
                    class="w-7 h-7 rounded-md border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Plus :size="12" />
                  </button>
                </div>
                <!-- Rate -->
                <div class="flex items-center gap-1">
                  <span class="text-xs text-gray-500 dark:text-gray-400">@</span>
                  <input
                    v-model.number="returnItems[index].rate"
                    type="number"
                    min="0"
                    step="0.01"
                    class="w-20 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                <!-- Line total -->
                <div class="ml-auto text-sm font-medium text-gray-800 dark:text-gray-200">
                  {{ formatCurrency(item.qty * item.rate) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Refund method -->
          <div v-if="returnItems.length > 0">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Refund Method</label>
            <select
              v-model="selectedPaymentMethod"
              class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option
                v-for="pm in settingsStore.paymentMethods"
                :key="pm.mode_of_payment"
                :value="pm.mode_of_payment"
              >
                {{ pm.mode_of_payment }}
              </option>
            </select>
          </div>

          <!-- Return total -->
          <div v-if="returnItems.length > 0" class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
            <div class="flex justify-between text-sm font-bold text-red-700 dark:text-red-400">
              <span>Refund Amount</span>
              <span>{{ formatCurrency(returnTotal) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit button -->
      <div v-if="returnItems.length > 0" class="border-t border-gray-200 dark:border-gray-800 px-5 py-3 shrink-0">
        <button
          @click="processReturn"
          :disabled="processing || returnTotal <= 0"
          class="w-full py-3 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          <RotateCcw :size="16" />
          {{ processing ? 'Processing...' : 'Process Return' }}
        </button>
      </div>
    </div>
  </div>
</template>
