<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Html5Qrcode } from 'html5-qrcode'
import { X, Camera } from 'lucide-vue-next'

const emit = defineEmits<{
  scan: [value: string]
  close: []
}>()

const scanning = ref(false)
const error = ref('')
const readerId = 'camera-scanner-reader'
let html5Qrcode: Html5Qrcode | null = null

onMounted(async () => {
  try {
    html5Qrcode = new Html5Qrcode(readerId)
    scanning.value = true

    await html5Qrcode.start(
      { facingMode: 'environment' },
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
      },
      (decodedText) => {
        emit('scan', decodedText)
        stopScanner()
      },
      () => {
        // Scan failure — ignore, keep trying
      }
    )
  } catch (e: any) {
    error.value = e.message || 'Could not access camera'
    scanning.value = false
  }
})

onBeforeUnmount(() => {
  stopScanner()
})

async function stopScanner() {
  if (html5Qrcode) {
    try {
      await html5Qrcode.stop()
    } catch {
      // ignore
    }
    html5Qrcode = null
  }
  scanning.value = false
}

function close() {
  stopScanner()
  emit('close')
}
</script>

<template>
  <div class="fixed inset-0 z-50 bg-black flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 bg-black/80 z-10">
      <div class="flex items-center gap-2 text-white">
        <Camera :size="18" />
        <span class="text-sm font-medium">Scan Barcode</span>
      </div>
      <button @click="close" class="text-white/80 hover:text-white">
        <X :size="20" />
      </button>
    </div>

    <!-- Camera view -->
    <div class="flex-1 flex items-center justify-center">
      <div v-if="error" class="text-center text-white">
        <p class="text-sm mb-2">{{ error }}</p>
        <button
          @click="close"
          class="px-4 py-2 bg-white/20 rounded-lg text-sm hover:bg-white/30 transition-colors"
        >
          Close
        </button>
      </div>
      <div :id="readerId" class="w-full max-w-md" />
    </div>

    <div class="text-center py-4 text-white/60 text-xs">
      Point camera at a barcode or QR code
    </div>
  </div>
</template>
