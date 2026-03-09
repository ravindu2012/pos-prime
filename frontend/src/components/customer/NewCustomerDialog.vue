<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
import { useCustomerStore } from '@/stores/customer'
import { usePosSessionStore } from '@/stores/posSession'
import { X } from 'lucide-vue-next'

interface QuickField {
  fieldname: string
  label: string
  fieldtype: string
  options?: string
  reqd: boolean
  default?: string
}

const emit = defineEmits<{
  close: []
  created: []
}>()

const customerStore = useCustomerStore()
const sessionStore = usePosSessionStore()

// Form state
const customerName = ref('')
const mobileNo = ref('')
const emailId = ref('')
const customerType = ref('Individual')
const customerGroup = ref('')
const extraFields = ref<Record<string, string>>({})
const loading = ref(false)
const loadingOptions = ref(true)
const error = ref('')

// Options from backend
const customerTypes = ref<string[]>(['Individual', 'Company'])
const customerGroups = ref<string[]>([])
const quickFields = ref<QuickField[]>([])

onMounted(async () => {
  try {
    const data = await call('pos_prime.api.customers.get_quick_entry_options', {
      pos_profile: sessionStore.posProfile || '',
    })
    customerTypes.value = data.customer_types || ['Individual']
    customerGroups.value = data.customer_groups || []
    customerType.value = data.default_customer_type || 'Individual'
    customerGroup.value = data.default_customer_group || ''

    // Filter out fields we handle explicitly
    const handled = new Set(['customer_name', 'customer_type', 'customer_group', 'territory'])
    quickFields.value = (data.quick_fields || []).filter(
      (f: QuickField) => !handled.has(f.fieldname)
    )
    // Set defaults for extra fields
    for (const f of quickFields.value) {
      if (f.default) extraFields.value[f.fieldname] = f.default
    }
  } catch {
    // Use sensible defaults if API fails
  } finally {
    loadingOptions.value = false
  }
})

async function create() {
  if (!customerName.value.trim()) {
    error.value = __('Customer name is required')
    return
  }
  if (customerName.value.trim().length > 140) {
    error.value = __('Customer name must be 140 characters or less')
    return
  }
  if (emailId.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailId.value.trim())) {
    error.value = __('Please enter a valid email address')
    return
  }
  if (mobileNo.value.trim() && !/^[0-9+\-() ]+$/.test(mobileNo.value.trim())) {
    error.value = __('Please enter a valid phone number')
    return
  }
  // Validate required extra fields
  for (const f of quickFields.value) {
    if (f.reqd && !extraFields.value[f.fieldname]?.trim()) {
      error.value = __('{0} is required', [__(f.label)])
      return
    }
  }

  loading.value = true
  error.value = ''
  try {
    await customerStore.quickCreateCustomer({
      customer_name: customerName.value.trim(),
      mobile_no: mobileNo.value.trim() || undefined,
      email_id: emailId.value.trim() || undefined,
      customer_type: customerType.value || undefined,
      customer_group: customerGroup.value || undefined,
      pos_profile: sessionStore.posProfile || undefined,
      ...extraFields.value,
    })
    emit('created')
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || __('Failed to create customer')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" :aria-label="__('New Customer')" @keydown.escape="emit('close')">
    <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="emit('close')" />
    <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-xl dark:shadow-black/30 w-full max-w-sm p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">{{ __('New Customer') }}</h3>
        <button @click="emit('close')" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
          <X :size="18" />
        </button>
      </div>

      <div v-if="error" class="mb-3 p-2 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-xs">
        {{ error }}
      </div>

      <div v-if="loadingOptions" class="py-8 text-center">
        <span class="text-sm text-gray-400 dark:text-gray-500">{{ __('Loading...') }}</span>
      </div>

      <div v-else class="space-y-3">
        <!-- Customer Name -->
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{{ __('Customer Name') }} *</label>
          <input
            v-model="customerName"
            type="text"
            autofocus
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            :placeholder="__('Customer name')"
            @keydown.enter="create"
          />
        </div>

        <!-- Customer Type -->
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{{ __('Customer Type') }} *</label>
          <select
            v-model="customerType"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="t in customerTypes" :key="t" :value="t">{{ __(t) }}</option>
          </select>
        </div>

        <!-- Customer Group -->
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{{ __('Customer Group') }} *</label>
          <select
            v-model="customerGroup"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="g in customerGroups" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>

        <!-- Dynamic quick_entry fields (e.g. NIC Number) -->
        <div v-for="field in quickFields" :key="field.fieldname">
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            {{ __(field.label) }}{{ field.reqd ? ' *' : '' }}
          </label>
          <select
            v-if="field.fieldtype === 'Select' && field.options"
            v-model="extraFields[field.fieldname]"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">{{ __('Select...') }}</option>
            <option v-for="opt in field.options.split('\n')" :key="opt" :value="opt">{{ __(opt) }}</option>
          </select>
          <input
            v-else
            v-model="extraFields[field.fieldname]"
            :type="field.fieldtype === 'Int' ? 'number' : 'text'"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            :placeholder="__(field.label)"
            @keydown.enter="create"
          />
        </div>

        <!-- Mobile -->
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{{ __('Mobile') }}</label>
          <input
            v-model="mobileNo"
            type="tel"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            :placeholder="__('Mobile number')"
            @keydown.enter="create"
          />
        </div>

        <!-- Email -->
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{{ __('Email') }}</label>
          <input
            v-model="emailId"
            type="email"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            :placeholder="__('Email address')"
            @keydown.enter="create"
          />
        </div>

        <button
          @click="create"
          :disabled="loading"
          class="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? __('Creating...') : __('Create Customer') }}
        </button>
      </div>
    </div>
  </div>
</template>
