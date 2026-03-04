<script setup lang="ts">
import { useCurrency } from '@/composables/useCurrency'
import { Printer, RotateCcw, FileText } from 'lucide-vue-next'
import type { POSInvoice } from '@/types'

const props = defineProps<{
  order: POSInvoice | null
  loading: boolean
}>()

function sanitizeHtml(html: string | null | undefined): string {
  if (!html) return ''
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+="[^"]*"/gi, '')
    .replace(/on\w+='[^']*'/gi, '')
}

const emit = defineEmits<{
  print: [name: string]
  return: [name: string]
}>()

const { formatCurrency } = useCurrency()

function canReturn() {
  return props.order && props.order.docstatus === 1 && !props.order.is_return
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-gray-400 dark:text-gray-500 text-sm">Loading details...</div>
    </div>

    <div v-else-if="!order" class="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
      <FileText :size="40" class="mb-2" />
      <span class="text-sm">Select an order to view details</span>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">{{ order.name }}</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ order.posting_date }} {{ order.posting_time }}</p>
            <p v-if="order.owner" class="text-[10px] text-gray-400 dark:text-gray-500">by {{ order.owner }}</p>
          </div>
          <div class="flex gap-2">
            <button
              @click="emit('print', order.name)"
              class="px-3 py-1.5 text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center gap-1"
            >
              <Printer :size="12" />
              Print
            </button>
            <button
              v-if="canReturn()"
              @click="emit('return', order.name)"
              class="px-3 py-1.5 text-xs font-medium bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors flex items-center gap-1"
            >
              <RotateCcw :size="12" />
              Return
            </button>
          </div>
        </div>
        <div class="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Customer: <span class="font-medium text-gray-900 dark:text-gray-200">{{ order.customer_name || order.customer }}</span>
        </div>
        <div v-if="order.is_return" class="mt-1 text-xs text-red-600 dark:text-red-400 font-medium">
          Return against {{ order.return_against }}
        </div>

        <!-- Additional info badges -->
        <div class="flex flex-wrap gap-1.5 mt-2">
          <span v-if="order.currency && order.currency !== 'USD'" class="text-[10px] bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-1.5 py-0.5 rounded">
            {{ order.currency }}
          </span>
          <span v-if="order.coupon_code" class="text-[10px] bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 px-1.5 py-0.5 rounded">
            Coupon: {{ order.coupon_code }}
          </span>
          <span v-if="order.loyalty_points > 0" class="text-[10px] bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded">
            {{ order.loyalty_points }} pts redeemed
          </span>
          <span v-if="order.consolidated_invoice" class="text-[10px] bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded">
            Consolidated: {{ order.consolidated_invoice }}
          </span>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-4 py-3">
        <!-- Address & Contact info -->
        <div v-if="order.address_display || order.shipping_address || order.contact_display" class="mb-4 space-y-1.5">
          <h4 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase">Address & Contact</h4>
          <div v-if="order.address_display" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Billing: </span>
            <span v-html="sanitizeHtml(order.address_display)" />
          </div>
          <div v-if="order.shipping_address" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Shipping: </span>
            <span v-html="sanitizeHtml(order.shipping_address)" />
          </div>
          <div v-if="order.contact_display" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Contact: </span>{{ order.contact_display }}
            <span v-if="order.contact_mobile"> ({{ order.contact_mobile }})</span>
          </div>
        </div>

        <!-- Document details -->
        <div v-if="order.po_no || order.project || order.sales_partner || order.remarks" class="mb-4 space-y-1">
          <h4 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase">Details</h4>
          <div v-if="order.po_no" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Customer PO: </span>{{ order.po_no }}
            <span v-if="order.po_date"> ({{ order.po_date }})</span>
          </div>
          <div v-if="order.project" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Project: </span>{{ order.project }}
          </div>
          <div v-if="order.sales_partner" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Sales Partner: </span>{{ order.sales_partner }}
            <span v-if="order.commission_rate"> ({{ order.commission_rate }}%)</span>
            <span v-if="order.total_commission"> = {{ formatCurrency(order.total_commission) }}</span>
          </div>
          <div v-if="order.remarks" class="text-xs text-gray-600 dark:text-gray-400">
            <span class="text-gray-400 dark:text-gray-500">Remarks: </span>{{ order.remarks }}
          </div>
        </div>

        <!-- Items -->
        <h4 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase mb-2">Items</h4>
        <div class="space-y-1.5">
          <div
            v-for="item in order.items"
            :key="item.item_code"
            class="flex items-center justify-between py-1.5"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm text-gray-800 dark:text-gray-200">{{ item.item_name }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatCurrency(item.rate) }} x {{ item.qty }}
                <span v-if="item.discount_percentage > 0" class="text-orange-500 dark:text-orange-400">
                  (-{{ item.discount_percentage }}%)
                </span>
                <span v-else-if="item.discount_amount > 0" class="text-orange-500 dark:text-orange-400">
                  (-{{ formatCurrency(item.discount_amount) }}/unit)
                </span>
                <span v-if="item.uom && item.stock_uom && item.uom !== item.stock_uom" class="text-gray-400 dark:text-gray-500">
                  · {{ item.uom }}
                </span>
              </div>
              <div v-if="item.serial_no || item.batch_no" class="text-[10px] text-gray-400 dark:text-gray-500">
                <span v-if="item.batch_no">Batch: {{ item.batch_no }}</span>
                <span v-if="item.serial_no">{{ item.batch_no ? ' · ' : '' }}SN: {{ item.serial_no }}</span>
              </div>
              <div v-if="item.item_tax_template" class="text-[10px] text-purple-400 dark:text-purple-500">
                Tax: {{ item.item_tax_template }}
              </div>
            </div>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">
              {{ formatCurrency(item.amount) }}
            </span>
          </div>
        </div>

        <!-- Taxes -->
        <div v-if="order.taxes && order.taxes.length > 0" class="mt-4">
          <h4 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase mb-2">Taxes</h4>
          <div v-for="tax in order.taxes" :key="tax.account_head" class="flex justify-between text-sm py-0.5">
            <span class="text-gray-500 dark:text-gray-400">{{ tax.description || tax.account_head }}</span>
            <span class="text-gray-700 dark:text-gray-300">{{ formatCurrency(tax.tax_amount) }}</span>
          </div>
        </div>

        <!-- Payments -->
        <div v-if="order.payments && order.payments.length > 0" class="mt-4">
          <h4 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase mb-2">Payments</h4>
          <div v-for="p in order.payments" :key="p.mode_of_payment" class="flex justify-between text-sm py-0.5">
            <span class="text-gray-500 dark:text-gray-400">{{ p.mode_of_payment }}</span>
            <span class="text-gray-700 dark:text-gray-300">{{ formatCurrency(p.amount) }}</span>
          </div>
        </div>
      </div>

      <!-- Totals -->
      <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 space-y-1">
        <div v-if="order.total_qty" class="flex justify-between text-xs text-gray-400 dark:text-gray-500">
          <span>Total Qty</span>
          <span>{{ order.total_qty }}</span>
        </div>
        <div class="flex justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>Net Total</span>
          <span>{{ formatCurrency(order.net_total) }}</span>
        </div>
        <div v-if="order.total_taxes_and_charges > 0" class="flex justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>Taxes & Charges</span>
          <span>{{ formatCurrency(order.total_taxes_and_charges) }}</span>
        </div>
        <div v-if="order.discount_amount > 0" class="flex justify-between text-sm text-orange-500 dark:text-orange-400">
          <span>
            Discount
            <span v-if="order.additional_discount_percentage">({{ order.additional_discount_percentage }}%)</span>
          </span>
          <span>-{{ formatCurrency(order.discount_amount) }}</span>
        </div>
        <div v-if="order.write_off_amount > 0" class="flex justify-between text-sm text-yellow-600 dark:text-yellow-400">
          <span>Write Off</span>
          <span>{{ formatCurrency(order.write_off_amount) }}</span>
        </div>
        <div class="flex justify-between text-sm font-bold text-gray-900 dark:text-gray-100">
          <span>Grand Total</span>
          <span>{{ formatCurrency(order.grand_total) }}</span>
        </div>
        <div v-if="order.rounded_total && order.rounded_total !== order.grand_total" class="flex justify-between text-xs text-gray-400 dark:text-gray-500">
          <span>Rounded Total</span>
          <span>{{ formatCurrency(order.rounded_total) }}</span>
        </div>
        <div v-if="order.in_words" class="text-[10px] text-gray-400 dark:text-gray-500 italic">
          {{ order.in_words }}
        </div>
        <div class="flex justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>Paid</span>
          <span>{{ formatCurrency(order.paid_amount) }}</span>
        </div>
        <div v-if="order.change_amount > 0" class="flex justify-between text-sm text-green-600 dark:text-green-400">
          <span>Change</span>
          <span>{{ formatCurrency(order.change_amount) }}</span>
        </div>
        <div v-if="order.outstanding_amount > 0" class="flex justify-between text-sm text-red-600 dark:text-red-400">
          <span>Outstanding</span>
          <span>{{ formatCurrency(order.outstanding_amount) }}</span>
        </div>
        <div v-if="order.loyalty_points > 0" class="flex justify-between text-sm text-indigo-500 dark:text-indigo-400">
          <span>Loyalty Redeemed</span>
          <span>{{ order.loyalty_points }} pts ({{ formatCurrency(order.loyalty_amount) }})</span>
        </div>

        <!-- Base currency totals (multi-currency) -->
        <div v-if="order.conversion_rate && order.conversion_rate !== 1" class="pt-2 border-t border-gray-200 dark:border-gray-700 mt-2">
          <div class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase mb-1">Company Currency</div>
          <div class="flex justify-between text-xs text-gray-400 dark:text-gray-500">
            <span>Conversion Rate</span>
            <span>{{ order.conversion_rate }}</span>
          </div>
          <div v-if="order.base_grand_total" class="flex justify-between text-xs text-gray-400 dark:text-gray-500">
            <span>Base Grand Total</span>
            <span>{{ order.base_grand_total }}</span>
          </div>
          <div v-if="order.base_paid_amount" class="flex justify-between text-xs text-gray-400 dark:text-gray-500">
            <span>Base Paid Amount</span>
            <span>{{ order.base_paid_amount }}</span>
          </div>
        </div>

        <!-- Weight -->
        <div v-if="order.total_net_weight" class="flex justify-between text-xs text-gray-400 dark:text-gray-500">
          <span>Total Weight</span>
          <span>{{ order.total_net_weight }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
