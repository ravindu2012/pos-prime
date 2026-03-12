// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { onMounted, onUnmounted } from 'vue'

interface ShortcutHandlers {
  onHoldOrder?: () => void
  onPay?: () => void
  onCloseDialog?: () => void
  onOpenOrders?: () => void
  onNewOrder?: () => void
  onFocusSearch?: () => void
  onToggleHeldOrders?: () => void
  onToggleReturn?: () => void
}

const GLOBAL_KEYS = new Set(['F1', 'F2', 'F3', 'F4', 'F5', 'F8', 'F9', 'F10', 'Escape'])

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  function handleKeyDown(e: KeyboardEvent) {
    const target = e.target as HTMLElement
    const isInInput =
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.isContentEditable

    // F-keys and Escape work globally (even inside inputs)
    if (GLOBAL_KEYS.has(e.key)) {
      switch (e.key) {
        case 'F1':
          e.preventDefault()
          handlers.onFocusSearch?.()
          return
        case 'F2':
          e.preventDefault()
          handlers.onToggleHeldOrders?.()
          return
        case 'F3':
        case 'F9':
          e.preventDefault()
          handlers.onPay?.()
          return
        case 'F4':
          e.preventDefault()
          handlers.onHoldOrder?.()
          return
        case 'F5':
          e.preventDefault()
          handlers.onOpenOrders?.()
          return
        case 'F8':
          e.preventDefault()
          handlers.onNewOrder?.()
          return
        case 'F10':
          e.preventDefault()
          handlers.onToggleReturn?.()
          return
        case 'Escape':
          e.preventDefault()
          handlers.onCloseDialog?.()
          return
      }
    }

    // Skip modifier shortcuts when in input fields
    if (isInInput) return

    const isMod = e.ctrlKey || e.metaKey

    // Ctrl+S — Hold order
    if (isMod && e.key === 's') {
      e.preventDefault()
      handlers.onHoldOrder?.()
      return
    }

    // Ctrl+Enter — Pay
    if (isMod && e.key === 'Enter') {
      e.preventDefault()
      handlers.onPay?.()
      return
    }

    // Ctrl+O — Orders
    if (isMod && e.key === 'o') {
      e.preventDefault()
      handlers.onOpenOrders?.()
      return
    }

    // Ctrl+N — New order
    if (isMod && e.key === 'n') {
      e.preventDefault()
      handlers.onNewOrder?.()
      return
    }

    // / — Focus search (when not in input)
    if (e.key === '/') {
      e.preventDefault()
      handlers.onFocusSearch?.()
      return
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })
}
