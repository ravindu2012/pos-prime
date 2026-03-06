import { ref, onMounted, onUnmounted } from 'vue'

export function useKioskMode(options?: { idleTimeout?: number; onIdleTimeout?: () => void }) {
  const idleTimeout = options?.idleTimeout ?? 120_000 // 2 minutes default
  const isFullscreen = ref(false)
  const isLocked = ref(false)
  const isIdle = ref(false)

  let idleTimer: ReturnType<typeof setTimeout> | null = null

  function enterFullscreen() {
    document.documentElement.requestFullscreen?.().then(() => {
      isFullscreen.value = true
      isLocked.value = false
    }).catch(() => {
      // Fullscreen request denied (needs user gesture)
    })
  }

  function onFullscreenChange() {
    const active = !!document.fullscreenElement
    isFullscreen.value = active
    if (!active) {
      // User exited fullscreen (Esc) — show re-enter overlay
      isLocked.value = true
    }
  }

  function preventContextMenu(e: Event) {
    e.preventDefault()
  }

  function preventBeforeUnload(e: BeforeUnloadEvent) {
    e.preventDefault()
  }

  function resetIdleTimer() {
    isIdle.value = false
    if (idleTimer) clearTimeout(idleTimer)
    if (idleTimeout > 0) {
      idleTimer = setTimeout(() => {
        isIdle.value = true
        options?.onIdleTimeout?.()
      }, idleTimeout)
    }
  }

  function onUserActivity() {
    resetIdleTimer()
  }

  onMounted(() => {
    document.addEventListener('fullscreenchange', onFullscreenChange)
    document.addEventListener('contextmenu', preventContextMenu)
    window.addEventListener('beforeunload', preventBeforeUnload)

    // Idle detection
    const events = ['touchstart', 'mousedown', 'mousemove', 'keydown'] as const
    events.forEach((evt) => document.addEventListener(evt, onUserActivity))
    resetIdleTimer()
  })

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    document.removeEventListener('contextmenu', preventContextMenu)
    window.removeEventListener('beforeunload', preventBeforeUnload)

    const events = ['touchstart', 'mousedown', 'mousemove', 'keydown'] as const
    events.forEach((evt) => document.removeEventListener(evt, onUserActivity))

    if (idleTimer) clearTimeout(idleTimer)
  })

  return { isFullscreen, isLocked, isIdle, enterFullscreen, resetIdleTimer }
}
