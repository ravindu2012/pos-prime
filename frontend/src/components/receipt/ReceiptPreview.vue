<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { usePaymentStore } from '@/stores/payment'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import { useCurrency } from '@/composables/useCurrency'
import { Printer, Plus, X, Check, Share2, Loader2, Mail } from 'lucide-vue-next'
import EmailReceiptDialog from './EmailReceiptDialog.vue'

const emit = defineEmits<{
  newOrder: []
  close: []
}>()

const paymentStore = usePaymentStore()
const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()
const { formatCurrency } = useCurrency()

const invoice = computed(() => paymentStore.lastInvoice)

// Auto-print receipt if POS Profile setting is enabled
onMounted(() => {
  if (settingsStore.printReceiptOnOrderComplete && invoice.value) {
    nextTick(() => {
      printReceipt()
    })
  }
})

function sanitizeHtml(html: string | null | undefined): string {
  if (!html) return ''
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+="[^"]*"/gi, '')
    .replace(/on\w+='[^']*'/gi, '')
}

function printReceipt() {
  const printFormat = settingsStore.posProfile?.print_format
  if (printFormat && invoice.value?.name) {
    // Use ERPNext's print format via frappe print URL
    const url = `/printview?doctype=POS+Invoice&name=${encodeURIComponent(invoice.value.name)}&format=${encodeURIComponent(printFormat)}&no_letterhead=0`
    const printWindow = window.open(url, '_blank')
    if (printWindow) {
      printWindow.addEventListener('load', () => {
        printWindow.addEventListener('afterprint', () => {
          printWindow.close()
        })
        printWindow.print()
      })
    }
  } else {
    // Fallback to inline receipt print
    window.print()
  }
}

const sharing = ref(false)
const showEmailDialog = ref(false)

async function generateReceiptPdf(): Promise<Blob> {
  const { default: html2canvas } = await import('html2canvas')
  const { jsPDF } = await import('jspdf')

  const el = document.getElementById('receipt-content')
  if (!el) throw new Error('Receipt content not found')

  const canvas = await html2canvas(el, {
    scale: 2,
    useCORS: true,
    backgroundColor: '#ffffff',
  })

  const imgWidth = 80 // mm (receipt width)
  const imgHeight = (canvas.height * imgWidth) / canvas.width
  const pdf = new jsPDF({ unit: 'mm', format: [imgWidth, imgHeight + 10] })
  pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 5, imgWidth, imgHeight)
  return pdf.output('blob')
}

