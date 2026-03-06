<script setup lang="ts">
import { usePaymentStore } from '@/stores/payment'

defineProps<{
  formatCurrency: (value: number) => string
  countdown: number
}>()

const emit = defineEmits<{
  done: []
}>()

const paymentStore = usePaymentStore()
</script>

<template>
  <div class="flex h-full flex-col items-center justify-center select-none" style="background: #0f172a;">
    <div class="text-center">
      <!-- Animated checkmark -->
      <div class="kiosk-check-ring mx-auto mb-8 flex h-32 w-32 items-center justify-center rounded-full" style="background: rgba(22,163,74,0.15); box-shadow: 0 0 60px rgba(34,197,94,0.2), 0 0 120px rgba(34,197,94,0.08);">
        <svg class="kiosk-check-icon h-16 w-16" style="color: #4ade80;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
        </svg>
      </div>

      <!-- Thank you -->
      <h1 class="mb-3 text-5xl font-bold text-white" style="letter-spacing: -0.03em;">Thank You!</h1>
      <p class="mb-2 text-lg" style="color: rgba(255,255,255,0.4);">Your payment was successful</p>

      <!-- Amount paid -->
      <p v-if="paymentStore.lastInvoice" class="mb-1 text-sm" style="color: rgba(255,255,255,0.3);">
        Amount paid
      </p>
      <p v-if="paymentStore.lastInvoice" class="mb-10 text-3xl font-bold text-white">
        {{ formatCurrency(paymentStore.lastInvoice.grand_total) }}
      </p>
      <div v-else class="mb-10" />

      <!-- Invoice reference -->
      <p v-if="paymentStore.lastInvoice" class="mb-8 text-sm" style="color: rgba(255,255,255,0.25);">
        Invoice {{ paymentStore.lastInvoice.name }}
      </p>

      <!-- Countdown -->
      <div class="mb-8 flex items-center justify-center gap-3">
        <div class="h-1.5 w-32 overflow-hidden rounded-full" style="background: rgba(255,255,255,0.08);">
          <div
            class="h-full rounded-full transition-all duration-1000 ease-linear"
            :style="{ width: (countdown / 8 * 100) + '%', background: '#4ade80' }"
          />
        </div>
        <span class="text-sm" style="color: rgba(255,255,255,0.3);">{{ countdown }}s</span>
      </div>

      <!-- Done button -->
      <button
        class="rounded-2xl px-14 py-5 text-lg font-bold text-white active:scale-95"
        style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.1);"
        @click="emit('done')"
      >
        Start New Order
      </button>
    </div>
  </div>
</template>

<style scoped>
.kiosk-check-ring {
  animation: kiosk-ring-in 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.kiosk-check-icon {
  animation: kiosk-check-draw 0.4s ease-out 0.3s both;
}

@keyframes kiosk-ring-in {
  0% { transform: scale(0); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes kiosk-check-draw {
  0% { transform: scale(0) rotate(-45deg); opacity: 0; }
  100% { transform: scale(1) rotate(0deg); opacity: 1; }
}
</style>
