// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { ref } from 'vue'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

const toasts = ref<ToastItem[]>([])
let nextId = 0

function addToast(message: string, type: ToastItem['type'], duration = 3000) {
  const id = nextId++
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }, duration)
}

export const toast = {
  success: (msg: string) => addToast(msg, 'success'),
  error: (msg: string, opts?: { duration?: number }) => addToast(msg, 'error', opts?.duration ?? 5000),
  warning: (msg: string) => addToast(msg, 'warning', 4000),
  info: (msg: string) => addToast(msg, 'info'),
}

export function useToast() {
  return { toasts, toast }
}
