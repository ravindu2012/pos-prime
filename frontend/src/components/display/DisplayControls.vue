<script setup lang="ts">
import { ref } from 'vue'
import { usePosSessionStore } from '@/stores/posSession'
import { useSerialDisplay } from '@/composables/useSerialDisplay'
import {
  Monitor,
  Usb,
  ChevronDown,
} from 'lucide-vue-next'

const sessionStore = usePosSessionStore()
const { connect, disconnect, isConnected, isSupported, baudRate } = useSerialDisplay()

const showBaudMenu = ref(false)
const baudOptions = [9600, 19200, 38400]

function openCustomerDisplay() {
  const sessionParam = sessionStore.openingEntry ? `?session=${encodeURIComponent(sessionStore.openingEntry)}` : ''
  window.open(
    `/pos-prime/display${sessionParam}`,
    `POSPrimeDisplay-${sessionStore.openingEntry || 'default'}`,
    'popup,width=800,height=600'
  )
}

async function toggleVFD() {
  if (isConnected.value) {
    await disconnect()
  } else {
    await connect(baudRate.value)
  }
}

function selectBaud(baud: number) {
  baudRate.value = baud
  showBaudMenu.value = false
}

</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 w-56 overflow-hidden">
    <div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
      <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Customer Display</span>
    </div>

    <div class="p-2 space-y-1">
      <!-- Open web display -->
      <button
        @click="openCustomerDisplay"
        class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
      >
        <Monitor :size="16" />
        Open Display Window
      </button>

      <!-- VFD section -->
      <div class="border-t border-gray-100 dark:border-gray-700 pt-1 mt-1">
        <button
          v-if="isSupported"
          @click="toggleVFD"
          class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="
            isConnected
              ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
              : 'text-gray-700 dark:text-gray-300 hover:bg-green-50 dark:hover:bg-green-900/20 hover:text-green-600 dark:hover:text-green-400'
          "
        >
          <div class="relative">
            <Usb :size="16" />
            <span
              class="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full border border-white dark:border-gray-800"
              :class="isConnected ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'"
            />
          </div>
          {{ isConnected ? 'Disconnect VFD' : 'Connect VFD' }}
        </button>

        <!-- Baud rate selector (only when disconnected) -->
        <div v-if="isSupported && !isConnected" class="relative px-2.5 pb-1">
          <button
            @click="showBaudMenu = !showBaudMenu"
            class="flex items-center justify-between w-full px-2 py-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 rounded transition-colors"
          >
            <span>Baud: {{ baudRate }}</span>
            <ChevronDown :size="12" />
          </button>
          <div
            v-if="showBaudMenu"
            class="absolute bottom-full left-2.5 right-2.5 mb-1 bg-white dark:bg-gray-700 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 overflow-hidden z-10"
          >
            <button
              v-for="baud in baudOptions"
              :key="baud"
              @click="selectBaud(baud)"
              class="block w-full px-3 py-1.5 text-xs text-left transition-colors"
              :class="
                baud === baudRate
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
              "
            >
              {{ baud }}
            </button>
          </div>
        </div>

        <p v-if="!isSupported" class="px-2.5 py-2 text-xs text-gray-400 dark:text-gray-500">
          VFD not supported in this browser. Use Chrome or Edge.
        </p>
      </div>
    </div>
  </div>
</template>
