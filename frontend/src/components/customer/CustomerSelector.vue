<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useCustomerStore } from '@/stores/customer'
import { usePosSessionStore } from '@/stores/posSession'
import NewCustomerDialog from './NewCustomerDialog.vue'
import { User, X, Plus, Search, Phone, Tag } from 'lucide-vue-next'

const customerStore = useCustomerStore()
const sessionStore = usePosSessionStore()
const searchTerm = ref('')
const results = ref<{ name: string; customer_name: string; mobile_no?: string; email_id?: string }[]>([])
const showDropdown = ref(false)
const showNewDialog = ref(false)
let debounceTimer: ReturnType<typeof setTimeout>

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

function onNewCustomerCreated() {
  showNewDialog.value = false
}
</script>

<template>
  <div class="relative">
    <!-- Selected customer display -->
    <div v-if="customerStore.customer" class="flex items-center gap-2.5 bg-gradient-to-r from-blue-50 to-violet-50 dark:from-blue-900/20 dark:to-violet-900/20 rounded-xl px-3 py-2.5 border border-blue-100 dark:border-blue-800">
      <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center shrink-0">
        <User :size="14" class="text-blue-600 dark:text-blue-400" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate">
          {{ customerStore.customer.customer_name }}
        </div>
        <div class="flex items-center gap-1.5 flex-wrap mt-0.5">
          <span v-if="customerStore.customer.mobile_no" class="text-[10px] text-gray-500 dark:text-gray-400 flex items-center gap-0.5">
            <Phone :size="8" />
            {{ customerStore.customer.mobile_no }}
          </span>
          <span v-if="customerStore.customer.customer_group" class="text-[10px] text-gray-400 dark:text-gray-500">
            {{ customerStore.customer.mobile_no ? '·' : '' }} {{ customerStore.customer.customer_group }}
          </span>
          <span
            v-if="customerStore.loyaltyPoints > 0"
            class="inline-flex items-center gap-0.5 px-1.5 py-0 bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400 rounded-md text-[9px] font-bold"
          >
            <Tag :size="8" />
            {{ customerStore.loyaltyPoints }} pts
          </span>
        </div>
      </div>
      <button
        @click="clearCustomer"
        class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
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
          :placeholder="__('Search customer...')"
          aria-label="Search customer"
          class="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:bg-white dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 pl-8 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 focus:bg-white dark:focus:bg-gray-700 transition-all duration-200 placeholder-gray-400 dark:placeholder-gray-500"
          @focus="showDropdown = results.length > 0"
        />
        <button
          @click="showNewDialog = true"
          class="absolute right-2 w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
          title="New Customer"
          aria-label="New Customer"
        >
          <Plus :size="16" />
        </button>
      </div>

      <!-- Dropdown -->
      <Transition name="dropdown">
        <div
          v-if="showDropdown"
          class="absolute z-20 left-0 right-0 mt-1.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl dark:shadow-black/30 max-h-48 overflow-y-auto"
        >
          <button
            v-for="c in results"
            :key="c.name"
            @click="selectCustomer(c.name)"
            class="w-full text-left px-3 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors first:rounded-t-xl last:rounded-b-xl"
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

    <NewCustomerDialog
      v-if="showNewDialog"
      @close="showNewDialog = false"
      @created="onNewCustomerCreated"
    />
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
</style>
