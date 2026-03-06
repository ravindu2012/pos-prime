<script setup lang="ts">
defineProps<{
  companyName: string
  companyLogo: string
}>()

const emit = defineEmits<{
  start: []
}>()
</script>

<template>
  <div
    class="kiosk-welcome flex h-full flex-col items-center justify-center select-none"
    @click="emit('start')"
  >
    <!-- Background glow effect -->
    <div class="kiosk-welcome-glow" />

    <!-- Content -->
    <div class="relative z-10 flex flex-col items-center">
      <!-- Company logo -->
      <div class="mb-10">
        <img
          v-if="companyLogo"
          :src="companyLogo"
          :alt="companyName"
          class="mx-auto h-28 max-w-[320px] object-contain drop-shadow-lg"
        />
        <div
          v-else
          class="flex h-28 w-28 items-center justify-center rounded-3xl shadow-lg"
          style="background: rgba(255,255,255,0.1); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15);"
        >
          <svg class="h-14 w-14 text-white/80" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016c.896 0 1.7-.393 2.25-1.015a3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72M6.75 18h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a.75.75 0 0 0-.75.75v3.75c0 .414.336.75.75.75Z" />
          </svg>
        </div>
      </div>

      <!-- Self-Checkout label -->
      <p class="mb-2 text-lg font-medium tracking-widest uppercase" style="color: rgba(255,255,255,0.4);">
        Self-Checkout
      </p>

      <!-- Company name -->
      <h1 class="mb-16 text-center text-4xl font-bold text-white" style="letter-spacing: -0.02em;">
        {{ companyName }}
      </h1>

      <!-- Pulsing start button -->
      <button
        class="kiosk-pulse-btn flex items-center gap-4 rounded-2xl px-16 py-7 text-2xl font-bold text-white shadow-2xl active:scale-95"
        style="background: #16a34a; box-shadow: 0 0 40px rgba(22,163,74,0.4), 0 8px 32px rgba(0,0,0,0.3);"
        @click.stop="emit('start')"
      >
        <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007ZM8.625 10.5a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm7.5 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
        </svg>
        Touch to Start
      </button>

      <!-- Hint -->
      <p class="mt-8 text-lg" style="color: rgba(255,255,255,0.35);">
        or scan a barcode to begin
      </p>
    </div>
  </div>
</template>

<style scoped>
.kiosk-welcome {
  background: #0f172a;
  position: relative;
  overflow: hidden;
}

.kiosk-welcome-glow {
  position: absolute;
  top: 30%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(22,163,74,0.12) 0%, transparent 70%);
  pointer-events: none;
}

.kiosk-pulse-btn {
  animation: kiosk-pulse 2.5s ease-in-out infinite;
}

@keyframes kiosk-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}

.kiosk-pulse-btn:active {
  animation: none;
}
</style>
