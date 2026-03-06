<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import { useCustomerStore } from '@/stores/customer'
import { useItemsStore } from '@/stores/items'
import { useCartStore } from '@/stores/cart'
import { usePaymentStore } from '@/stores/payment'
import { useBarcodeScanner } from '@/composables/useBarcodeScanner'
import { useCurrency } from '@/composables/useCurrency'
import { useKioskMode } from '@/composables/useKioskMode'
import { usePaymentTerminal } from '@/composables/usePaymentTerminal'
import KioskWelcome from '@/components/kiosk/KioskWelcome.vue'
import KioskPhoneEntry from '@/components/kiosk/KioskPhoneEntry.vue'
import KioskScanning from '@/components/kiosk/KioskScanning.vue'
import type { ComponentPublicInstance } from 'vue'
import KioskCartReview from '@/components/kiosk/KioskCartReview.vue'
import KioskPayment from '@/components/kiosk/KioskPayment.vue'
import KioskProcessing from '@/components/kiosk/KioskProcessing.vue'
import KioskComplete from '@/components/kiosk/KioskComplete.vue'

type KioskStep = 'welcome' | 'phone_entry' | 'scanning' | 'cart_review' | 'payment' | 'processing' | 'complete'

const route = useRoute()
const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()
const customerStore = useCustomerStore()
const itemsStore = useItemsStore()
const cartStore = useCartStore()
const paymentStore = usePaymentStore()
const { formatCurrency } = useCurrency()

const scanningRef = ref<ComponentPublicInstance & { showScannedFeedback: (name: string) => void; showScanError: (barcode: string) => void } | null>(null)
const step = ref<KioskStep>('welcome')
const initError = ref<string | null>(null)
const initializing = ref(true)
const companyName = ref('')
const companyLogo = ref('')

// Payment error state
const paymentError = ref<string | null>(null)

// Phone/loyalty state
const phoneLookupLoading = ref(false)
const phoneLookupError = ref<string | null>(null)
const matchedCustomerName = ref<string | null>(null)
const matchedLoyaltyPoints = ref(0)

// Kiosk mode: fullscreen, idle, nav prevention
const { isFullscreen, isLocked, enterFullscreen, resetIdleTimer } = useKioskMode({
  idleTimeout: 120_000,
  onIdleTimeout: () => {
    if (step.value !== 'welcome' && step.value !== 'processing') {
      resetToWelcome()
    }
  },
})

// Payment terminal (mock for MVP)
const terminal = usePaymentTerminal()

// Barcode scanner
useBarcodeScanner(handleBarcodeScan)

// Auto-reset timer for complete step
let completeTimer: ReturnType<typeof setTimeout> | null = null
const countdown = ref(8)
let countdownInterval: ReturnType<typeof setInterval> | null = null

const cashMethodAvailable = computed(() =>
  settingsStore.paymentMethods.some(
    (m) => m.mode_of_payment.toLowerCase().includes('cash')
  )
)

const cardMethodName = computed(() => {
  const card = settingsStore.paymentMethods.find(
    (m) => !m.mode_of_payment.toLowerCase().includes('cash')
  )
  return card?.mode_of_payment ?? null
})

const cashMethodName = computed(() => {
  const cash = settingsStore.paymentMethods.find(
    (m) => m.mode_of_payment.toLowerCase().includes('cash')
  )
  return cash?.mode_of_payment ?? 'Cash'
})

// Auto-navigate back to scanning if cart empties during review
watch(() => cartStore.items.length, (len) => {
  if (len === 0 && (step.value === 'cart_review' || step.value === 'payment')) {
    step.value = 'scanning'
  }
})

onMounted(async () => {
  await initializeSession()
})

onUnmounted(() => {
  clearCompleteTimer()
})

