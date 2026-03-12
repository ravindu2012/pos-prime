<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { useCartStore } from '@/stores/cart'

const props = defineProps<{
  formatCurrency: (value: number) => string
  cashAvailable: boolean
  error: string | null
}>()

const emit = defineEmits<{
  'pay-card': []
  'pay-cash': []
  back: []
}>()

const cartStore = useCartStore()
</script>

<template>
  <div class="flex h-full flex-col items-center justify-center select-none" style="background: #0f172a;">
    <!-- Step indicator -->
    <div class="absolute right-6 top-6 flex items-center gap-2">
      <div class="h-2 w-8 rounded-full" style="background: #16a34a;" />
      <div class="h-2 w-8 rounded-full" style="background: #16a34a;" />
      <div class="h-2 w-8 rounded-full" style="background: #16a34a;" />
    </div>

    <div class="w-full max-w-lg px-8 text-center">
      <!-- Amount -->
      <p class="mb-3 text-lg font-medium" style="color: rgba(255,255,255,0.4);">Total Amount</p>
      <p class="text-6xl font-bold text-white" style="letter-spacing: -0.03em;">
        {{ formatCurrency(cartStore.roundedTotal ?? cartStore.grandTotal) }}
      </p>
      <!-- Discount summary -->
      <div v-if="cartStore.pricingRuleDiscount || cartStore.items.some(i => i.is_free_item)" class="mt-3 mb-14 flex items-center justify-center gap-3 flex-wrap">
        <span v-if="cartStore.pricingRuleDiscount" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold" style="background: rgba(96,165,250,0.12); color: #60a5fa;">
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
          {{ cartStore.pricingRuleDiscount.type === 'percentage' ? cartStore.pricingRuleDiscount.value + '% discount applied' : 'Discount applied' }}
        </span>
        <span v-if="cartStore.items.some(i => i.is_free_item)" class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold" style="background: rgba(22,163,74,0.12); color: #4ade80;">
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
          Free items included
        </span>
      </div>
      <div v-else class="mb-14" />

      <!-- Error message -->
      <div
        v-if="error"
        class="mb-6 rounded-2xl px-5 py-4 text-left"
        style="background: rgba(248,113,113,0.12); border: 1px solid rgba(248,113,113,0.2);"
      >
        <div class="flex items-start gap-3">
          <svg class="mt-0.5 h-5 w-5 shrink-0" style="color: #f87171;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
          <p class="text-sm font-medium" style="color: #f87171;">{{ error }}</p>
        </div>
      </div>

      <!-- Payment method label -->
      <p class="mb-6 text-base font-medium" style="color: rgba(255,255,255,0.35);">How would you like to pay?</p>

      <!-- Payment buttons -->
      <div class="space-y-4">
        <!-- Pay by Card -->
        <button
          class="flex w-full items-center gap-5 rounded-2xl p-6 text-left transition-transform active:scale-[0.97]"
          style="background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); box-shadow: 0 4px 24px rgba(37,99,235,0.3);"
          @click="emit('pay-card')"
        >
          <div class="flex h-14 w-14 items-center justify-center rounded-xl" style="background: rgba(255,255,255,0.15);">
            <svg class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" />
            </svg>
          </div>
          <div>
            <p class="text-xl font-bold text-white">Pay by Card</p>
            <p class="text-sm text-white/50">Tap, insert, or swipe</p>
          </div>
          <svg class="ml-auto h-6 w-6 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </button>

        <!-- Pay by Cash -->
        <button
          v-if="cashAvailable"
          class="flex w-full items-center gap-5 rounded-2xl p-6 text-left transition-transform active:scale-[0.97]"
          style="background: linear-gradient(135deg, #15803d 0%, #16a34a 100%); box-shadow: 0 4px 24px rgba(22,163,74,0.3);"
          @click="emit('pay-cash')"
        >
          <div class="flex h-14 w-14 items-center justify-center rounded-xl" style="background: rgba(255,255,255,0.15);">
            <svg class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
            </svg>
          </div>
          <div>
            <p class="text-xl font-bold text-white">Pay by Cash</p>
            <p class="text-sm text-white/50">Pay at the counter</p>
          </div>
          <svg class="ml-auto h-6 w-6 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </button>
      </div>

      <!-- Back link -->
      <button
        class="mt-10 py-3 text-base font-medium active:opacity-70"
        style="color: rgba(255,255,255,0.3);"
        @click="emit('back')"
      >
        &larr; Back to Order
      </button>
    </div>
  </div>
</template>
