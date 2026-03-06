import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call } from 'frappe-ui'
import type { PaymentEntry, POSInvoice, InvoiceOptions } from '@/types'

export const usePaymentStore = defineStore('payment', () => {
  const payments = ref<PaymentEntry[]>([])
  const activePaymentMethod = ref<string>('')
  const showPaymentDialog = ref(false)
  const submitting = ref(false)
  const lastInvoice = ref<POSInvoice | null>(null)
  const error = ref<string | null>(null)

  const totalPaid = computed(() =>
    payments.value.reduce((sum, p) => sum + p.amount, 0)
  )

  function initializePayments(
    paymentMethods: { mode_of_payment: string; default: boolean }[],
    grandTotal: number,
    disableGrandTotalToDefaultMop: boolean
  ) {
    // Initialize all payment methods with 0 amount
    payments.value = paymentMethods.map((pm) => ({
      mode_of_payment: pm.mode_of_payment,
      amount: 0,
    }))

    // Set active to default method
    const defaultMethod = paymentMethods.find((p) => p.default)
    activePaymentMethod.value =
      defaultMethod?.mode_of_payment || paymentMethods[0]?.mode_of_payment || 'Cash'

    // Pre-fill default method with grand total unless disabled
    if (!disableGrandTotalToDefaultMop && grandTotal > 0) {
      const defaultPayment = payments.value.find(
        (p) => p.mode_of_payment === activePaymentMethod.value
      )
      if (defaultPayment) {
        defaultPayment.amount = grandTotal
      }
    }
  }

  function setPaymentAmount(modeOfPayment: string, amount: number) {
    const existing = payments.value.find(
      (p) => p.mode_of_payment === modeOfPayment
    )
    if (existing) {
      existing.amount = Math.max(0, amount)
    } else {
      payments.value.push({ mode_of_payment: modeOfPayment, amount: Math.max(0, amount) })
    }
  }

  function setActivePaymentMethod(mode: string) {
    activePaymentMethod.value = mode
  }

  function changeAmount(grandTotal: number) {
    return Math.round(Math.max(0, totalPaid.value - grandTotal) * 100) / 100
  }

  function remainingAmount(grandTotal: number) {
    return Math.round(Math.max(0, grandTotal - totalPaid.value) * 100) / 100
  }

  function writeOffAmount(grandTotal: number, writeOffLimit: number) {
    const remaining = remainingAmount(grandTotal)
    if (remaining > 0 && remaining <= writeOffLimit) {
      return remaining
    }
    return 0
  }

  async function submitInvoice(args: {
    customer: string
    pos_profile: string
    items: { item_code: string; qty: number; rate: number; [key: string]: any }[]
    payments: PaymentEntry[]
    taxes?: string
    additional_discount_percentage?: number
    discount_amount?: number
    apply_discount_on?: string
    coupon_code?: string
    loyalty_points?: number
    loyalty_program?: string
    redeem_loyalty_points?: boolean
    loyalty_redemption_account?: string
    loyalty_redemption_cost_center?: string
    is_return?: boolean
    return_against?: string
  } & Partial<InvoiceOptions>) {
    submitting.value = true
    try {
      const data = await call('pos_prime.api.invoices.create_pos_invoice', args)
      lastInvoice.value = data
      return data
    } catch (e) {
      error.value = 'Failed to submit invoice'
      throw e
    } finally {
      submitting.value = false
    }
  }

  function openPaymentDialog() {
    showPaymentDialog.value = true
  }

  function closePaymentDialog() {
    showPaymentDialog.value = false
  }

  function $reset() {
    payments.value = []
    activePaymentMethod.value = ''
    showPaymentDialog.value = false
    submitting.value = false
    lastInvoice.value = null
    error.value = null
  }

  return {
    payments,
    activePaymentMethod,
    showPaymentDialog,
    submitting,
    lastInvoice,
    error,
    totalPaid,
    initializePayments,
    setPaymentAmount,
    setActivePaymentMethod,
    changeAmount,
    remainingAmount,
    writeOffAmount,
    submitInvoice,
    openPaymentDialog,
    closePaymentDialog,
    $reset,
  }
})