async function initializeSession() {
  initializing.value = true
  initError.value = null

  let sessionName = route.query.session as string

  // Auto-detect open session if not provided
  if (!sessionName) {
    try {
      const openEntries = await sessionStore.checkOpeningEntry()
      if (openEntries && openEntries.length > 0) {
        sessionName = openEntries[0].name
      } else {
        initError.value = 'No open POS session found. Open a POS session first via Posify, then launch the kiosk.'
        initializing.value = false
        return
      }
    } catch {
      initError.value = 'Could not check for open POS sessions. Please provide ?session=POS-OPE-XXXX in the URL.'
      initializing.value = false
      return
    }
  }

  try {
    // Fetch POS Opening Entry
    const entry = await call('frappe.client.get', {
      doctype: 'POS Opening Entry',
      name: sessionName,
    })

    if (!entry || entry.docstatus !== 1 || entry.status === 'Closed') {
      initError.value = `POS Session "${sessionName}" is not open. Please open a valid POS session first.`
      initializing.value = false
      return
    }

    // Populate session store
    sessionStore.openingEntry = entry.name
    sessionStore.posProfile = entry.pos_profile
    sessionStore.company = entry.company
    sessionStore.isOpen = true

    // Load POS Profile
    await settingsStore.loadPOSProfile(entry.pos_profile)

    // Load company info
    companyName.value = entry.company
    try {
      const companyDoc = await call('frappe.client.get', {
        doctype: 'Company',
        name: entry.company,
        fields: ['company_logo', 'company_name'],
      })
      companyLogo.value = companyDoc?.company_logo || ''
      companyName.value = companyDoc?.company_name || entry.company
    } catch {
      // Non-critical
    }

    // Set default walk-in customer
    if (settingsStore.posProfile?.customer) {
      await customerStore.setCustomer(settingsStore.posProfile.customer)
    }

    // Connect terminal (mock)
    await terminal.connect()

    initializing.value = false
  } catch (e: any) {
    initError.value = e?.message || 'Failed to initialize kiosk session.'
    initializing.value = false
  }
}

async function handleBarcodeScan(barcode: string) {
  resetIdleTimer()
  const result = await itemsStore.searchByBarcode(barcode)
  const needsTransition = step.value === 'welcome' || step.value === 'phone_entry'

  if (result) {
    // Check stock availability for stock items
    if (result.is_stock_item && result.actual_qty !== undefined && result.actual_qty <= 0) {
      const msg = `${result.item_name} is out of stock`
      if (needsTransition) {
        step.value = 'scanning'
        setTimeout(() => scanningRef.value?.showScanError(msg), 350)
      } else {
        scanningRef.value?.showScanError(msg)
      }
      return
    }
    cartStore.addItem(result)
    if (needsTransition) {
      step.value = 'scanning'
      // Wait for out-in transition (250ms) + mount before calling exposed method
      setTimeout(() => scanningRef.value?.showScannedFeedback(result.item_name), 350)
    } else {
      scanningRef.value?.showScannedFeedback(result.item_name)
    }
  } else {
    if (needsTransition) {
      step.value = 'scanning'
      setTimeout(() => scanningRef.value?.showScanError(barcode), 350)
    } else {
      scanningRef.value?.showScanError(barcode)
    }
  }
}

function startShopping() {
  resetIdleTimer()
  step.value = 'phone_entry'
}

async function lookupPhone(phone: string) {
  phoneLookupLoading.value = true
  phoneLookupError.value = null
  matchedCustomerName.value = null
  matchedLoyaltyPoints.value = 0

  // Strip non-digits for matching (handles spaces, dashes, parentheses, plus signs)
  const digits = phone.replace(/\D/g, '')
  if (!digits) {
    phoneLookupError.value = 'Please enter a valid phone number.'
    phoneLookupLoading.value = false
    return
  }

  // Strip leading 0 (trunk prefix) for international matching
  // e.g. customer enters 0778407616 → also search for 778407616
  // so it matches +94778407616, +44778407616, etc.
  const withoutTrunk = digits.startsWith('0') ? digits.slice(1) : digits

  try {
    const orFilters: any[] = [
      ['mobile_no', 'like', '%' + digits],
    ]
    // If number had a leading 0, also match without it (handles local→international)
    if (withoutTrunk !== digits) {
      orFilters.push(['mobile_no', 'like', '%' + withoutTrunk])
    }

    const results = await call('frappe.client.get_list', {
      doctype: 'Customer',
      or_filters: orFilters,
      fields: ['name', 'customer_name', 'loyalty_program'],
      limit_page_length: 1,
    })

    if (results && results.length > 0) {
      const cust = results[0]
      await customerStore.setCustomer(cust.name)
      matchedCustomerName.value = cust.customer_name
      matchedLoyaltyPoints.value = customerStore.loyaltyPoints
      // Auto-redirect to scanning after brief delay to show match
      setTimeout(() => {
        if (step.value === 'phone_entry') {
          step.value = 'scanning'
        }
      }, 1500)
    } else {
      phoneLookupError.value = 'No account found with this number. You can continue as guest.'
    }
  } catch {
    phoneLookupError.value = 'Could not look up phone number. Try again or skip.'
  } finally {
    phoneLookupLoading.value = false
  }
}

