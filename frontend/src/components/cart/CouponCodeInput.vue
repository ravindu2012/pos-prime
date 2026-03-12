<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref } from 'vue'
import { call } from 'frappe-ui'
import { useCartStore } from '@/stores/cart'
import { useCustomerStore } from '@/stores/customer'
import { Tag, X, Check, Loader2 } from 'lucide-vue-next'

const cartStore = useCartStore()
const customerStore = useCustomerStore()
const input = ref('')
const applying = ref(false)
const error = ref('')
const displayCode = ref('')

async function applyCoupon() {
  const code = input.value.trim()
  if (!code) return
  error.value = ''
  applying.value = true
  try {
    const result = await call('pos_prime.api.taxes.validate_coupon_code', {
      coupon_code: code,
      customer: customerStore.customer?.name || undefined,
    })
    // ERPNext expects the document name, not the coupon_code field
    cartStore.setCouponCode(result.name)
    displayCode.value = result.coupon_code || code
    input.value = ''
  } catch (e: any) {
    const msg = e?.messages?.[0] || e?.message || e?.exc || ''
    let parsed = msg
    try {
      const arr = JSON.parse(msg)
      if (Array.isArray(arr) && arr.length) parsed = arr[0]
    } catch { /* not JSON */ }
    parsed = String(parsed).replace(/<[^>]*>/g, '').trim()
    error.value = parsed || __('Invalid coupon code')
  } finally {
    applying.value = false
  }
}

function removeCoupon() {
  cartStore.setCouponCode(null)
  displayCode.value = ''
  error.value = ''
}
</script>

<template>
  <div>
    <!-- Applied coupon -->
    <div v-if="cartStore.couponCode" class="flex items-center gap-2 bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-800 rounded-lg px-3 py-2">
      <div class="w-5 h-5 bg-purple-100 dark:bg-purple-900/40 rounded flex items-center justify-center shrink-0">
        <Tag :size="10" class="text-purple-600 dark:text-purple-400" />
      </div>
      <span class="text-xs font-bold text-purple-700 dark:text-purple-300 flex-1">{{ displayCode || cartStore.couponCode }}</span>
      <button @click="removeCoupon" class="w-5 h-5 rounded flex items-center justify-center text-purple-400 dark:text-purple-500 hover:text-purple-600 dark:hover:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors">
        <X :size="12" />
      </button>
    </div>

    <!-- Coupon input -->
    <div v-else class="flex gap-1.5">
      <div class="relative flex-1">
        <Tag class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-300 dark:text-gray-600 pointer-events-none" :size="11" />
        <input
          v-model="input"
          type="text"
          :placeholder="__('Coupon code...')"
          class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:bg-white dark:hover:bg-gray-700 focus:bg-white dark:focus:bg-gray-700 text-gray-900 dark:text-gray-100 pl-7 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200 placeholder-gray-400 dark:placeholder-gray-500"
          @keydown.enter="applyCoupon"
        />
      </div>
      <button
        @click="applyCoupon"
        :disabled="!input.trim() || applying"
        class="px-3 py-1.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-lg text-xs font-bold hover:bg-purple-100 dark:hover:bg-purple-900/40 disabled:opacity-40 transition-all duration-150 flex items-center gap-1 active:scale-95"
      >
        <Loader2 v-if="applying" :size="10" class="animate-spin" />
        <Check v-else :size="10" />
        {{ __('Apply') }}
      </button>
    </div>
    <div v-if="error" class="text-[10px] text-red-500 dark:text-red-400 mt-1 font-medium">{{ error }}</div>
  </div>
</template>
