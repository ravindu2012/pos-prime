<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { call } from 'frappe-ui'
import { useCustomerStore } from '@/stores/customer'
import { usePosSessionStore } from '@/stores/posSession'
import { useCurrency } from '@/composables/useCurrency'
import {
  X, User, Mail, Phone, MapPin, Tag, CreditCard,
  FileText, ExternalLink, AlertTriangle, Wallet
} from 'lucide-vue-next'
import { deskUrl } from '@/utils/deskUrl'

const emit = defineEmits<{ close: [] }>()
const customerStore = useCustomerStore()
const sessionStore = usePosSessionStore()
const { formatCurrency } = useCurrency()

// Editable fields
const editEmail = ref('')
const editMobile = ref('')
const editLoyaltyProgram = ref('')
const savingField = ref<string | null>(null)

// Transactions
const transactions = ref<any[]>([])
const loadingTx = ref(false)

onMounted(async () => {
  if (!customerStore.customer) return
  editEmail.value = customerStore.customer.email_id || ''
  editMobile.value = customerStore.customer.mobile_no || ''
  editLoyaltyProgram.value = customerStore.customer.loyalty_program || ''
  await fetchTransactions()
})

async function fetchTransactions() {
  if (!customerStore.customer) return
  loadingTx.value = true
  try {
    const data = await call('pos_prime.api.customer_profile.get_customer_pos_invoices', {
      customer: customerStore.customer.name,
      company: sessionStore.company || '',
      limit: 20,
    })
    transactions.value = data || []
  } catch {
    transactions.value = []
  } finally {
    loadingTx.value = false
  }
}

async function saveField(fieldname: string) {
  if (!customerStore.customer) return
  const value = fieldname === 'email_id' ? editEmail.value.trim()
    : fieldname === 'mobile_no' ? editMobile.value.trim()
    : editLoyaltyProgram.value.trim()

  // Skip if unchanged
  const original = (customerStore.customer as any)[fieldname] || ''
  if (value === original) return

  savingField.value = fieldname
  try {
    await call('pos_prime.api.customers.update_customer_field', {
      customer: customerStore.customer.name,
      fieldname,
      value,
    })
    // Refresh customer data
    await customerStore.setCustomer(customerStore.customer.name)
    // Sync local edits
    if (customerStore.customer) {
      editEmail.value = customerStore.customer.email_id || ''
      editMobile.value = customerStore.customer.mobile_no || ''
      editLoyaltyProgram.value = customerStore.customer.loyalty_program || ''
    }
  } catch (e: any) {
    const frappe = (window as any).frappe
    frappe?.show_alert?.({ message: e.messages?.[0] || __('Failed to update'), indicator: 'red' })
  } finally {
    savingField.value = null
  }
}

function openCustomerForm() {
  if (!customerStore.customer) return
  window.open(deskUrl(`customer/${encodeURIComponent(customerStore.customer.name)}`), '_blank')
}

function openInvoice(invoiceName: string) {
  window.open(deskUrl(`pos-invoice/${encodeURIComponent(invoiceName)}`), '_blank')
}

function statusColor(status: string, isReturn: boolean): string {
  if (isReturn) return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
  if (status === 'Paid') return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
  if (status === 'Consolidated') return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
  if (status === 'Draft') return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
  return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const frappe = (window as any).frappe
  if (frappe?.datetime?.str_to_user) {
    return frappe.datetime.str_to_user(dateStr)
  }
  return dateStr
}

