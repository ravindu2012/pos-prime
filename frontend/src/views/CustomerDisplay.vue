<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCustomerDisplayStore } from '@/stores/customerDisplay'
import AppShell from '@/components/layout/AppShell.vue'
import {
  ArrowLeft,
  Search,
  X,
  MapPin,
  Phone,
  Mail,
  Star,
  ExternalLink,
  User,
  CreditCard,
  FileText,
  Award,
  Loader2,
  Clock,
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const store = useCustomerDisplayStore()

const searchInput = ref('')
const mobileShowDetail = ref(false)

let debounceTimer: ReturnType<typeof setTimeout>

onUnmounted(() => {
  clearTimeout(debounceTimer)
})

onMounted(() => {
  // If route has :id param, load that customer
  if (route.params.id) {
    store.loadCustomerDetail(route.params.id as string)
    mobileShowDetail.value = true
  }
  // Load recent customers on mount
  store.loadRecentCustomers()
})

watch(searchInput, (term) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    store.searchCustomers(term)
  }, 300)
})

async function selectCustomer(name: string) {
  await store.loadCustomerDetail(name)
  mobileShowDetail.value = true
}

function clearSearch() {
  searchInput.value = ''
  store.searchCustomers('')
}

function formatCurrency(amount: number, currency?: string) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 2,
    }).format(amount)
  } catch {
    return `${currency || ''} ${amount.toFixed(2)}`
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<template>
  <AppShell>
    <div class="h-full flex flex-col">
      <!-- Header -->
      <div class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center gap-3">
        <button
          @click="mobileShowDetail ? (mobileShowDetail = false) : router.push('/posify')"
          class="lg:hidden text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Customers</h2>
      </div>

      <div class="flex-1 flex overflow-hidden">
        <!-- Left: Search + List -->
        <div
          class="w-full lg:w-[360px] shrink-0 flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900"
          :class="{ 'hidden lg:flex': mobileShowDetail }"
        >
          <!-- Search -->
          <div class="p-3 border-b border-gray-200 dark:border-gray-800">
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" :size="14" />
              <input
                v-model="searchInput"
                type="text"
                placeholder="Search customers..."
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

          <!-- Customer list -->
          <div class="flex-1 overflow-y-auto p-3">
            <!-- Loading -->
            <div v-if="store.listLoading" class="flex items-center justify-center py-12">
              <Loader2 :size="24" class="animate-spin text-gray-400" />
            </div>

            <!-- No search: show recent customers -->
            <div v-else-if="!searchInput">
              <div v-if="store.recentCustomers.length > 0">
                <div class="flex items-center gap-1.5 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                  <Clock :size="12" />
                  Recent Customers
                </div>
                <div class="space-y-2">
                  <button
                    v-for="c in store.recentCustomers"
                    :key="c.name"
                    @click="selectCustomer(c.name)"
                    class="w-full text-left p-3 rounded-lg border transition-all duration-150"
                    :class="
                      store.selectedCustomer?.name === c.name
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-500'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                    "
                  >
                    <div class="font-medium text-sm text-gray-900 dark:text-gray-100">{{ c.customer_name }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ c.name }}</div>
                    <div class="flex items-center gap-3 mt-1.5 text-xs text-gray-400 dark:text-gray-500">
                      <span v-if="c.mobile_no" class="flex items-center gap-1">
                        <Phone :size="10" />
                        {{ c.mobile_no }}
                      </span>
                      <span v-if="c.email_id" class="flex items-center gap-1 truncate">
                        <Mail :size="10" />
                        {{ c.email_id }}
                      </span>
                      <span v-if="c.last_invoice_date" class="flex items-center gap-1 ml-auto">
                        <Clock :size="10" />
                        {{ formatDate(c.last_invoice_date) }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                <Search :size="32" class="mb-3" />
                <p class="text-sm">Search for a customer</p>
                <p class="text-xs mt-1">Type at least 2 characters</p>
              </div>
            </div>

            <!-- Search with no results -->
            <div v-else-if="store.customers.length === 0 && searchInput.length >= 2" class="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
              <User :size="32" class="mb-3" />
              <p class="text-sm">No customers found</p>
            </div>

            <!-- Search results -->
            <div v-else class="space-y-2">
              <button
                v-for="c in store.customers"
                :key="c.name"
                @click="selectCustomer(c.name)"
                class="w-full text-left p-3 rounded-lg border transition-all duration-150"
                :class="
                  store.selectedCustomer?.name === c.name
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-500'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                "
              >
                <div class="font-medium text-sm text-gray-900 dark:text-gray-100">{{ c.customer_name }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ c.name }}</div>
                <div v-if="c.mobile_no || c.email_id" class="flex items-center gap-3 mt-1.5 text-xs text-gray-400 dark:text-gray-500">
                  <span v-if="c.mobile_no" class="flex items-center gap-1">
                    <Phone :size="10" />
                    {{ c.mobile_no }}
                  </span>
                  <span v-if="c.email_id" class="flex items-center gap-1 truncate">
                    <Mail :size="10" />
                    {{ c.email_id }}
                  </span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Detail -->
        <div
          class="flex-1 bg-gray-100 dark:bg-gray-950 overflow-y-auto"
          :class="{ 'hidden lg:block': !mobileShowDetail }"
        >
          <!-- Loading -->
          <div v-if="store.detailLoading" class="flex items-center justify-center h-full">
            <Loader2 :size="32" class="animate-spin text-gray-400" />
          </div>

          <!-- No selection -->
          <div v-else-if="!store.selectedCustomer" class="flex flex-col items-center justify-center h-full bg-gray-100 dark:bg-gray-950">
            <div class="w-20 h-20 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center mb-5">
              <User :size="36" class="text-gray-400 dark:text-gray-500" />
            </div>
            <p class="text-lg font-semibold text-gray-600 dark:text-gray-300">Select a customer</p>
            <p class="text-sm mt-1.5 text-gray-400 dark:text-gray-500">Search and select a customer to view details</p>
          </div>

          <!-- Customer detail -->
          <div v-else class="max-w-3xl mx-auto p-4 lg:p-6 space-y-5">
            <!-- Header -->
            <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">
                    {{ store.selectedCustomer.customer_name }}
                  </h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{{ store.selectedCustomer.name }}</p>
                  <div class="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span v-if="store.selectedCustomer.customer_group" class="bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
                      {{ store.selectedCustomer.customer_group }}
                    </span>
                    <span v-if="store.selectedCustomer.territory" class="bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
                      {{ store.selectedCustomer.territory }}
                    </span>
                  </div>
                </div>
                <a
                  :href="`/app/customer/${store.selectedCustomer.name}`"
                  target="_blank"
                  class="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Open in ERPNext
                  <ExternalLink :size="12" />
                </a>
              </div>
            </div>

            <!-- Quick stats -->
            <div class="grid grid-cols-3 gap-3">
              <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <CreditCard :size="18" class="mx-auto text-orange-500 mb-1.5" />
                <div class="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {{ formatCurrency(store.outstanding.outstanding) }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Outstanding</div>
              </div>
              <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <Award :size="18" class="mx-auto text-purple-500 mb-1.5" />
                <div class="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {{ store.selectedCustomer.loyalty_points || 0 }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Loyalty Points</div>
              </div>
              <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <FileText :size="18" class="mx-auto text-blue-500 mb-1.5" />
                <div class="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {{ store.invoices.length }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Invoices</div>
              </div>
            </div>

            <!-- Basic info -->
            <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Basic Info</h4>
              <div class="space-y-2 text-sm">
                <div v-if="store.selectedCustomer.mobile_no" class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <Phone :size="14" class="text-gray-400" />
                  {{ store.selectedCustomer.mobile_no }}
                </div>
                <div v-if="store.selectedCustomer.email_id" class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <Mail :size="14" class="text-gray-400" />
                  {{ store.selectedCustomer.email_id }}
                </div>
                <div v-if="store.selectedCustomer.tax_id" class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <FileText :size="14" class="text-gray-400" />
                  Tax ID: {{ store.selectedCustomer.tax_id }}
                </div>
                <div v-if="store.outstanding.credit_limit" class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <CreditCard :size="14" class="text-gray-400" />
                  Credit Limit: {{ formatCurrency(store.outstanding.credit_limit) }}
                </div>
                <div v-if="!store.selectedCustomer.mobile_no && !store.selectedCustomer.email_id && !store.selectedCustomer.tax_id" class="text-gray-400 dark:text-gray-500 text-xs">
                  No contact info available
                </div>
              </div>
            </div>

            <!-- Addresses -->
            <div v-if="store.addresses.length > 0" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Addresses ({{ store.addresses.length }})
              </h4>
              <div class="space-y-3">
                <div
                  v-for="addr in store.addresses"
                  :key="addr.name"
                  class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <MapPin :size="12" class="text-gray-400" />
                    <span class="text-xs font-medium text-gray-700 dark:text-gray-300">
                      {{ addr.address_title || addr.name }}
                    </span>
                    <span v-if="addr.is_primary_address" class="text-[10px] bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded-full">Primary</span>
                    <span v-if="addr.is_shipping_address" class="text-[10px] bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-1.5 py-0.5 rounded-full">Shipping</span>
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 ml-5" v-html="addr.display" />
                </div>
              </div>
            </div>

            <!-- Contacts -->
            <div v-if="store.contacts.length > 0" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Contacts ({{ store.contacts.length }})
              </h4>
              <div class="space-y-3">
                <div
                  v-for="contact in store.contacts"
                  :key="contact.name"
                  class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <User :size="12" class="text-gray-400" />
                    <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ contact.full_name }}</span>
                    <span v-if="contact.is_primary_contact" class="text-[10px] bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded-full">Primary</span>
                    <span v-if="contact.is_billing_contact" class="text-[10px] bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-1.5 py-0.5 rounded-full">Billing</span>
                  </div>
                  <div class="ml-5 space-y-0.5 text-xs text-gray-500 dark:text-gray-400">
                    <div v-if="contact.phone || contact.mobile_no">
                      <Phone :size="10" class="inline mr-1" />
                      {{ contact.mobile_no || contact.phone }}
                    </div>
                    <div v-if="contact.email_id">
                      <Mail :size="10" class="inline mr-1" />
                      {{ contact.email_id }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loyalty -->
            <div v-if="store.loyaltyData" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                <Star :size="14" class="inline mr-1 text-purple-500" />
                Loyalty Program
              </h4>
              <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <div class="flex justify-between">
                  <span>Program</span>
                  <span class="font-medium text-gray-900 dark:text-gray-100">{{ store.loyaltyData.loyalty_program }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Points Balance</span>
                  <span class="font-medium text-gray-900 dark:text-gray-100">{{ store.loyaltyData.loyalty_points }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Conversion Factor</span>
                  <span class="font-medium text-gray-900 dark:text-gray-100">{{ store.loyaltyData.conversion_factor }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Max Redeemable</span>
                  <span class="font-medium text-gray-900 dark:text-gray-100">{{ formatCurrency(store.loyaltyData.max_redeemable_amount) }}</span>
                </div>
              </div>
            </div>

            <!-- Recent POS Invoices -->
            <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Recent POS Invoices
              </h4>
              <div v-if="store.invoices.length === 0" class="text-xs text-gray-400 dark:text-gray-500 py-4 text-center">
                No invoices found
              </div>
              <div v-else class="overflow-x-auto -mx-5 px-5">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                      <th class="pb-2 pr-3 font-medium">Invoice</th>
                      <th class="pb-2 pr-3 font-medium">Date</th>
                      <th class="pb-2 pr-3 font-medium text-right">Qty</th>
                      <th class="pb-2 pr-3 font-medium text-right">Total</th>
                      <th class="pb-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="inv in store.invoices"
                      :key="inv.name"
                      class="border-b border-gray-100 dark:border-gray-800 last:border-0"
                    >
                      <td class="py-2 pr-3">
                        <a
                          :href="`/app/pos-invoice/${inv.name}`"
                          target="_blank"
                          class="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          {{ inv.name }}
                        </a>
                      </td>
                      <td class="py-2 pr-3 text-gray-600 dark:text-gray-400">{{ formatDate(inv.posting_date) }}</td>
                      <td class="py-2 pr-3 text-right text-gray-600 dark:text-gray-400">{{ inv.total_qty }}</td>
                      <td class="py-2 pr-3 text-right font-medium text-gray-900 dark:text-gray-100">
                        {{ formatCurrency(inv.grand_total, inv.currency) }}
                      </td>
                      <td class="py-2">
                        <span
                          class="px-1.5 py-0.5 rounded-full text-[10px] font-medium"
                          :class="
                            inv.is_return
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                              : inv.status === 'Paid'
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                              : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                          "
                        >
                          {{ inv.is_return ? 'Return' : inv.status }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