function skipPhoneEntry() {
  // Reset to walk-in customer
  if (settingsStore.posProfile?.customer) {
    customerStore.setCustomer(settingsStore.posProfile.customer)
  }
  matchedCustomerName.value = null
  matchedLoyaltyPoints.value = 0
  phoneLookupError.value = null
  step.value = 'scanning'
}

function goToCartReview() {
  step.value = 'cart_review'
}

function goBackToScanning() {
  step.value = 'scanning'
}

function goToPayment() {
  step.value = 'payment'
}

function goBackToCart() {
  step.value = 'cart_review'
}

function cancelOrder() {
  resetToWelcome()
}

async function payByCash() {
  step.value = 'processing'
  paymentError.value = null
  try {
    await submitInvoice(cashMethodName.value)
    step.value = 'complete'
    startCompleteCountdown()
  } catch (e: any) {
    paymentError.value = extractErrorMessage(e)
    step.value = 'payment'
  }
}

async function payByCard() {
  step.value = 'processing'
  paymentError.value = null
  const amount = cartStore.roundedTotal ?? cartStore.grandTotal
  const currency = settingsStore.currency || 'USD'

  const result = await terminal.collectPayment(amount, currency)
  if (result.success) {
    try {
      const methodName = cardMethodName.value || settingsStore.paymentMethods[0]?.mode_of_payment || 'Cash'
      await submitInvoice(methodName)
      step.value = 'complete'
      startCompleteCountdown()
    } catch (e: any) {
      paymentError.value = extractErrorMessage(e)
      step.value = 'payment'
    }
  } else {
    paymentError.value = 'Card payment declined. Please try again.'
    step.value = 'payment'
  }
}

function extractErrorMessage(e: any): string {
  // ERPNext sends HTML-formatted error messages — extract clean text
  const msgs: string[] = e?.exc_type
    ? [e.message || e._server_messages || 'Payment failed']
    : e?.messages || (e?.message ? [e.message] : ['Payment failed. Please try again.'])
  // Try to parse _server_messages JSON array
  if (e?._server_messages) {
    try {
      const parsed = JSON.parse(e._server_messages)
      if (Array.isArray(parsed)) {
        return parsed.map((m: string) => {
          try { return JSON.parse(m).message || m } catch { return m }
        }).map((m: string) => m.replace(/<[^>]*>/g, '').trim()).filter(Boolean).join('. ') || 'Payment failed.'
      }
    } catch { /* fall through */ }
  }
  return (Array.isArray(msgs) ? msgs : [msgs])
    .map((m: string) => String(m).replace(/<[^>]*>/g, '').trim())
    .filter(Boolean)
    .join('. ') || 'Payment failed. Please try again.'
}

function cancelProcessing() {
  terminal.cancelPayment()
  step.value = 'payment'
}

async function submitInvoice(paymentMethod: string) {
  const amount = cartStore.roundedTotal ?? cartStore.grandTotal
  const customerName = customerStore.customer?.name || settingsStore.posProfile?.customer || ''

  await paymentStore.submitInvoice({
    customer: customerName,
    pos_profile: sessionStore.posProfile,
    items: cartStore.items.map((item) => ({
      item_code: item.item_code,
      qty: item.qty,
      rate: item.rate,
      discount_percentage: item.discount_percentage,
      discount_amount: item.discount_amount || undefined,
      serial_no: item.serial_no || undefined,
      batch_no: item.batch_no || undefined,
      serial_and_batch_bundle: item.serial_and_batch_bundle || undefined,
      uom: item.uom || undefined,
      conversion_factor: item.conversion_factor || 1,
      item_tax_template: item.item_tax_template || undefined,
      margin_type: item.margin_type || undefined,
      margin_rate_or_amount: item.margin_rate_or_amount || undefined,
      description: item.description || undefined,
      weight_per_unit: item.weight_per_unit || undefined,
      weight_uom: item.weight_uom || undefined,
    })),
    payments: [{ mode_of_payment: paymentMethod, amount }],
    taxes: settingsStore.posProfile?.taxes_and_charges || undefined,
    additional_discount_percentage: cartStore.additionalDiscountPercentage || undefined,
    discount_amount: cartStore.additionalDiscountAmount || undefined,
    coupon_code: cartStore.couponCode || undefined,
  })
}

function startCompleteCountdown() {
  countdown.value = 8
  clearCompleteTimer()
  countdownInterval = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      resetToWelcome()
    }
  }, 1000)
  completeTimer = setTimeout(() => {
    resetToWelcome()
  }, 8500)
}

