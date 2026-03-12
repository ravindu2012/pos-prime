// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { ref, onMounted, onUnmounted } from 'vue'

export function useBarcodeScanner(onScan: (barcode: string) => void) {
  const buffer = ref('')
  const isScanning = ref(false)
  let lastKeyTime = 0
  let resetTimer: ReturnType<typeof setTimeout> | null = null

  const SCAN_THRESHOLD_MS = 50 // Max time between keystrokes for barcode scanner
  const MIN_LENGTH = 3 // Minimum barcode length

  function handleKeyDown(e: KeyboardEvent) {
    // Ignore if user is focused on an input/textarea/select
    const target = e.target as HTMLElement
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.isContentEditable
    ) {
      return
    }

    const now = Date.now()
    const timeDiff = now - lastKeyTime
    lastKeyTime = now

    // Reset buffer if too much time between keystrokes
    if (timeDiff > SCAN_THRESHOLD_MS) {
      buffer.value = ''
    }

    if (e.key === 'Enter') {
      if (buffer.value.length >= MIN_LENGTH) {
        e.preventDefault()
        const barcode = buffer.value
        buffer.value = ''
        isScanning.value = false
        onScan(barcode)
      }
      buffer.value = ''
      return
    }

    // Only accept printable characters
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      buffer.value += e.key
      isScanning.value = true

      // Reset after a timeout (no more keystrokes coming)
      if (resetTimer) clearTimeout(resetTimer)
      resetTimer = setTimeout(() => {
        buffer.value = ''
        isScanning.value = false
      }, 200)
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
    if (resetTimer) clearTimeout(resetTimer)
  })

  return { isScanning }
}
