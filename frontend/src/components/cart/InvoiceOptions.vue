<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useCartStore } from '@/stores/cart'
import { useCustomerStore } from '@/stores/customer'
import { useSettingsStore } from '@/stores/settings'
import { usePosSessionStore } from '@/stores/posSession'
import { call } from 'frappe-ui'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

const cartStore = useCartStore()
const customerStore = useCustomerStore()
const settingsStore = useSettingsStore()
const sessionStore = usePosSessionStore()

const expanded = ref(false)

// Link targets
const salesPartners = ref<string[]>([])
const projects = ref<string[]>([])
const shippingRules = ref<string[]>([])
const termsTemplates = ref<string[]>([])
const paymentTermsTemplates = ref<string[]>([])

// Local form state synced to cart store
const form = computed({
  get: () => cartStore.invoiceOptions,
  set: (val) => cartStore.setInvoiceOptions(val),
})

function update(field: string, value: any) {
  cartStore.setInvoiceOptions({ [field]: value || null })
}

onMounted(async () => {
  // Fetch link options in parallel
  try {
    const data = await call('pos_prime.api.pos_session.get_invoice_option_lists')
    if (data) {
      salesPartners.value = (data.sales_partners || []).map((r: any) => r.name)
      projects.value = (data.projects || []).map((r: any) => r.name)
      shippingRules.value = (data.shipping_rules || []).map((r: any) => r.name)
      termsTemplates.value = (data.terms_and_conditions || []).map((r: any) => r.name)
      paymentTermsTemplates.value = (data.payment_terms_templates || []).map((r: any) => r.name)
    }
  } catch {
    // ignore
  }

  // Pre-fill defaults from POS Profile (only if not already set, e.g. from a resumed draft)
  const profile = settingsStore.posProfile
  if (profile) {
    const defaults: Record<string, any> = {}
    if (profile.tc_name && !form.value.tc_name) defaults.tc_name = profile.tc_name
    if (profile.project && !form.value.project) defaults.project = profile.project
    if (profile.letter_head && !form.value.letter_head) defaults.letter_head = profile.letter_head
    if (profile.select_print_heading && !form.value.select_print_heading) defaults.select_print_heading = profile.select_print_heading
    if (Object.keys(defaults).length > 0) {
      cartStore.setInvoiceOptions(defaults)
    }
  }
})

// Address options from customer store
const billingAddresses = computed(() =>
  customerStore.addresses.map((a) => ({ value: a.name, label: `${a.address_title} (${a.address_type})` }))
)
const shippingAddresses = computed(() =>
  customerStore.addresses
    .filter((a) => a.is_shipping_address || a.address_type === 'Shipping')
    .map((a) => ({ value: a.name, label: `${a.address_title} (${a.address_type})` }))
)
const contactOptions = computed(() =>
  customerStore.contacts.map((c) => ({ value: c.name, label: c.full_name || c.name }))
)

// Sync customer store selections into invoice options
watch(() => customerStore.selectedAddress, (val) => update('customer_address', val))
watch(() => customerStore.selectedShippingAddress, (val) => update('shipping_address_name', val))
watch(() => customerStore.selectedContact, (val) => update('contact_person', val))

const hasAnyOption = computed(() => {
  const o = form.value
  return !!(o.sales_partner || o.project || o.remarks || o.po_no || o.shipping_rule
    || o.customer_address || o.shipping_address_name || o.contact_person
    || o.set_posting_time || o.payment_terms_template || o.tc_name)
})

const selectClass = "w-full text-xs border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
const inputClass = "w-full text-xs border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
</script>

