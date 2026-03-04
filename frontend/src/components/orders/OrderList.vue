<script setup lang="ts">
import { useCurrency } from '@/composables/useCurrency'
import type { OrderSummary } from '@/stores/orders'
import { FileText, RotateCcw } from 'lucide-vue-next'

defineProps<{
  orders: OrderSummary[]
  selectedName: string | null
  loading: boolean
}>()

const emit = defineEmits<{
  select: [name: string]
}>()

const { formatCurrency } = useCurrency()

function statusColor(order: OrderSummary) {
  if (order.is_return) return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
  if (order.docstatus === 0) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
  if (order.status === 'Paid') return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
  if (order.status === 'Consolidated') return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
  return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
}

function statusLabel(order: OrderSummary) {
  if (order.is_return) return 'Return'
  if (order.docstatus === 0) return 'Draft'
  return order.status
}
</script>

<template>
  <div class="space-y-1.5">
    <div v-if="loading && orders.length === 0" class="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">
      Loading orders...
    </div>
    <div v-else-if="orders.length === 0" class="flex flex-col items-center py-8 text-gray-400 dark:text-gray-500">
      <FileText :size="36" class="mb-2" />
      <span class="text-sm">No orders found</span>
    </div>
    <button
      v-for="order in orders"
      :key="order.name"
      @click="emit('select', order.name)"
      class="w-full text-left bg-white dark:bg-gray-900 border rounded-lg p-3 transition-colors"
      :class="
        selectedName === order.name
          ? 'border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      "
    >
      <div class="flex items-center justify-between">
        <div class="min-w-0 flex-1">
          <div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {{ order.name }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {{ order.customer_name }} &middot; {{ order.posting_date }}
          </div>
          <div v-if="order.owner" class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
            by {{ order.owner }}
          </div>
        </div>
        <div class="text-right shrink-0 ml-3">
          <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {{ formatCurrency(order.grand_total) }}
          </div>
          <span
            class="inline-flex items-center gap-0.5 mt-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full"
            :class="statusColor(order)"
          >
            <RotateCcw v-if="order.is_return" :size="8" />
            {{ statusLabel(order) }}
          </span>
        </div>
      </div>
    </button>
  </div>
</template>
