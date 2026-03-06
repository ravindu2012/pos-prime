import { ref } from 'vue'

export type TerminalStatus = 'disconnected' | 'connecting' | 'connected' | 'processing' | 'success' | 'error'

export function usePaymentTerminal() {
  const status = ref<TerminalStatus>('disconnected')
  const error = ref<string | null>(null)
  const paymentReference = ref<string | null>(null)

  let abortController: AbortController | null = null

  async function connect() {
    status.value = 'connecting'
    error.value = null
    // Mock: simulate connection delay
    await delay(500)
    status.value = 'connected'
  }

  async function collectPayment(amount: number, _currency: string): Promise<{ success: boolean; reference: string | null }> {
    status.value = 'processing'
    error.value = null
    paymentReference.value = null
    abortController = new AbortController()

    try {
      // Mock: simulate 2s card processing
      await delay(2000, abortController.signal)
      const ref = `MOCK-${Date.now()}`
      paymentReference.value = ref
      status.value = 'success'
      return { success: true, reference: ref }
    } catch {
      if (abortController?.signal.aborted) {
        status.value = 'connected'
        return { success: false, reference: null }
      }
      error.value = 'Payment failed'
      status.value = 'error'
      return { success: false, reference: null }
    } finally {
      abortController = null
    }
  }

  function cancelPayment() {
    abortController?.abort()
    abortController = null
    status.value = 'connected'
  }

  return { status, error, paymentReference, connect, collectPayment, cancelPayment }
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms)
    signal?.addEventListener('abort', () => {
      clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    })
  })
}
