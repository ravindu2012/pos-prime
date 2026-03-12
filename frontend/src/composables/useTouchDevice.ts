// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { ref } from 'vue'

const isTouchDevice = ref(false)

// Detect once on load
if (typeof window !== 'undefined') {
  isTouchDevice.value =
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    window.matchMedia('(pointer: coarse)').matches
}

export function useTouchDevice() {
  return { isTouchDevice }
}