async function shareReceipt() {
  if (!invoice.value) return
  const inv = invoice.value
  sharing.value = true
  try {
    const blob = await generateReceiptPdf()
    const fileName = `${inv.name}.pdf`
    const file = new File([blob], fileName, { type: 'application/pdf' })

    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({
        files: [file],
        title: `Receipt ${inv.name}`,
        text: `Receipt from ${inv.company || sessionStore.company || 'Our Store'} - ${formatCurrency(inv.grand_total)}`,
      })
    } else {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (e: any) {
    if (e.name !== 'AbortError') {
      console.error('Share failed:', e)
    }
  } finally {
    sharing.value = false
  }
}

function newOrder() {
  emit('newOrder')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="invoice" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4" role="dialog" aria-label="Receipt">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm no-print" />
      <div class="relative bg-white dark:bg-gray-900 w-full sm:rounded-2xl sm:shadow-2xl dark:sm:shadow-black/30 sm:max-w-sm max-h-[100dvh] sm:max-h-[90vh] flex flex-col overflow-hidden rounded-t-2xl animate-slide-up sm:animate-scale-in">

        <!-- Success header (no-print) -->
        <div class="no-print bg-gradient-to-br from-green-500 to-green-600 text-white px-5 py-4 text-center relative overflow-hidden">
          <div class="absolute -top-6 -right-6 w-20 h-20 bg-white/10 rounded-full" />
          <div class="absolute -bottom-3 -left-3 w-14 h-14 bg-white/10 rounded-full" />
          <div class="relative">
            <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Check :size="22" />
            </div>
            <div class="text-sm font-semibold">Payment Successful</div>
            <div class="text-2xl font-bold mt-0.5">{{ formatCurrency(invoice.grand_total) }}</div>
          </div>
          <button
            @click="emit('close')"
            class="no-print absolute right-3 top-3 w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X :size="14" />
          </button>
        </div>

        <!-- Receipt content (scrollable) -->
        <div class="flex-1 overflow-y-auto">
          <div class="p-5 text-center" id="receipt-content">
            <!-- Company info -->
            <div class="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">
              {{ invoice.company || sessionStore.company || 'Company' }}
            </div>
            <div v-if="invoice.company_address_display || settingsStore.posProfile?.company_address" class="text-[10px] text-gray-400 dark:text-gray-500 mb-1 leading-tight">
              <span v-if="invoice.company_address_display" v-html="sanitizeHtml(invoice.company_address_display)" />
              <span v-else>{{ settingsStore.posProfile?.company_address }}</span>
            </div>
            <div class="text-[10px] text-gray-400 dark:text-gray-500 mb-4">
              {{ invoice.name }} &middot; {{ invoice.posting_date }}
              <span v-if="invoice.po_no"> &middot; PO: {{ invoice.po_no }}</span>
            </div>

            <!-- Return badge -->
            <div v-if="invoice.is_return" class="mb-3 px-3 py-1.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-[10px] font-bold uppercase tracking-wider">
              Return{{ invoice.return_against ? ` (against ${invoice.return_against})` : '' }}
            </div>

            <!-- Customer -->
            <div class="border-t border-dashed border-gray-200 dark:border-gray-700 pt-3 mb-3">
              <div class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-1 font-semibold">Customer</div>
              <div class="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {{ invoice.customer_name || invoice.customer }}
              </div>
              <div v-if="invoice.tax_id" class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Tax ID: {{ invoice.tax_id }}</div>
              <div v-if="invoice.address_display" class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5 leading-tight" v-html="sanitizeHtml(invoice.address_display)" />
              <div v-if="invoice.contact_mobile || invoice.contact_email" class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                {{ invoice.contact_mobile }}{{ invoice.contact_mobile && invoice.contact_email ? ' · ' : '' }}{{ invoice.contact_email }}
              </div>
            </div>

            <!-- Items -->
            <div class="border-t border-dashed border-gray-200 dark:border-gray-700 pt-3">
              <div
                v-for="item in invoice.items"
                :key="item.item_code"
                class="flex justify-between text-xs py-1.5"
              >
                <div class="text-left flex-1 pr-2">
                  <span class="text-gray-800 dark:text-gray-200 font-medium">{{ item.item_name }}</span>
                  <span class="text-gray-400 dark:text-gray-500 ml-1">&times;{{ item.qty }}</span>
                  <span v-if="item.discount_percentage > 0" class="text-orange-500 dark:text-orange-400 ml-1 text-[10px] font-semibold">
                    -{{ item.discount_percentage }}%
                  </span>
                  <span v-else-if="(item.discount_amount || 0) > 0" class="text-orange-500 dark:text-orange-400 ml-1 text-[10px] font-semibold">
                    -{{ formatCurrency(item.discount_amount || 0) }}
                  </span>
                  <div v-if="item.serial_no || item.batch_no" class="text-[9px] text-gray-400 dark:text-gray-500 mt-0.5">
                    <span v-if="item.batch_no">Batch: {{ item.batch_no }}</span>
                    <span v-if="item.serial_no">{{ item.batch_no ? ' · ' : '' }}SN: {{ item.serial_no }}</span>
                  </div>
                </div>
                <span class="text-gray-800 dark:text-gray-200 font-semibold shrink-0">
                  {{ formatCurrency(item.amount) }}
                </span>
              </div>
            </div>

            <!-- Totals -->
            <div class="border-t border-dashed border-gray-200 dark:border-gray-700 mt-3 pt-3 space-y-1">
              <div v-if="invoice.total_qty" class="flex justify-between text-[10px] text-gray-400 dark:text-gray-500">
                <span>Total Qty</span>
                <span>{{ invoice.total_qty }}</span>
              </div>

              <div v-if="invoice.net_total !== undefined" class="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                <span>Net Total</span>
                <span class="font-medium">{{ formatCurrency(invoice.net_total) }}</span>
              </div>

              <div
                v-for="tax in (invoice.taxes || [])"
                :key="tax.account_head"
                class="flex justify-between text-xs text-gray-500 dark:text-gray-400"
              >
                <span>{{ tax.description || tax.account_head }}</span>
                <span>{{ formatCurrency(tax.tax_amount) }}</span>
              </div>

              <!-- Discount -->
              <div v-if="invoice.discount_amount > 0" class="flex justify-between text-xs text-orange-600 dark:text-orange-400">
                <span>
                  Discount
                  <span v-if="invoice.additional_discount_percentage" class="text-[10px]">({{ invoice.additional_discount_percentage }}%)</span>
                </span>
                <span class="font-medium">-{{ formatCurrency(invoice.discount_amount) }}</span>
              </div>

              <!-- Coupon -->
              <div v-if="invoice.coupon_code" class="flex justify-between text-xs text-purple-600 dark:text-purple-400">
                <span>Coupon: {{ invoice.coupon_code }}</span>
                <span></span>
              </div>

              <!-- Write-off -->
              <div v-if="invoice.write_off_amount > 0" class="flex justify-between text-xs text-amber-600 dark:text-amber-400">
                <span>Write Off</span>
                <span>{{ formatCurrency(invoice.write_off_amount) }}</span>
              </div>

              <!-- Grand Total -->
              <div class="flex justify-between text-sm font-bold text-gray-900 dark:text-gray-100 pt-1.5 border-t border-dashed border-gray-200 dark:border-gray-700">
                <span>Grand Total</span>
                <span>{{ formatCurrency(invoice.grand_total) }}</span>
              </div>

              <!-- Rounded Total -->
              <div v-if="invoice.rounded_total && invoice.rounded_total !== invoice.grand_total" class="flex justify-between text-[10px] text-gray-400 dark:text-gray-500">
                <span>Rounded Total</span>
                <span>{{ formatCurrency(invoice.rounded_total) }}</span>
              </div>

              <!-- In Words -->
              <div v-if="invoice.in_words" class="text-[9px] text-gray-400 dark:text-gray-500 text-left italic pt-0.5">
                {{ invoice.in_words }}
              </div>

              <!-- Payments -->
              <div class="pt-1.5 border-t border-dashed border-gray-200 dark:border-gray-700 space-y-0.5">
                <div
                  v-for="payment in (invoice.payments || [])"
                  :key="payment.mode_of_payment"
                  class="flex justify-between text-xs text-gray-600 dark:text-gray-400"
                >
                  <span>{{ payment.mode_of_payment }}</span>
                  <span class="font-medium">{{ formatCurrency(payment.amount) }}</span>
                </div>
              </div>

              <div v-if="invoice.change_amount > 0" class="flex justify-between text-xs text-green-600 dark:text-green-400 font-semibold">
                <span>Change</span>
                <span>{{ formatCurrency(invoice.change_amount) }}</span>
              </div>

              <div v-if="invoice.outstanding_amount && invoice.outstanding_amount > 0" class="flex justify-between text-xs text-red-600 dark:text-red-400 font-semibold">
                <span>Outstanding</span>
                <span>{{ formatCurrency(invoice.outstanding_amount) }}</span>
              </div>

              <!-- Loyalty -->
              <div v-if="invoice.loyalty_points > 0" class="flex justify-between text-xs text-violet-600 dark:text-violet-400">
                <span>Loyalty Points Redeemed</span>
                <span>{{ invoice.loyalty_points }} pts ({{ formatCurrency(invoice.loyalty_amount) }})</span>
              </div>

              <!-- Sales Partner -->
              <div v-if="invoice.sales_partner" class="flex justify-between text-[10px] text-gray-400 dark:text-gray-500 pt-1">
                <span>Sales Partner</span>
                <span>{{ invoice.sales_partner }}</span>
              </div>
            </div>

            <!-- PO Reference -->
            <div v-if="invoice.po_no" class="mt-2 text-[10px] text-gray-400 dark:text-gray-500">
              Ref PO: {{ invoice.po_no }}
            </div>

            <!-- Remarks -->
            <div v-if="invoice.remarks" class="mt-2 text-[10px] text-gray-400 dark:text-gray-500 text-left">
              {{ invoice.remarks }}
            </div>

            <div class="mt-4 text-[10px] text-gray-400 dark:text-gray-500">
              Thank you for your purchase!
            </div>
          </div>
        </div>

        <!-- Actions (no-print) -->
        <div class="no-print px-4 py-3 border-t border-gray-100 dark:border-gray-800 flex flex-col gap-2 bg-white dark:bg-gray-900">
          <!-- Share receipt PDF - mobile only -->
          <button
            @click="shareReceipt"
            :disabled="sharing"
            class="sm:hidden w-full py-2.5 bg-[#25D366] text-white rounded-xl text-sm font-semibold hover:bg-[#1fb855] active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2 disabled:opacity-60"
          >
            <Loader2 v-if="sharing" :size="16" class="animate-spin" />
            <Share2 v-else :size="16" />
            {{ sharing ? 'Preparing...' : 'Share Receipt via WhatsApp' }}
          </button>
          <div class="flex gap-2">
            <button
              @click="printReceipt"
              class="flex-1 py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-semibold hover:bg-gray-200 dark:hover:bg-gray-700 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2"
            >
              <Printer :size="16" />
              Print
            </button>
            <button
              @click="showEmailDialog = true"
              class="py-2.5 px-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-semibold hover:bg-gray-200 dark:hover:bg-gray-700 active:scale-[0.98] transition-all duration-150 flex items-center justify-center"
            >
              <Mail :size="16" />
            </button>
            <button
              @click="newOrder"
              class="flex-1 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 active:scale-[0.98] shadow-lg shadow-blue-600/20 transition-all duration-150 flex items-center justify-center gap-2"
            >
              <Plus :size="16" />
              New Order
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Email Receipt Dialog -->
    <EmailReceiptDialog
      v-if="showEmailDialog && invoice"
      :invoice-name="invoice.name"
      :default-email="invoice.contact_email || ''"
      @close="showEmailDialog = false"
    />
  </Teleport>
</template>

<style scoped>
@keyframes slide-up {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@keyframes scale-in {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.animate-slide-up { animation: slide-up 0.3s ease-out; }
.animate-scale-in { animation: scale-in 0.2s ease-out; }
</style>
