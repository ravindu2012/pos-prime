<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePosSessionStore } from '@/stores/posSession'
import { useCurrency } from '@/composables/useCurrency'
import { call } from 'frappe-ui'
import { LogOut } from 'lucide-vue-next'

const router = useRouter()
const sessionStore = usePosSessionStore()
const { formatCurrency } = useCurrency()

interface PaymentSummary {
  mode_of_payment: string
  opening_amount: number
  sales_amount: number
  expected_amount: number
  closing_amount: number
}

const paymentSummary = ref<PaymentSummary[]>([])
const grandTotal = ref(0)
const netTotal = ref(0)
const totalQuantity = ref(0)
const numInvoices = ref(0)
const loading = ref(false)
const loadingSummary = ref(true)
const error = ref('')

onMounted(async () => {
  if (!sessionStore.hasOpenShift) {
    router.replace('/posify/open')
    return
  }
  await loadSummary()
})

async function loadSummary() {
  loadingSummary.value = true
  try {
    const data = await call('posify.api.pos_session.get_shift_summary', {
      opening_entry: sessionStore.openingEntry,
    })
    grandTotal.value = data.grand_total || 0
    netTotal.value = data.net_total || 0
    totalQuantity.value = data.total_quantity || 0
    numInvoices.value = data.num_invoices || 0

    paymentSummary.value = (data.payment_summary || []).map((ps: any) => ({
      mode_of_payment: ps.mode_of_payment,
      opening_amount: ps.opening_amount,
      sales_amount: ps.sales_amount,
      expected_amount: ps.expected_amount,
      closing_amount: ps.expected_amount, // Pre-fill with expected
    }))
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || 'Failed to load shift summary'
  } finally {
    loadingSummary.value = false
  }
}

function getDifference(ps: PaymentSummary) {
  return ps.closing_amount - ps.expected_amount
}

async function handleCloseShift() {
  // Validate closing amounts are non-negative
  for (const ps of paymentSummary.value) {
    if (ps.closing_amount < 0) {
      error.value = 'Closing amounts cannot be negative'
      return
    }
  }
  loading.value = true
  error.value = ''
  try {
    await sessionStore.closeShift(
      paymentSummary.value.map((ps) => ({
        mode_of_payment: ps.mode_of_payment,
        closing_amount: ps.closing_amount,
      }))
    )
    router.replace('/posify/open')
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || 'Failed to close shift'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
    <div class="w-full max-w-2xl bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
      <div class="flex items-center gap-3 mb-6">
        <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-red-50 dark:bg-red-900/30">
          <LogOut class="text-red-600 dark:text-red-400" :size="20" />
        </div>
        <div>
          <h1 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Close POS Shift</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Enter closing balances to reconcile</p>
        </div>
      </div>

      <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-sm">
        {{ error }}
      </div>

      <div v-if="loadingSummary" class="py-12 text-center text-gray-400 dark:text-gray-500 text-sm">
        Loading shift summary...
      </div>

      <div v-else class="space-y-5">
        <!-- Session info -->
        <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">POS Profile</span>
            <span class="font-medium text-gray-800 dark:text-gray-200">{{ sessionStore.posProfile }}</span>
          </div>
          <div class="flex justify-between text-sm mt-1">
            <span class="text-gray-500 dark:text-gray-400">Opening Entry</span>
            <span class="font-medium text-gray-800 dark:text-gray-200">{{ sessionStore.openingEntry }}</span>
          </div>
        </div>

        <!-- Shift summary stats -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-blue-700 dark:text-blue-400">{{ numInvoices }}</div>
            <div class="text-xs text-blue-500 dark:text-blue-400/70">Invoices</div>
          </div>
          <div class="bg-green-50 dark:bg-green-900/30 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-green-700 dark:text-green-400">{{ formatCurrency(grandTotal) }}</div>
            <div class="text-xs text-green-500 dark:text-green-400/70">Grand Total</div>
          </div>
          <div class="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-purple-700 dark:text-purple-400">{{ formatCurrency(netTotal) }}</div>
            <div class="text-xs text-purple-500 dark:text-purple-400/70">Net Total</div>
          </div>
          <div class="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-orange-700 dark:text-orange-400">{{ totalQuantity }}</div>
            <div class="text-xs text-orange-500 dark:text-orange-400/70">Qty Sold</div>
          </div>
        </div>

        <!-- Payment reconciliation table -->
        <div>
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Payment Reconciliation</h3>
          <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                  <th class="text-left px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Mode</th>
                  <th class="text-right px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Opening</th>
                  <th class="text-right px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Expected</th>
                  <th class="text-right px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Closing</th>
                  <th class="text-right px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Diff</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(ps, index) in paymentSummary"
                  :key="ps.mode_of_payment"
                  class="border-b border-gray-100 dark:border-gray-800 last:border-0"
                >
                  <td class="px-3 py-2 font-medium text-gray-800 dark:text-gray-200">{{ ps.mode_of_payment }}</td>
                  <td class="px-3 py-2 text-right text-gray-500 dark:text-gray-400">{{ formatCurrency(ps.opening_amount) }}</td>
                  <td class="px-3 py-2 text-right text-gray-700 dark:text-gray-300 font-medium">{{ formatCurrency(ps.expected_amount) }}</td>
                  <td class="px-3 py-2 text-right">
                    <input
                      v-model.number="paymentSummary[index].closing_amount"
                      type="number"
                      min="0"
                      step="0.01"
                      class="w-28 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  </td>
                  <td
                    class="px-3 py-2 text-right font-medium"
                    :class="getDifference(ps) === 0 ? 'text-green-600 dark:text-green-400' : getDifference(ps) > 0 ? 'text-blue-600 dark:text-blue-400' : 'text-red-600 dark:text-red-400'"
                  >
                    {{ formatCurrency(getDifference(ps)) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="flex gap-3">
          <button
            @click="router.push('/posify')"
            class="flex-1 py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleCloseShift"
            :disabled="loading"
            class="flex-1 py-2.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ loading ? 'Closing...' : 'Close Shift' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
