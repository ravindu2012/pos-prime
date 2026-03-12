<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { call } from 'frappe-ui'
import { useCustomerStore } from '@/stores/customer'
import { usePosSessionStore } from '@/stores/posSession'
import { useCurrency } from '@/composables/useCurrency'
import { User, X, Plus, Search, Phone, Tag, AlertTriangle, ChevronRight, Loader2, ChevronDown } from 'lucide-vue-next'

const { formatCurrency } = useCurrency()

const emit = defineEmits<{
  openDetail: []
}>()

const customerStore = useCustomerStore()
const sessionStore = usePosSessionStore()
const searchTerm = ref('')
const results = ref<{ name: string; customer_name: string; mobile_no?: string; email_id?: string }[]>([])
const showDropdown = ref(false)
let debounceTimer: ReturnType<typeof setTimeout>

// Quick Entry state
const showQuickEntry = ref(false)
const quickEntryLoading = ref(false)
const quickEntrySaving = ref(false)
const quickEntryError = ref('')
const quickEntryOptions = ref<any>(null)
const quickEntryForm = ref<Record<string, string>>({})
const customerNameInput = ref<HTMLInputElement | null>(null)
const showContactSection = ref(false)
const showAddressSection = ref(false)

onUnmounted(() => {
  clearTimeout(debounceTimer)
})

watch(searchTerm, (term) => {
  clearTimeout(debounceTimer)
  if (term.length < 2) {
    results.value = []
    showDropdown.value = false
    return
  }
  debounceTimer = setTimeout(async () => {
    results.value = await customerStore.searchCustomers(term, sessionStore.posProfile)
    showDropdown.value = results.value.length > 0
  }, 300)
})

async function selectCustomer(name: string) {
  await customerStore.setCustomer(name)
  searchTerm.value = ''
  results.value = []
  showDropdown.value = false
}

function clearCustomer() {
  customerStore.$reset()
}

async function openQuickEntry() {
  showQuickEntry.value = true
  quickEntryLoading.value = true
  quickEntryError.value = ''
  quickEntryForm.value = {}

  try {
    const options = await call('pos_prime.api.customers.get_quick_entry_options', {
      pos_profile: sessionStore.posProfile || '',
    })
    quickEntryOptions.value = options

    // Set defaults
    quickEntryForm.value = {
      customer_name: searchTerm.value || '',
      customer_type: options.default_customer_type || 'Individual',
      customer_group: options.default_customer_group || '',
      territory: options.default_territory || '',
      mobile_no: '',
      email_id: '',
      first_name: '',
      last_name: '',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      pincode: '',
      country: options.default_country || '',
    }
    showContactSection.value = false
    showAddressSection.value = false

    // Set defaults for extra quick_entry fields
    for (const f of options.quick_fields || []) {
      if (f.default && !(f.fieldname in quickEntryForm.value)) {
        quickEntryForm.value[f.fieldname] = f.default
      }
    }

    await nextTick()
    customerNameInput.value?.focus()
  } catch {
    quickEntryError.value = __('Failed to load form options')
  } finally {
    quickEntryLoading.value = false
  }
}

function closeQuickEntry() {
  showQuickEntry.value = false
  quickEntryOptions.value = null
  quickEntryForm.value = {}
  quickEntryError.value = ''
}

async function submitQuickEntry() {
  if (!quickEntryForm.value.customer_name?.trim()) {
    quickEntryError.value = __('Customer name is required')
    return
  }

  quickEntrySaving.value = true
  quickEntryError.value = ''

  try {
    const args: Record<string, string> = {
      ...quickEntryForm.value,
      pos_profile: sessionStore.posProfile || '',
    }
    await customerStore.quickCreateCustomer(args as any)
    closeQuickEntry()
    searchTerm.value = ''
    results.value = []
    showDropdown.value = false
  } catch (e: any) {
    quickEntryError.value = e.messages?.[0] || e.message || __('Failed to create customer')
  } finally {
    quickEntrySaving.value = false
  }
}

