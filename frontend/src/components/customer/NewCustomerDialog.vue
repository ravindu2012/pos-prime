<script setup lang="ts">
import { ref } from 'vue'
import { useCustomerStore } from '@/stores/customer'
import { usePosSessionStore } from '@/stores/posSession'
import { X } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
  created: []
}>()

const customerStore = useCustomerStore()
const sessionStore = usePosSessionStore()
const customerName = ref('')
const mobileNo = ref('')
const emailId = ref('')
const loading = ref(false)
const error = ref('')

async function create() {
  if (!customerName.value.trim()) {
    error.value = 'Customer name is required'
    return
  }
  if (customerName.value.trim().length > 140) {
    error.value = 'Customer name must be 140 characters or less'
    return
  }
  if (emailId.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailId.value.trim())) {
    error.value = 'Please enter a valid email address'
    return
  }
  if (mobileNo.value.trim() && !/^[0-9+\-() ]+$/.test(mobileNo.value.trim())) {
    error.value = 'Please enter a valid phone number'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await customerStore.quickCreateCustomer({
      customer_name: customerName.value.trim(),
      mobile_no: mobileNo.value.trim() || undefined,
      email_id: emailId.value.trim() || undefined,
      pos_profile: sessionStore.posProfile || undefined,
    })
    emit('created')
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || 'Failed to create customer'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-label="New Customer">
    <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="emit('close')" />
    <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-xl dark:shadow-black/30 w-full max-w-sm p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">New Customer</h3>
        <button @click="emit('close')" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
          <X :size="18" />
        </button>
      </div>

      <div v-if="error" class="mb-3 p-2 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-xs">
        {{ error }}
      </div>

      <div class="space-y-3">
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Name *</label>
          <input
            v-model="customerName"
            type="text"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            placeholder="Customer name"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Mobile</label>
          <input
            v-model="mobileNo"
            type="tel"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            placeholder="Mobile number"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Email</label>
          <input
            v-model="emailId"
            type="email"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
            placeholder="Email address"
          />
        </div>
        <button
          @click="create"
          :disabled="loading"
          class="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? 'Creating...' : 'Create Customer' }}
        </button>
      </div>
    </div>
  </div>
</template>
