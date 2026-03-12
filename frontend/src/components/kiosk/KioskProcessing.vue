<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { useCartStore } from '@/stores/cart'
import type { TerminalStatus } from '@/composables/usePaymentTerminal'

defineProps<{
  formatCurrency: (value: number) => string
  terminalStatus: TerminalStatus
}>()

const emit = defineEmits<{
  cancel: []
}>()

const cartStore = useCartStore()
</script>

<template>
  <div class="flex h-full flex-col items-center justify-center select-none" style="background: #0f172a;">
    <div class="text-center">
      <!-- Animated card tap illustration -->
      <div class="kiosk-card-tap mx-auto mb-10 flex h-32 w-32 items-center justify-center rounded-3xl" style="background: rgba(37,99,235,0.1); border: 1px solid rgba(37,99,235,0.2);">
        <svg class="h-16 w-16" style="color: #60a5fa;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" />
        </svg>
      </div>

      <!-- Status -->
      <h2 class="mb-3 text-3xl font-bold text-white">Processing Payment</h2>
      <p class="mb-8 text-lg" style="color: rgba(255,255,255,0.4);">
        Follow the instructions on the card reader
      </p>

      <!-- Amount -->
      <p class="mb-12 text-5xl font-bold text-white" style="letter-spacing: -0.03em;">
        {{ formatCurrency(cartStore.roundedTotal ?? cartStore.grandTotal) }}
      </p>

      <!-- Loading dots -->
      <div class="mb-10 flex items-center justify-center gap-2">
        <div class="kiosk-dot h-3 w-3 rounded-full" style="background: #60a5fa; animation-delay: 0s;" />
        <div class="kiosk-dot h-3 w-3 rounded-full" style="background: #60a5fa; animation-delay: 0.2s;" />
        <div class="kiosk-dot h-3 w-3 rounded-full" style="background: #60a5fa; animation-delay: 0.4s;" />
      </div>

      <!-- Cancel -->
      <button
        class="rounded-xl px-8 py-3 text-base font-medium active:scale-95"
        style="background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.4); border: 1px solid rgba(255,255,255,0.08);"
        @click="emit('cancel')"
      >
        Cancel Payment
      </button>
    </div>
  </div>
</template>

<style scoped>
.kiosk-card-tap {
  animation: kiosk-float 3s ease-in-out infinite;
}

@keyframes kiosk-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.kiosk-dot {
  animation: kiosk-bounce 1.2s ease-in-out infinite;
}

@keyframes kiosk-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