<template>
  <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
    <button
      @click="expanded = !expanded"
      class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
    >
      <span>
        {{ __('More Options') }}
        <span v-if="hasAnyOption && !expanded" class="ml-1 text-blue-500 dark:text-blue-400">({{ __('configured') }})</span>
      </span>
      <component :is="expanded ? ChevronUp : ChevronDown" :size="14" />
    </button>

    <div v-if="expanded" class="px-3 pb-3 space-y-2.5 border-t border-gray-100 dark:border-gray-800">
      <!-- Address & Contact -->
      <div v-if="customerStore.customer && customerStore.addresses.length > 0" class="space-y-2 pt-2">
        <div class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase">{{ __('Address & Contact') }}</div>
        <div v-if="billingAddresses.length > 0">
          <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Billing Address') }}</label>
          <select
            :value="customerStore.selectedAddress || ''"
            @change="customerStore.setSelectedAddress(($event.target as HTMLSelectElement).value || null)"
            :class="selectClass"
          >
            <option value="">{{ __('None') }}</option>
            <option v-for="a in billingAddresses" :key="a.value" :value="a.value">{{ a.label }}</option>
          </select>
        </div>
        <div v-if="shippingAddresses.length > 0">
          <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Shipping Address') }}</label>
          <select
            :value="customerStore.selectedShippingAddress || ''"
            @change="customerStore.setSelectedShippingAddress(($event.target as HTMLSelectElement).value || null)"
            :class="selectClass"
          >
            <option value="">{{ __('None') }}</option>
            <option v-for="a in shippingAddresses" :key="a.value" :value="a.value">{{ a.label }}</option>
          </select>
        </div>
        <div v-if="contactOptions.length > 0">
          <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Contact Person') }}</label>
          <select
            :value="customerStore.selectedContact || ''"
            @change="customerStore.setSelectedContact(($event.target as HTMLSelectElement).value || null)"
            :class="selectClass"
          >
            <option value="">{{ __('None') }}</option>
            <option v-for="c in contactOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>
      </div>

      <!-- Sales Partner -->
      <div v-if="salesPartners.length > 0" class="pt-2">
        <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Sales Partner') }}</label>
        <select
          :value="form.sales_partner || ''"
          @change="update('sales_partner', ($event.target as HTMLSelectElement).value)"
          :class="selectClass"
        >
          <option value="">None</option>
          <option v-for="sp in salesPartners" :key="sp" :value="sp">{{ sp }}</option>
        </select>
      </div>

      <!-- Project -->
      <div v-if="projects.length > 0">
        <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Project') }}</label>
        <select
          :value="form.project || ''"
          @change="update('project', ($event.target as HTMLSelectElement).value)"
          :class="selectClass"
        >
          <option value="">None</option>
          <option v-for="p in projects" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>

      <!-- Customer PO -->
      <div class="grid grid-cols-2 gap-2 pt-2">
        <div>
          <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Customer PO #') }}</label>
          <input
            :value="form.po_no || ''"
            @input="update('po_no', ($event.target as HTMLInputElement).value)"
            type="text"
            :placeholder="__('PO Number')"
            :class="inputClass"
          />
        </div>
        <div>
          <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('PO Date') }}</label>
          <input
            :value="form.po_date || ''"
            @input="update('po_date', ($event.target as HTMLInputElement).value)"
            type="date"
            :class="inputClass"
          />
        </div>
      </div>

      <!-- Posting Date Override -->
      <div class="pt-2">
        <div class="flex items-center gap-2">
          <input
            type="checkbox"
            :checked="form.set_posting_time || false"
            @change="update('set_posting_time', ($event.target as HTMLInputElement).checked)"
            id="set-posting-time"
            class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
          />
          <label for="set-posting-time" class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Override Posting Date/Time') }}</label>
        </div>
        <div v-if="form.set_posting_time" class="grid grid-cols-2 gap-2 mt-1.5">
          <div>
            <input
              :value="form.posting_date || ''"
              @input="update('posting_date', ($event.target as HTMLInputElement).value)"
              type="date"
              :class="inputClass"
            />
          </div>
          <div>
            <input
              :value="form.posting_time || ''"
              @input="update('posting_time', ($event.target as HTMLInputElement).value)"
              type="time"
              step="1"
              :class="inputClass"
            />
          </div>
        </div>
      </div>

      <!-- Shipping Rule -->
      <div v-if="shippingRules.length > 0">
        <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Shipping Rule') }}</label>
        <select
          :value="form.shipping_rule || ''"
          @change="update('shipping_rule', ($event.target as HTMLSelectElement).value)"
          :class="selectClass"
        >
          <option value="">None</option>
          <option v-for="sr in shippingRules" :key="sr" :value="sr">{{ sr }}</option>
        </select>
      </div>

      <!-- Payment Terms Template -->
      <div v-if="paymentTermsTemplates.length > 0">
        <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Payment Terms') }}</label>
        <select
          :value="form.payment_terms_template || ''"
          @change="update('payment_terms_template', ($event.target as HTMLSelectElement).value)"
          :class="selectClass"
        >
          <option value="">None</option>
          <option v-for="pt in paymentTermsTemplates" :key="pt" :value="pt">{{ pt }}</option>
        </select>
      </div>

      <!-- Terms & Conditions -->
      <div v-if="termsTemplates.length > 0">
        <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Terms & Conditions') }}</label>
        <select
          :value="form.tc_name || ''"
          @change="update('tc_name', ($event.target as HTMLSelectElement).value)"
          :class="selectClass"
        >
          <option value="">None</option>
          <option v-for="tc in termsTemplates" :key="tc" :value="tc">{{ tc }}</option>
        </select>
      </div>

      <!-- Remarks -->
      <div>
        <label class="text-[10px] text-gray-500 dark:text-gray-400">{{ __('Remarks') }}</label>
        <textarea
          :value="form.remarks || ''"
          @input="update('remarks', ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          :placeholder="__('Internal notes...')"
          class="w-full text-xs border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none placeholder-gray-400 dark:placeholder-gray-500"
        />
      </div>
    </div>
  </div>
</template>
