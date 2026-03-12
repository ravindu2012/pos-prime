<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  loading: boolean
  error: string | null
  customerName: string | null
  loyaltyPoints: number
}>()

const emit = defineEmits<{
  lookup: [phone: string]
  skip: []
}>()

const phone = ref('')
const matched = computed(() => !!props.customerName)

function onDigit(d: string) {
  if (phone.value.length < 15) {
    phone.value += d
  }
}

function onBackspace() {
  phone.value = phone.value.slice(0, -1)
}

function onClear() {
  phone.value = ''
}

function onLookup() {
  if (phone.value.length >= 3) {
    emit('lookup', phone.value)
  }
}
</script>

<template>
  <div class="flex h-full flex-col items-center justify-center select-none" style="background: #0f172a;">
    <div class="w-full max-w-md px-8">
      <!-- Title -->
      <div class="mb-8 text-center">
        <div class="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl" style="background: rgba(22,163,74,0.1);">
          <svg class="h-8 w-8" style="color: #4ade80;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-white">Enter Your Phone Number</h1>
        <p class="mt-2 text-sm" style="color: rgba(255,255,255,0.35);">Earn & redeem loyalty points</p>
      </div>

      <!-- Phone display -->
      <div
        class="mb-6 flex items-center justify-center rounded-2xl px-6 py-5"
        style="background: #1e293b; border: 1px solid rgba(255,255,255,0.06);"
      >
        <p
          class="text-center text-3xl font-bold tracking-wider"
          :style="phone ? 'color: white;' : 'color: rgba(255,255,255,0.2);'"
        >
          {{ phone || 'Phone Number' }}
        </p>
      </div>

      <!-- Matched customer info -->
      <Transition name="match-fade">
        <div
          v-if="matched"
          class="mb-5 flex items-center gap-4 rounded-2xl px-5 py-5"
          style="background: rgba(22,163,74,0.1); border: 1px solid rgba(22,163,74,0.2);"
        >
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full" style="background: rgba(22,163,74,0.2);">
            <svg class="h-6 w-6" style="color: #4ade80;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-lg font-bold text-white truncate">Welcome, {{ customerName }}!</p>
            <p v-if="loyaltyPoints > 0" class="text-sm" style="color: #4ade80;">
              {{ loyaltyPoints }} loyalty points available
            </p>
          </div>
        </div>
      </Transition>

      <!-- Redirecting indicator when matched -->
      <div v-if="matched" class="mb-5 flex items-center justify-center gap-3">
        <div class="h-5 w-5 animate-spin rounded-full border-2" style="border-color: rgba(255,255,255,0.1); border-top-color: #4ade80;" />
        <p class="text-sm" style="color: rgba(255,255,255,0.4);">Taking you to scan items...</p>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-5 rounded-xl px-4 py-3 text-center text-sm"
        style="background: rgba(248,113,113,0.1); color: #f87171;"
      >
        {{ error }}
      </div>

      <!-- Numpad (hide when matched) -->
      <div v-if="!matched" class="grid grid-cols-3 gap-3 mb-5">
        <button
          v-for="d in ['1','2','3','4','5','6','7','8','9']"
          :key="d"
          class="flex h-16 items-center justify-center rounded-xl text-2xl font-semibold text-white active:scale-95"
          style="background: #1e293b;"
          @click="onDigit(d)"
        >{{ d }}</button>
        <button
          class="flex h-16 items-center justify-center rounded-xl text-lg font-medium active:scale-95"
          style="background: #1e293b; color: rgba(255,255,255,0.4);"
          @click="onClear"
        >Clear</button>
        <button
          class="flex h-16 items-center justify-center rounded-xl text-2xl font-semibold text-white active:scale-95"
          style="background: #1e293b;"
          @click="onDigit('0')"
        >0</button>
        <button
          class="flex h-16 items-center justify-center rounded-xl text-2xl font-semibold text-white active:scale-95"
          style="background: #1e293b;"
          @click="onBackspace"
        >
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9.75 14.25 12m0 0 2.25 2.25M14.25 12l2.25-2.25M14.25 12 12 14.25m-2.58 4.92-6.374-6.375a1.125 1.125 0 0 1 0-1.59L9.42 4.83c.21-.211.497-.33.795-.33H19.5a2.25 2.25 0 0 1 2.25 2.25v10.5a2.25 2.25 0 0 1-2.25 2.25h-9.284c-.298 0-.585-.119-.795-.33Z" />
          </svg>
        </button>
      </div>

      <!-- Action buttons (hide when matched) -->
      <div v-if="!matched" class="space-y-3">
        <button
          class="w-full rounded-2xl py-5 text-lg font-bold text-white active:scale-[0.98] disabled:opacity-30"
          style="background: #16a34a; box-shadow: 0 4px 20px rgba(22,163,74,0.4);"
          :disabled="phone.length < 3 || loading"
          @click="onLookup"
        >
          {{ loading ? 'Looking up...' : 'Look Up' }}
        </button>
        <button
          class="w-full py-3 text-base font-medium active:opacity-70"
          style="color: rgba(255,255,255,0.3);"
          @click="emit('skip')"
        >
          Skip — Continue as Guest
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.match-fade-enter-active {
  transition: all 0.3s ease-out;
}
.match-fade-enter-from {
  transform: translateY(-8px);
  opacity: 0;
}
</style>
