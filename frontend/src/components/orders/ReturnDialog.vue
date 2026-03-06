<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useCurrency } from '@/composables/useCurrency'
import { call } from 'frappe-ui'
import { X, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  order: Record<string, any>
}>()

const emit = defineEmits<{
  close: []
  completed: [data: any]
}>()

const settingsStore = useSettingsStore()
const { formatCurrency } = useCurrency()

interface ReturnItem {
  item_code: string
  item_name: string
  max_qty: number
  return_qty: number
  rate: number
}

const returnItems = ref<ReturnItem[]>(
  (props.order?.items || []).map((item: any) => ({
    item_code: item.item_code,
    item_name: item.item_name,
    max_qty: item.qty,
    return_qty: item.qty,
    rate: item.rate,
  }))
)

const selectedPaymentMethod = ref(
  settingsStore.paymentMethods.find((p) => p.allow_in_returns)?.mode_of_payment ||
  settingsStore.defaultPaymentMethod
)

const returnTotal = computed(() =>
  returnItems.value.reduce((sum, item) => sum + item.return_qty * item.rate, 0)
)

const loading = ref(false)
const error = ref('')

async function processReturn() {
  error.value = ''

  // Validate at least one item has qty > 0
  const hasReturnItems = returnItems.value.some(item => item.return_qty > 0)
  if (!hasReturnItems) {
    error.value = 'Please select at least one item to return'
    return
  }
  // Validate quantities don't exceed max
  for (const item of returnItems.value) {
    if (item.return_qty > item.max_qty) {
      error.value = `Return qty for ${item.item_name} cannot exceed ${item.max_qty}`
      return
    }
    if (item.return_qty < 0) {
      error.value = `Return qty for ${item.item_name} cannot be negative`
      return
    }
  }

  loading.value = true
  try {
    // Create the return invoice
    const returnDoc = await call('pos_prime.api.orders.create_return_invoice', {
      source_invoice: props.order.name,
    })

    // Submit with adjusted quantities
    const result = await call('pos_prime.api.orders.submit_return_invoice', {
      invoice_name: returnDoc.name,
      items: returnItems.value
        .filter((item) => item.return_qty > 0)
        .map((item) => ({
          item_code: item.item_code,
          qty: -item.return_qty, // Negative for return
        })),
      payments: [
        {
          mode_of_payment: selectedPaymentMethod.value,
          amount: -returnTotal.value, // Negative for return
        },
      ],
    })

    emit('completed', result)
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || 'Failed to process return'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-label="Process Return">
    <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="emit('close')" />
    <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-xl dark:shadow-black/30 w-full max-w-lg max-h-[90vh] overflow-y-auto">
      <div class="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-5 py-3 flex items-center justify-between rounded-t-xl z-10">
        <div class="flex items-center gap-2">
          <RotateCcw :size="18" class="text-red-600 dark:text-red-400" />
          <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">Process Return</h3>
        </div>
        <button @click="emit('close')" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
          <X :size="18" />
        </button>
      </div>

      <div class="p-5 space-y-4">
        <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-sm">
          {{ error }}
        </div>

        <div class="text-sm text-gray-500 dark:text-gray-400">
          Returning against: <span class="font-medium text-gray-700 dark:text-gray-300">{{ order.name }}</span>
        </div>

        <!-- Return items -->
        <div class="space-y-2">
          <div
            v-for="(item, index) in returnItems"
            :key="item.item_code"
            class="flex items-center gap-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ item.item_name }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatCurrency(item.rate) }} &middot; Max: {{ item.max_qty }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-xs text-gray-500 dark:text-gray-400">Qty:</label>
              <input
                v-model.number="returnItems[index].return_qty"
                type="number"
                :min="0"
                :max="item.max_qty"
                class="w-16 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-2 py-1 text-sm text-center focus:outline-none focus:ring-2 focus:ring-red-500"
              />
            </div>
            <div class="w-20 text-right text-sm font-medium text-gray-800 dark:text-gray-200">
              {{ formatCurrency(item.return_qty * item.rate) }}
            </div>
          </div>
        </div>

        <!-- Refund method -->
        <div>
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
        <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
          <div class="flex justify-between text-sm font-bold text-red-700 dark:text-red-400">
            <span>Refund Amount</span>
            <span>{{ formatCurrency(returnTotal) }}</span>
          </div>
        </div>

        <button
          @click="processReturn"
          :disabled="loading || returnTotal <= 0"
          class="w-full py-3 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          <RotateCcw :size="16" />
          {{ loading ? 'Processing...' : 'Process Return' }}
        </button>
      </div>
    </div>
  </div>
</template>