function clearCompleteTimer() {
  if (completeTimer) {
    clearTimeout(completeTimer)
    completeTimer = null
  }
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

function resetToWelcome() {
  clearCompleteTimer()
  cartStore.$reset()
  paymentStore.$reset()
  // Reset customer to walk-in
  matchedCustomerName.value = null
  matchedLoyaltyPoints.value = 0
  phoneLookupError.value = null
  paymentError.value = null
  if (settingsStore.posProfile?.customer) {
    customerStore.setCustomer(settingsStore.posProfile.customer)
  }
  step.value = 'welcome'
}
</script>

<template>
  <div class="fixed inset-0 select-none overflow-hidden" style="background: #0f172a; touch-action: manipulation;">
    <!-- Fullscreen lock overlay -->
    <div
      v-if="isLocked && !isFullscreen"
      class="absolute inset-0 z-50 flex items-center justify-center"
      style="background: rgba(0,0,0,0.9);"
      @click="enterFullscreen"
    >
      <div class="text-center">
        <div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl" style="background: rgba(255,255,255,0.06);">
          <svg class="h-10 w-10 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
          </svg>
        </div>
        <p class="text-2xl font-bold text-white mb-2">Tap to Resume</p>
        <p style="color: rgba(255,255,255,0.35);">Fullscreen mode required</p>
      </div>
    </div>

    <!-- Initialization -->
    <div v-if="initializing" class="flex h-full items-center justify-center">
      <div class="text-center">
        <div class="mx-auto mb-6 h-14 w-14 animate-spin rounded-full border-4" style="border-color: rgba(255,255,255,0.08); border-top-color: #16a34a;" />
        <p class="text-lg" style="color: rgba(255,255,255,0.4);">Loading kiosk...</p>
      </div>
    </div>

    <!-- Init error -->
    <div v-else-if="initError" class="flex h-full items-center justify-center p-8">
      <div class="max-w-md rounded-2xl p-8 text-center" style="background: #1e293b; border: 1px solid rgba(255,255,255,0.06);">
        <div class="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl" style="background: rgba(248,113,113,0.1);">
          <svg class="h-8 w-8" style="color: #f87171;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <h2 class="mb-2 text-xl font-bold text-white">Setup Required</h2>
        <p style="color: rgba(255,255,255,0.4);">{{ initError }}</p>
      </div>
    </div>

    <!-- Kiosk flow -->
    <template v-else>
      <!-- Enter fullscreen button -->
      <button
        v-if="!isFullscreen && !isLocked"
        class="absolute right-4 top-4 z-40 rounded-xl px-4 py-2.5 text-sm font-medium text-white active:scale-95"
        style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.1);"
        @click="enterFullscreen"
      >
        Enter Fullscreen
      </button>

      <Transition name="kiosk-fade" mode="out-in">
        <KioskWelcome
          v-if="step === 'welcome'"
          :company-name="companyName"
          :company-logo="companyLogo"
          @start="startShopping"
        />
        <KioskPhoneEntry
          v-else-if="step === 'phone_entry'"
          :loading="phoneLookupLoading"
          :error="phoneLookupError"
          :customer-name="matchedCustomerName"
          :loyalty-points="matchedLoyaltyPoints"
          @lookup="lookupPhone"
          @skip="skipPhoneEntry"
        />
        <KioskScanning
          v-else-if="step === 'scanning'"
          ref="scanningRef"
          :format-currency="formatCurrency"
          @review-cart="goToCartReview"
          @cancel="cancelOrder"
        />
        <KioskCartReview
          v-else-if="step === 'cart_review'"
          :format-currency="formatCurrency"
          @pay="goToPayment"
          @add-more="goBackToScanning"
          @cancel="cancelOrder"
        />
        <KioskPayment
          v-else-if="step === 'payment'"
          :format-currency="formatCurrency"
          :cash-available="cashMethodAvailable"
          :error="paymentError"
          @pay-card="payByCard"
          @pay-cash="payByCash"
          @back="goBackToCart"
        />
        <KioskProcessing
          v-else-if="step === 'processing'"
          :format-currency="formatCurrency"
          :terminal-status="terminal.status.value"
          @cancel="cancelProcessing"
        />
        <KioskComplete
          v-else-if="step === 'complete'"
          :format-currency="formatCurrency"
          :countdown="countdown"
          @done="resetToWelcome"
        />
      </Transition>
    </template>
  </div>
</template>

<style scoped>
.kiosk-fade-enter-active,
.kiosk-fade-leave-active {
  transition: opacity 0.25s ease;
}
.kiosk-fade-enter-from,
.kiosk-fade-leave-to {
  opacity: 0;
}
</style>