function timeAgo(dateStr: string): string {
  if (!dateStr) return ''
  const frappe = (window as any).frappe
  if (frappe?.datetime?.comment_when) {
    return frappe.datetime.comment_when(dateStr)
  }
  return dateStr
}
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-stretch justify-end"
    role="dialog"
    aria-modal="true"
    @keydown.escape="emit('close')"
  >
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="emit('close')" />

    <!-- Panel (slide-in from right) -->
    <div class="relative w-full max-w-md bg-white dark:bg-gray-900 shadow-2xl dark:shadow-black/50 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
        <h3 class="text-sm font-bold text-gray-900 dark:text-gray-100">{{ __('Customer Details') }}</h3>
        <div class="flex items-center gap-1">
          <button
            @click="openCustomerForm"
            class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
            :title="__('Open Full Form')"
          >
            <ExternalLink :size="14" />
          </button>
          <button
            @click="emit('close')"
            class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X :size="16" />
          </button>
        </div>
      </div>

      <!-- Scrollable content -->
      <div v-if="customerStore.customer" class="flex-1 overflow-y-auto">
        <!-- Customer identity -->
        <div class="px-4 py-4 border-b border-gray-100 dark:border-gray-800">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900/40 rounded-xl flex items-center justify-center shrink-0">
              <User :size="22" class="text-blue-600 dark:text-blue-400" />
            </div>
            <div class="min-w-0">
              <div class="text-base font-bold text-gray-900 dark:text-gray-100 truncate">
                {{ customerStore.customer.customer_name }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ customerStore.customer.name }}</div>
              <div v-if="customerStore.customer.customer_group" class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                {{ customerStore.customer.customer_group }}
                <span v-if="customerStore.customer.territory"> &middot; {{ customerStore.customer.territory }}</span>
              </div>
            </div>
          </div>

          <!-- Quick stats -->
          <div class="flex gap-2 mt-3 flex-wrap">
            <div
              v-if="customerStore.loyaltyPoints > 0"
              class="flex items-center gap-1 px-2 py-1 bg-violet-50 dark:bg-violet-900/20 rounded-lg"
            >
              <Tag :size="12" class="text-violet-500" />
              <span class="text-xs font-semibold text-violet-700 dark:text-violet-400">{{ customerStore.loyaltyPoints }} {{ __('pts') }}</span>
            </div>
            <div
              v-if="customerStore.outstanding > 0"
              class="flex items-center gap-1 px-2 py-1 bg-amber-50 dark:bg-amber-900/20 rounded-lg"
            >
              <AlertTriangle :size="12" class="text-amber-500" />
              <span class="text-xs font-semibold text-amber-700 dark:text-amber-400">{{ __('Outstanding') }}: {{ formatCurrency(customerStore.outstanding) }}</span>
            </div>
            <div
              v-if="customerStore.creditLimit > 0"
              class="flex items-center gap-1 px-2 py-1 rounded-lg"
              :class="customerStore.outstanding > customerStore.creditLimit
                ? 'bg-red-50 dark:bg-red-900/20'
                : 'bg-gray-50 dark:bg-gray-800'"
            >
              <CreditCard :size="12" :class="customerStore.outstanding > customerStore.creditLimit ? 'text-red-500' : 'text-gray-400'" />
              <span
                class="text-xs font-semibold"
                :class="customerStore.outstanding > customerStore.creditLimit
                  ? 'text-red-700 dark:text-red-400'
                  : 'text-gray-600 dark:text-gray-400'"
              >{{ __('Limit') }}: {{ formatCurrency(customerStore.creditLimit) }}</span>
            </div>
            <div
              v-if="customerStore.storeCredit > 0"
              class="flex items-center gap-1 px-2 py-1 bg-green-50 dark:bg-green-900/20 rounded-lg"
            >
              <Wallet :size="12" class="text-green-500" />
              <span class="text-xs font-semibold text-green-700 dark:text-green-400">{{ __('Credit') }}: {{ formatCurrency(customerStore.storeCredit) }}</span>
            </div>
          </div>
        </div>

        <!-- Editable fields -->
        <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-800 space-y-3">
          <div class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Contact Details') }}</div>

          <!-- Email -->
          <div>
            <label class="text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1 block">{{ __('Email') }}</label>
            <div class="flex items-center gap-2">
              <Mail :size="14" class="text-gray-400 shrink-0" />
              <input
                v-model="editEmail"
                type="email"
                :placeholder="__('Email address')"
                @blur="saveField('email_id')"
                @keydown.enter="($event.target as HTMLInputElement).blur()"
                :disabled="savingField === 'email_id'"
                class="flex-1 text-sm text-gray-800 dark:text-gray-200 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 transition-colors disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500"
              />
              <span v-if="savingField === 'email_id'" class="text-[10px] text-blue-500 shrink-0">{{ __('Saving...') }}</span>
            </div>
          </div>

          <!-- Mobile -->
          <div>
            <label class="text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1 block">{{ __('Mobile') }}</label>
            <div class="flex items-center gap-2">
              <Phone :size="14" class="text-gray-400 shrink-0" />
              <input
                v-model="editMobile"
                type="tel"
                :placeholder="__('Mobile number')"
                @blur="saveField('mobile_no')"
                @keydown.enter="($event.target as HTMLInputElement).blur()"
                :disabled="savingField === 'mobile_no'"
                class="flex-1 text-sm text-gray-800 dark:text-gray-200 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 transition-colors disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500"
              />
              <span v-if="savingField === 'mobile_no'" class="text-[10px] text-blue-500 shrink-0">{{ __('Saving...') }}</span>
            </div>
          </div>

          <!-- Loyalty Program -->
          <div v-if="customerStore.customer.loyalty_program || editLoyaltyProgram" class="flex items-center gap-2">
            <Tag :size="14" class="text-gray-400 shrink-0" />
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ editLoyaltyProgram || __('No loyalty program') }}</span>
          </div>

          <!-- Primary Address -->
          <div v-if="customerStore.addresses.length > 0" class="flex items-start gap-2">
            <MapPin :size="14" class="text-gray-400 shrink-0 mt-0.5" />
            <div class="text-xs text-gray-600 dark:text-gray-400">
              <span class="font-medium text-gray-700 dark:text-gray-300">
                {{ customerStore.addresses.find(a => a.is_primary_address)?.address_title || customerStore.addresses[0].address_title }}
              </span>
              <br />
              {{ customerStore.addresses.find(a => a.is_primary_address)?.address_line1 || customerStore.addresses[0].address_line1 }}
              <span v-if="(customerStore.addresses.find(a => a.is_primary_address) || customerStore.addresses[0]).city">
                , {{ (customerStore.addresses.find(a => a.is_primary_address) || customerStore.addresses[0]).city }}
              </span>
            </div>
          </div>
        </div>

        <!-- Recent Transactions -->
        <div class="px-4 py-3">
          <div class="flex items-center justify-between mb-2">
            <div class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Recent Transactions') }}</div>
            <span v-if="transactions.length > 0" class="text-[10px] text-gray-400 dark:text-gray-500">
              {{ __('Last') }}: {{ timeAgo(transactions[0]?.posting_date) }}
            </span>
          </div>

          <div v-if="loadingTx" class="py-6 text-center">
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ __('Loading...') }}</span>
          </div>

          <div v-else-if="transactions.length === 0" class="py-6 text-center">
            <FileText :size="24" class="text-gray-300 dark:text-gray-600 mx-auto mb-1" />
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ __('No transactions found') }}</span>
          </div>

          <div v-else class="space-y-1">
            <button
              v-for="tx in transactions"
              :key="tx.name"
              @click="openInvoice(tx.name)"
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left group"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span class="text-xs font-semibold text-gray-800 dark:text-gray-200">{{ tx.name }}</span>
                  <span
                    class="inline-flex px-1.5 py-0.5 rounded text-[9px] font-bold"
                    :class="statusColor(tx.status, tx.is_return)"
                  >
                    {{ tx.is_return ? __('Return') : tx.status }}
                  </span>
                </div>
                <div class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                  {{ formatDate(tx.posting_date) }}
                </div>
              </div>
              <div class="text-right shrink-0">
                <div
                  class="text-sm font-bold"
                  :class="tx.is_return ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-200'"
                >
                  {{ tx.is_return ? '-' : '' }}{{ formatCurrency(tx.grand_total) }}
                </div>
                <div class="text-[10px] text-gray-400 dark:text-gray-500">
                  {{ tx.total_qty }} {{ __('items') }}
                </div>
              </div>
              <ExternalLink :size="12" class="text-gray-300 dark:text-gray-600 group-hover:text-blue-400 shrink-0" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
