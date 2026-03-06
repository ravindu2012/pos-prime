<script setup lang="ts">
import { useCartStore } from '@/stores/cart'

const props = defineProps<{
  formatCurrency: (value: number) => string
}>()

const emit = defineEmits<{
  pay: []
  'add-more': []
  cancel: []
}>()

const cartStore = useCartStore()

function incrementQty(index: number) {
  cartStore.updateQty(index, cartStore.items[index].qty + 1)
}

function decrementQty(index: number) {
  const item = cartStore.items[index]
  if (item.qty <= 1) {
    cartStore.removeItem(index)
  } else {
    cartStore.updateQty(index, item.qty - 1)
  }
}

function removeItem(index: number) {
  cartStore.removeItem(index)
}
</script>

<template>
  <div class="flex h-full flex-col select-none" style="background: #0f172a;">
    <!-- Header -->
    <div class="px-6 py-5" style="background: #1e293b; border-bottom: 1px solid rgba(255,255,255,0.06);">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-white">Review Order</h1>
          <p class="text-sm" style="color: rgba(255,255,255,0.4);">
            {{ cartStore.totalItems }} item{{ cartStore.totalItems !== 1 ? 's' : '' }}
          </p>
        </div>
        <!-- Step indicator -->
        <div class="flex items-center gap-2">
          <div class="h-2 w-8 rounded-full" style="background: #16a34a;" />
          <div class="h-2 w-8 rounded-full" style="background: #16a34a;" />
          <div class="h-2 w-8 rounded-full" style="background: rgba(255,255,255,0.15);" />
        </div>
      </div>
    </div>

    <!-- Items list -->
    <div class="flex-1 overflow-y-auto px-6 py-5">
      <div v-if="cartStore.items.length === 0" class="flex h-full items-center justify-center">
        <div class="text-center">
          <p class="text-xl" style="color: rgba(255,255,255,0.3);">Your cart is empty</p>
          <button
            class="mt-6 rounded-xl px-10 py-4 font-bold text-white active:scale-95"
            style="background: #16a34a;"
            @click="emit('add-more')"
          >
            Add Items
          </button>
        </div>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(item, index) in cartStore.items"
          :key="item.item_code + '-' + index"
          class="flex items-center gap-5 rounded-2xl p-5"
          style="background: #1e293b; border: 1px solid rgba(255,255,255,0.04);"
        >
          <!-- Thumbnail -->
          <div class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl" style="background: #0f172a;">
            <img
              v-if="item.image"
              :src="item.image"
              :alt="item.item_name"
              class="h-full w-full object-cover"
            />
            <svg v-else class="h-7 w-7" style="color: rgba(255,255,255,0.1);" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
              <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
            </svg>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="text-lg font-semibold text-white truncate">{{ item.item_name }}</p>
            <p class="text-sm" style="color: rgba(255,255,255,0.35);">{{ formatCurrency(item.rate) }} each</p>
          </div>

          <!-- Qty controls -->
          <div class="flex items-center gap-3">
            <button
              class="flex h-12 w-12 items-center justify-center rounded-full text-xl font-bold text-white active:scale-90"
              style="background: rgba(255,255,255,0.08);"
              @click="decrementQty(index)"
            >&minus;</button>
            <span class="w-10 text-center text-xl font-bold text-white">{{ item.qty }}</span>
            <button
              class="flex h-12 w-12 items-center justify-center rounded-full text-xl font-bold text-white active:scale-90"
              style="background: rgba(255,255,255,0.08);"
              @click="incrementQty(index)"
            >+</button>
          </div>

          <!-- Line total -->
          <p class="w-28 text-right text-xl font-bold text-white">{{ formatCurrency(item.amount) }}</p>

          <!-- Remove -->
          <button
            class="flex h-11 w-11 items-center justify-center rounded-xl active:scale-90"
            style="background: rgba(248,113,113,0.1);"
            @click="removeItem(index)"
          >
            <svg class="h-5 w-5" style="color: #f87171;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom: totals + actions -->
    <div class="px-6 pb-6 pt-4" style="background: #1e293b; border-top: 1px solid rgba(255,255,255,0.06);">
      <div class="mx-auto max-w-2xl">
        <!-- Totals -->
        <div class="mb-5 space-y-2">
          <div class="flex justify-between text-base" style="color: rgba(255,255,255,0.4);">
            <span>Subtotal</span>
            <span class="text-white/70">{{ formatCurrency(cartStore.subtotal) }}</span>
          </div>
          <div v-if="cartStore.taxAmount > 0" class="flex justify-between text-base" style="color: rgba(255,255,255,0.4);">
            <span>Tax</span>
            <span class="text-white/70">{{ formatCurrency(cartStore.taxAmount) }}</span>
          </div>
          <div class="flex justify-between border-t pt-3" style="border-color: rgba(255,255,255,0.08);">
            <span class="text-xl font-semibold text-white">Total</span>
            <span class="text-3xl font-bold text-white">{{ formatCurrency(cartStore.roundedTotal ?? cartStore.grandTotal) }}</span>
          </div>
        </div>

        <!-- Actions -->
        <button
          class="w-full rounded-2xl py-5 text-xl font-bold text-white shadow-lg active:scale-[0.98] disabled:opacity-30"
          style="background: #16a34a; box-shadow: 0 4px 24px rgba(22,163,74,0.4);"
          :disabled="cartStore.items.length === 0"
          @click="emit('pay')"
        >
          Proceed to Payment
        </button>
        <div class="mt-3 flex justify-between">
          <button
            class="py-2 text-base font-medium active:opacity-70"
            style="color: rgba(255,255,255,0.4);"
            @click="emit('add-more')"
          >
            &larr; Add More Items
          </button>
          <button
            class="py-2 text-base active:opacity-70"
            style="color: rgba(255,255,255,0.25);"
            @click="emit('cancel')"
          >
            Cancel Order
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
