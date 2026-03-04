import { onMounted, onUnmounted } from 'vue'

interface ShortcutHandlers {
  onHoldOrder?: () => void
  onPay?: () => void
  onCloseDialog?: () => void
  onOpenOrders?: () => void
  onNewOrder?: () => void
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  function handleKeyDown(e: KeyboardEvent) {
    // Ignore if user is in an input/textarea
    const target = e.target as HTMLElement
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.isContentEditable
    ) {
      // Only handle Escape for closing dialogs from inputs
      if (e.key === 'Escape' && handlers.onCloseDialog) {
        e.preventDefault()
        handlers.onCloseDialog()
      }
      return
    }

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

    // Escape — Close dialog
    if (e.key === 'Escape') {
      e.preventDefault()
      handlers.onCloseDialog?.()
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
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })
}