// Check if a field is one of the standard ones we render manually
const standardFields = new Set(['customer_name', 'customer_type', 'customer_group', 'territory', 'mobile_no', 'email_id'])
function isExtraField(fieldname: string) {
  return !standardFields.has(fieldname)
}
</script>

<template>
  <div class="relative">
    <!-- Selected customer display (ERPNext-style: circular avatar + name/desc) -->
    <div v-if="customerStore.customer" class="flex items-center gap-3">
      <button
        @click="emit('openDetail')"
        class="flex items-center gap-3 flex-1 min-w-0 text-left cursor-pointer"
      >
        <!-- Circular avatar (ERPNext-style) -->
        <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-gray-100 dark:bg-gray-800">
          <User :size="18" class="text-gray-500 dark:text-gray-400" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">
            {{ customerStore.customer.customer_name }}
          </div>
          <div class="flex items-center gap-1.5 flex-wrap mt-0.5">
            <span v-if="customerStore.customer.mobile_no" class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-0.5 font-medium">
              <Phone :size="10" />
              {{ customerStore.customer.mobile_no }}
            </span>
            <span v-if="customerStore.customer.email_id" class="text-xs text-gray-500 dark:text-gray-400 font-medium">
              {{ customerStore.customer.mobile_no ? '·' : '' }} {{ customerStore.customer.email_id }}
            </span>
            <span v-else-if="customerStore.customer.customer_group" class="text-xs text-gray-400 dark:text-gray-500 font-medium">
              {{ customerStore.customer.mobile_no ? '·' : '' }} {{ customerStore.customer.customer_group }}
            </span>
          </div>
          <div v-if="customerStore.loyaltyPoints > 0 || customerStore.outstanding > 0 || customerStore.creditLimit > 0" class="flex items-center gap-1.5 flex-wrap mt-1">
            <span
              v-if="customerStore.loyaltyPoints > 0"
              class="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400 rounded-md text-[9px] font-bold"
            >
              <Tag :size="8" />
              {{ customerStore.loyaltyPoints }} pts
            </span>
            <span
              v-if="customerStore.outstanding > 0"
              class="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 rounded-md text-[9px] font-bold"
            >
              <AlertTriangle :size="8" />
              {{ formatCurrency(customerStore.outstanding) }}
            </span>
            <span
              v-if="customerStore.creditLimit > 0"
              class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[9px] font-bold"
              :class="customerStore.outstanding > customerStore.creditLimit
                ? 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'"
            >
              {{ __('Limit') }}: {{ formatCurrency(customerStore.creditLimit) }}
            </span>
          </div>
        </div>
        <ChevronRight :size="14" class="text-gray-400 dark:text-gray-500 shrink-0" />
      </button>
      <button
        @click="clearCustomer"
        class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors shrink-0 cursor-pointer"
        aria-label="Clear customer"
      >
        <X :size="14" />
      </button>
    </div>

    <!-- Customer search -->
    <div v-else>
      <div class="relative flex items-center">
        <Search class="absolute left-3 text-gray-400 dark:text-gray-500 pointer-events-none" :size="14" />
        <input
          v-model="searchTerm"
          type="text"
          :placeholder="__('Search by customer name, phone, email.')"
          aria-label="Search customer"
          class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:bg-white dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 pl-8 pr-10 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 focus:bg-white dark:focus:bg-gray-700 transition-all duration-200 placeholder-gray-400 dark:placeholder-gray-500"
          @focus="showDropdown = results.length > 0"
        />
        <button
          @click="openQuickEntry"
          class="absolute right-2 w-7 h-7 rounded-md flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
          :title="__('New Customer')"
          :aria-label="__('New Customer')"
        >
          <Plus :size="16" />
        </button>
      </div>

      <!-- Dropdown -->
      <Transition name="dropdown">
        <div
          v-if="showDropdown"
          class="absolute z-20 left-0 right-0 mt-1.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl dark:shadow-black/30 max-h-48 overflow-y-auto"
        >
          <button
            v-for="c in results"
            :key="c.name"
            @click="selectCustomer(c.name)"
            class="w-full text-left px-3 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors first:rounded-t-lg last:rounded-b-lg"
          >
            <div class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ c.customer_name }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
              {{ c.name }}
              <span v-if="c.mobile_no"> · {{ c.mobile_no }}</span>
            </div>
          </button>
        </div>
      </Transition>
    </div>

    <!-- Quick Entry Dialog -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showQuickEntry"
          class="fixed inset-0 z-50 flex items-center justify-center"
          @keydown.escape="closeQuickEntry"
        >
          <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="closeQuickEntry" />
          <div class="relative w-full max-w-sm mx-4 bg-white dark:bg-gray-900 rounded-xl shadow-2xl dark:shadow-black/50 overflow-hidden" style="color-scheme: light dark;">
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80">
              <div class="flex items-center gap-2">
                <div class="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
                  <User :size="14" class="text-blue-600 dark:text-blue-400" />
                </div>
                <h3 class="text-sm font-bold text-gray-900 dark:text-gray-100">{{ __('New Customer') }}</h3>
              </div>
              <button
                @click="closeQuickEntry"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <X :size="16" />
              </button>
            </div>

            <!-- Loading -->
            <div v-if="quickEntryLoading" class="px-4 py-8 text-center">
              <Loader2 :size="20" class="animate-spin text-blue-400 dark:text-blue-500 mx-auto" />
            </div>

            <!-- Form -->
            <form v-else @submit.prevent="submitQuickEntry" class="max-h-[70vh] overflow-y-auto">
              <div class="px-4 py-3 space-y-3">
                <!-- Error -->
                <div v-if="quickEntryError" class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-md px-3 py-2">
                  {{ quickEntryError }}
                </div>

                <!-- Customer Name (required) -->
                <div>
                  <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Customer Name') }} *</label>
                  <input
                    ref="customerNameInput"
                    v-model="quickEntryForm.customer_name"
                    type="text"
                    required
                    :placeholder="__('Full name')"
                    class="qe-input"
                  />
                </div>

                <!-- Customer Type -->
                <div v-if="quickEntryOptions?.customer_types?.length > 1">
                  <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Customer Type') }}</label>
                  <select v-model="quickEntryForm.customer_type" class="qe-input">
                    <option v-for="t in quickEntryOptions.customer_types" :key="t" :value="t">{{ t }}</option>
                  </select>
                </div>

                <!-- Customer Group -->
                <div v-if="quickEntryOptions?.customer_groups?.length > 0">
                  <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Customer Group') }}</label>
                  <select v-model="quickEntryForm.customer_group" class="qe-input">
                    <option v-for="g in quickEntryOptions.customer_groups" :key="g" :value="g">{{ g }}</option>
                  </select>
                </div>

                <!-- Extra quick_entry fields from Customer doctype -->
                <template v-if="quickEntryOptions?.quick_fields">
                  <div v-for="f in quickEntryOptions.quick_fields.filter((ff: any) => isExtraField(ff.fieldname))" :key="f.fieldname">
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">
                      {{ f.label }}{{ f.reqd ? ' *' : '' }}
                    </label>
                    <select
                      v-if="f.fieldtype === 'Select' && f.options"
                      v-model="quickEntryForm[f.fieldname]"
                      :required="!!f.reqd"
                      class="qe-input"
                    >
                      <option v-for="opt in f.options.split('\n').filter((o: string) => o.trim())" :key="opt" :value="opt">{{ opt }}</option>
                    </select>
                    <input
                      v-else
                      v-model="quickEntryForm[f.fieldname]"
                      :type="f.fieldtype === 'Int' ? 'number' : 'text'"
                      :required="!!f.reqd"
                      class="qe-input"
                    />
                  </div>
                </template>
              </div>

              <!-- Primary Contact Details (collapsible) -->
              <div class="border-t border-gray-100 dark:border-gray-800">
                <button
                  type="button"
                  @click="showContactSection = !showContactSection"
                  class="w-full flex items-center justify-between px-4 py-2.5 text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  {{ __('Primary Contact Details') }}
                  <ChevronDown :size="14" class="transition-transform" :class="showContactSection ? 'rotate-180' : ''" />
                </button>
                <div v-show="showContactSection" class="px-4 pb-3 space-y-3">
                  <!-- First Name (hidden for Company type) -->
                  <div v-if="quickEntryForm.customer_type !== 'Company'">
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('First Name') }}</label>
                    <input v-model="quickEntryForm.first_name" type="text" :placeholder="__('First name')" class="qe-input" />
                  </div>
                  <!-- Last Name (hidden for Company type) -->
                  <div v-if="quickEntryForm.customer_type !== 'Company'">
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Last Name') }}</label>
                    <input v-model="quickEntryForm.last_name" type="text" :placeholder="__('Last name')" class="qe-input" />
                  </div>
                  <!-- Email -->
                  <div>
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Email Id') }}</label>
                    <input v-model="quickEntryForm.email_id" type="email" :placeholder="__('Email address')" class="qe-input" />
                  </div>
                  <!-- Mobile -->
                  <div>
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Mobile Number') }}</label>
                    <input v-model="quickEntryForm.mobile_no" type="tel" :placeholder="__('Mobile number')" class="qe-input" />
                  </div>
                </div>
              </div>

              <!-- Primary Address Details (collapsible) -->
              <div class="border-t border-gray-100 dark:border-gray-800">
                <button
                  type="button"
                  @click="showAddressSection = !showAddressSection"
                  class="w-full flex items-center justify-between px-4 py-2.5 text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  {{ __('Primary Address Details') }}
                  <ChevronDown :size="14" class="transition-transform" :class="showAddressSection ? 'rotate-180' : ''" />
                </button>
                <div v-show="showAddressSection" class="px-4 pb-3 space-y-3">
                  <div>
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Address Line 1') }}</label>
                    <input v-model="quickEntryForm.address_line1" type="text" :placeholder="__('Address Line 1')" class="qe-input" />
                  </div>
                  <div>
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Address Line 2') }}</label>
                    <input v-model="quickEntryForm.address_line2" type="text" :placeholder="__('Address Line 2')" class="qe-input" />
                  </div>
                  <div class="grid grid-cols-2 gap-3">
                    <div>
                      <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('ZIP Code') }}</label>
                      <input v-model="quickEntryForm.pincode" type="text" :placeholder="__('ZIP Code')" class="qe-input" />
                    </div>
                    <div>
                      <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('City') }}</label>
                      <input v-model="quickEntryForm.city" type="text" :placeholder="__('City')" class="qe-input" />
                    </div>
                  </div>
                  <div>
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('State') }}</label>
                    <input v-model="quickEntryForm.state" type="text" :placeholder="__('State / Province')" class="qe-input" />
                  </div>
                  <div>
                    <label class="text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-1 block">{{ __('Country') }}</label>
                    <select v-model="quickEntryForm.country" class="qe-input">
                      <option value="">{{ __('Select Country') }}</option>
                      <option v-for="c in quickEntryOptions?.countries || []" :key="c" :value="c">{{ c }}</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Actions (sticky at bottom) -->
              <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center gap-2">
                <button
                  type="button"
                  @click="closeQuickEntry"
                  class="flex-1 text-sm font-medium py-2 rounded-md border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  {{ __('Cancel') }}
                </button>
                <button
                  type="submit"
                  :disabled="quickEntrySaving"
                  class="flex-1 text-sm font-bold py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  <Loader2 v-if="quickEntrySaving" :size="14" class="animate-spin" />
                  {{ quickEntrySaving ? __('Creating...') : __('Create') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.dropdown-enter-active {
  transition: all 0.15s ease-out;
}
.dropdown-leave-active {
  transition: all 0.1s ease-in;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
.modal-enter-active {
  transition: all 0.2s ease-out;
}
.modal-leave-active {
  transition: all 0.15s ease-in;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from > div:last-child {
  transform: scale(0.95);
}
.qe-input {
  @apply w-full text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-400 dark:focus:ring-blue-500 focus:border-blue-400 dark:focus:border-blue-500 placeholder-gray-400 dark:placeholder-gray-500;
  color-scheme: light dark;
}
</style>
