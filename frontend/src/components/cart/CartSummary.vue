<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { useCartStore } from '@/stores/cart'
import { useCurrency } from '@/composables/useCurrency'
import { computed } from 'vue'
import { Loader2, Zap } from 'lucide-vue-next'

const cartStore = useCartStore()
const { formatCurrency } = useCurrency()

const totalWeight = computed(() =>
  cartStore.items.reduce((sum, item) => {
    if (item.weight_per_unit) return sum + item.weight_per_unit * item.qty
    return sum
  }, 0)
)

const weightUom = computed(() => {
  const item = cartStore.items.find((i) => i.weight_uom)
  return item?.weight_uom || ''
})
</script>

<template>
  <div class="space-y-1">
    <!-- Item qty total (ERPNext-style) -->
    <div class="flex justify-between items-center text-gray-600 dark:text-gray-400 text-sm font-medium py-0.5">
      <span>{{ __('Total Qty') }}</span>
      <span>{{ cartStore.totalItems }}</span>
    </div>

    <!-- Net Total -->
    <div class="flex justify-between items-center text-gray-600 dark:text-gray-400 text-sm font-medium py-0.5">
      <span>{{ __('Net Total') }}</span>
      <span>{{ formatCurrency(cartStore.subtotal) }}</span>
    </div>

    <!-- Manual discount -->
    <div v-if="cartStore.additionalDiscountPercentage > 0 && !cartStore.pricingRuleDiscount" class="flex justify-between text-orange-600 dark:text-orange-400 text-sm font-medium py-0.5">
      <span class="flex items-center gap-1">
        {{ __('Discount') }}
        <span class="px-1 py-0 bg-orange-100 dark:bg-orange-900/30 rounded text-[10px] font-semibold">{{ cartStore.additionalDiscountPercentage }}%</span>
      </span>
      <span class="font-semibold">-{{ formatCurrency(cartStore.subtotal - cartStore.netTotal) }}</span>
    </div>
    <div v-else-if="cartStore.additionalDiscountAmount > 0 && !cartStore.pricingRuleDiscount" class="flex justify-between text-orange-600 dark:text-orange-400 text-sm font-medium py-0.5">
      <span>{{ __('Discount') }}</span>
      <span class="font-semibold">-{{ formatCurrency(cartStore.additionalDiscountAmount) }}</span>
    </div>

    <!-- Pricing rule transaction discount -->
    <div v-if="cartStore.pricingRuleDiscount" class="flex justify-between text-blue-600 dark:text-blue-400 text-sm font-medium py-0.5">
      <span class="flex items-center gap-1">
        <Zap :size="10" />
        {{ __('Promo Discount') }}
        <span v-if="cartStore.pricingRuleDiscount.type === 'percentage'" class="px-1 py-0 bg-blue-100 dark:bg-blue-900/30 rounded text-[10px] font-semibold">{{ cartStore.pricingRuleDiscount.value }}%</span>
      </span>
      <span class="font-semibold">-{{ formatCurrency(cartStore.subtotal - cartStore.netTotal) }}</span>
    </div>

    <!-- Individual tax rows -->
    <div
      v-for="tax in cartStore.taxes"
      :key="tax.account_head"
      class="flex justify-between text-gray-500 dark:text-gray-400 text-sm font-medium py-0.5"
    >
      <span>{{ tax.description || tax.account_head }}</span>
      <span>{{ formatCurrency(tax.tax_amount) }}</span>
    </div>

    <!-- Fallback tax -->
    <div v-if="cartStore.taxes.length === 0 && cartStore.taxAmount > 0" class="flex justify-between text-gray-500 dark:text-gray-400 text-sm font-medium py-0.5">
      <span>{{ __('Tax') }}</span>
      <span>{{ formatCurrency(cartStore.taxAmount) }}</span>
    </div>

    <!-- Tax calculating -->
    <div v-if="cartStore.taxCalculating" class="flex items-center justify-end gap-1 text-xs text-gray-400 dark:text-gray-500">
      <Loader2 :size="10" class="animate-spin" />
      <span>{{ __('Calculating...') }}</span>
    </div>

    <!-- Grand Total (ERPNext-style: bold, larger) -->
    <div class="flex justify-between items-center font-bold text-gray-900 dark:text-gray-100 pt-2 mt-1 border-t border-gray-200 dark:border-gray-700">
      <span class="text-base">{{ __('Grand Total') }}</span>
      <span class="text-lg">{{ formatCurrency(cartStore.grandTotal) }}</span>
    </div>

    <!-- Rounding + Rounded Total -->
    <template v-if="cartStore.serverRoundingAdjustment !== 0">
      <div class="flex justify-between text-[10px] text-gray-400 dark:text-gray-500">
        <span>{{ __('Rounding') }}</span>
        <span>{{ formatCurrency(cartStore.serverRoundingAdjustment) }}</span>
      </div>
      <div class="flex justify-between items-center font-bold text-gray-900 dark:text-gray-100">
        <span class="text-sm">{{ __('Rounded Total') }}</span>
        <span class="text-lg">{{ formatCurrency(cartStore.roundedTotal) }}</span>
      </div>
    </template>

    <!-- Weight -->
    <div v-if="totalWeight > 0" class="flex justify-between text-[10px] text-gray-400 dark:text-gray-500">
      <span>{{ __('Total Weight') }}</span>
      <span>{{ totalWeight.toFixed(2) }} {{ weightUom }}</span>
    </div>
  </div>
</template>
