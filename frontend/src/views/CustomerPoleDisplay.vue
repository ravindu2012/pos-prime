<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'
import {
  useBroadcastDisplay,
  type DisplayMessage,
  type CartUpdatePayload,
  type PaymentCompletePayload,
  type PaymentStartPayload,
} from '@/composables/useBroadcastDisplay'

const route = useRoute()

type DisplayState = 'idle' | 'cart' | 'payment' | 'complete'

const state = ref<DisplayState>('idle')
const cartData = ref<CartUpdatePayload | null>(null)
const completedTotal = ref<PaymentCompletePayload | null>(null)
const paymentData = ref<PaymentStartPayload | null>(null)
let completeTimer: ReturnType<typeof setTimeout> | null = null

const companyName = ref<string | null>(null)
const companyLogo = ref<string | null>(null)
const currency = ref<string>('USD')

const poleCartItems = ref<HTMLElement | null>(null)
const mobileInput = ref('')
const mobileStatus = ref<'idle' | 'searching' | 'found' | 'not_found'>('idle')
const foundCustomerName = ref<string | null>(null)
let mobileStatusTimer: ReturnType<typeof setTimeout> | null = null
let searchTimeoutTimer: ReturnType<typeof setTimeout> | null = null

// Animated time display for idle screen
const currentTime = ref('')
let clockInterval: ReturnType<typeof setInterval> | null = null

// Scope channel by session (POS Opening Entry) from URL query param
const sessionId = (route.query.session as string) || undefined
const { onUpdate, sendUpdate, close } = useBroadcastDisplay(sessionId)

function fmt(value: number, curr: string): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency', currency: curr,
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    }).format(value)
  } catch { return value.toFixed(2) }
}

function companyInitials(name: string): string {
  return name.split(/\s+/).map(w => w[0]).join('').substring(0, 2).toUpperCase()
}

function paymentIcon(method: string): string {
  const m = method.toLowerCase()
  if (m.includes('cash')) return 'cash'
  if (m.includes('card') || m.includes('credit') || m.includes('debit')) return 'card'
  if (m.includes('bank') || m.includes('transfer')) return 'bank'
  return 'other'
}

function updateClock() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// Numpad handlers
function numpadPress(key: string) {
  if (mobileStatus.value === 'searching') return
  if (mobileInput.value.length < 15) {
    mobileInput.value += key
  }
}

function numpadDelete() {
  if (mobileStatus.value === 'searching') return
  mobileInput.value = mobileInput.value.slice(0, -1)
}

function numpadClear() {
  if (mobileStatus.value === 'searching') return
  mobileInput.value = ''
}

async function submitMobile() {
  const mobile = mobileInput.value.trim()
  if (!mobile) return
  mobileStatus.value = 'searching'
  try {
    const results = await call('pos_prime.api.customers.search_customers', {
      search_term: mobile,
      pos_profile: '',
    })
    if (results && results.length > 0) {
      mobileStatus.value = 'found'
      foundCustomerName.value = results[0].customer_name || results[0].name
      // Notify POS to set this customer on its side
      sendUpdate({ type: 'customer_mobile', payload: { mobile } })
    } else {
      mobileStatus.value = 'not_found'
      foundCustomerName.value = null
    }
  } catch {
    mobileStatus.value = 'not_found'
    foundCustomerName.value = null
  }
  clearMobileStatus()
}

function clearMobileStatus() {
  if (mobileStatusTimer) clearTimeout(mobileStatusTimer)
  mobileStatusTimer = setTimeout(() => {
    mobileStatus.value = 'idle'
    mobileInput.value = ''
    foundCustomerName.value = null
  }, 3000)
}

onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 10000)

  onUpdate((message: DisplayMessage) => {
    if (completeTimer) { clearTimeout(completeTimer); completeTimer = null }

    switch (message.type) {
      case 'init':
        companyName.value = message.payload.companyName
        companyLogo.value = message.payload.companyLogo
        currency.value = message.payload.currency
        break
      case 'cart_update':
        state.value = 'cart'
        cartData.value = message.payload
        if (message.payload.companyName) companyName.value = message.payload.companyName
        // Auto-scroll cart to bottom
        nextTick(() => {
          if (poleCartItems.value) {
            poleCartItems.value.scrollTo({
              top: poleCartItems.value.scrollHeight,
              behavior: 'smooth',
            })
          }
        })
        break
      case 'payment_start':
        state.value = 'payment'
        paymentData.value = message.payload
        break
      case 'payment_complete':
        state.value = 'complete'
        completedTotal.value = message.payload
        completeTimer = setTimeout(() => {
          state.value = 'idle'
          cartData.value = null
          completedTotal.value = null
          paymentData.value = null
        }, 5000)
        break
      case 'idle':
        state.value = 'idle'
        cartData.value = null
        completedTotal.value = null
        paymentData.value = null
        break
      case 'customer_result':
        if (searchTimeoutTimer) { clearTimeout(searchTimeoutTimer); searchTimeoutTimer = null }
        if (message.payload.found) {
          mobileStatus.value = 'found'
          foundCustomerName.value = message.payload.customerName
        } else {
          mobileStatus.value = 'not_found'
          foundCustomerName.value = null
        }
        clearMobileStatus()
        break
    }
  })
  document.addEventListener('click', enterFullscreen, { once: true })
})

onUnmounted(() => {
  close()
  if (completeTimer) clearTimeout(completeTimer)
  if (mobileStatusTimer) clearTimeout(mobileStatusTimer)
  if (searchTimeoutTimer) clearTimeout(searchTimeoutTimer)
  if (clockInterval) clearInterval(clockInterval)
  document.removeEventListener('click', enterFullscreen)
})

function enterFullscreen() {
  document.documentElement.requestFullscreen?.().catch(() => {})
}
</script>

<template>
  <div class="pole">
    <!-- ============================== -->
    <!-- IDLE — Branded Welcome Screen  -->
    <!-- ============================== -->
    <Transition name="fade" mode="out-in">
      <div v-if="state === 'idle'" key="idle" class="screen idle-screen">
        <!-- Top bar with time -->
        <div class="idle-top">
          <span class="idle-time">{{ currentTime }}</span>
        </div>

        <!-- Center branding -->
        <div class="idle-center">
          <div class="idle-logo-wrap">
            <div v-if="companyLogo" class="idle-logo">
              <img :src="companyLogo" alt="" />
            </div>
            <div v-else class="idle-logo idle-logo-fallback">
              <span v-if="companyName">{{ companyInitials(companyName) }}</span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="40" height="40"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" x2="21" y1="6" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            </div>
          </div>
          <h1 class="idle-name">{{ companyName || 'Welcome' }}</h1>
          <p class="idle-tagline">{{ companyName ? 'Welcome! Your order will appear here.' : 'Your order will appear here.' }}</p>
        </div>

        <!-- Mobile lookup with on-screen numpad -->
        <div class="numpad-section">
          <!-- Display field -->
          <div class="numpad-display" :class="{ 'numpad-display--empty': !mobileInput }">
            <svg class="numpad-display-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            <span v-if="mobileInput" class="numpad-display-value">{{ mobileInput }}</span>
            <span v-else class="numpad-display-placeholder">Enter mobile number</span>
          </div>

          <!-- Status feedback -->
          <Transition name="slide-up">
            <div v-if="mobileStatus === 'found'" class="m-status m-status--ok">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><polyline points="20 6 9 17 4 12"/></svg>
              Welcome, {{ foundCustomerName }}!
            </div>
            <div v-else-if="mobileStatus === 'not_found'" class="m-status m-status--err">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              Customer not found
            </div>
          </Transition>

          <!-- Number pad grid -->
          <div class="numpad-grid">
            <button v-for="n in ['1','2','3','4','5','6','7','8','9']" :key="n" class="numpad-key" @click="numpadPress(n)" :disabled="mobileStatus === 'searching'">{{ n }}</button>
            <button class="numpad-key numpad-key--fn" @click="numpadClear" :disabled="mobileStatus === 'searching'">C</button>
            <button class="numpad-key" @click="numpadPress('0')" :disabled="mobileStatus === 'searching'">0</button>
            <button class="numpad-key numpad-key--fn" @click="numpadDelete" :disabled="mobileStatus === 'searching'">
              <!-- Backspace icon -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20"><path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"/><line x1="18" y1="9" x2="12" y2="15"/><line x1="12" y1="9" x2="18" y2="15"/></svg>
            </button>
            <!-- Submit row -->
            <button class="numpad-submit" @click="submitMobile" :disabled="!mobileInput.trim() || mobileStatus === 'searching'">
              <template v-if="mobileStatus === 'searching'">
                <span class="m-spinner"></span> Looking up...
              </template>
              <template v-else>
                Submit
              </template>
            </button>
          </div>
        </div>

        <span class="idle-hint">Tap anywhere to enter fullscreen</span>
      </div>

      <!-- ============================== -->
      <!-- CART — Order Review            -->
      <!-- ============================== -->
      <div v-else-if="state === 'cart' && cartData" key="cart" class="screen cart-screen">
        <!-- Branded header with customer name -->
        <div class="cart-header">
          <div class="cart-header-left">
            <div v-if="companyLogo" class="cart-logo"><img :src="companyLogo" alt="" /></div>
            <div v-else-if="companyName" class="cart-logo cart-logo-text">{{ companyInitials(companyName) }}</div>
            <span v-if="companyName" class="cart-brand">{{ companyName }}</span>
          </div>
          <div v-if="cartData.customerName" class="cart-customer">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span class="cart-customer-name">{{ cartData.customerName }}</span>
          </div>
        </div>

        <!-- Scrollable item list -->
        <div ref="poleCartItems" class="cart-items">
          <TransitionGroup name="item-list" tag="div">
            <div v-for="(item, i) in cartData.items" :key="item.item_name + '-' + i" class="cart-item" :class="{ 'cart-item--free': item.is_free_item }">
              <div class="cart-item-info">
                <div class="cart-item-name-row">
                  <span class="cart-item-name">{{ item.item_name }}</span>
                  <span v-if="item.is_free_item" class="cart-free-badge">FREE</span>
                  <span v-else-if="item.pricing_rules" class="cart-promo-badge">Promo</span>
                </div>
                <div v-if="item.is_free_item" class="cart-item-meta">Promotional item</div>
                <div v-else class="cart-item-meta">
                  <span>Qty: {{ item.qty }} × </span>
                  <span v-if="item.price_list_rate && item.price_list_rate !== item.rate" class="cart-strike">{{ fmt(item.price_list_rate, cartData.currency) }}</span>
                  <span>{{ fmt(item.rate, cartData.currency) }}</span>
                  <span v-if="item.discount_percentage && item.discount_percentage > 0" class="cart-disc-badge">-{{ item.discount_percentage }}%</span>
                  <span v-else-if="item.discount_amount && item.discount_amount > 0" class="cart-disc-badge">-{{ fmt(item.discount_amount, cartData.currency) }}</span>
                </div>
              </div>
              <span class="cart-item-amount" :class="{ 'cart-item-amount--free': item.is_free_item }">{{ item.is_free_item ? 'FREE' : fmt(item.amount, cartData.currency) }}</span>
            </div>
          </TransitionGroup>
          <div v-if="cartData.items.length === 0" class="cart-empty">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="36" height="36"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
            <span>Waiting for items...</span>
          </div>
        </div>

        <!-- Totals footer -->
        <div class="cart-footer">
          <div class="cart-summary-row">
            <span>Subtotal ({{ cartData.totalItems }} item{{ cartData.totalItems !== 1 ? 's' : '' }})</span>
            <span>{{ fmt(cartData.subtotal, cartData.currency) }}</span>
          </div>
          <div v-if="cartData.pricingRuleDiscount" class="cart-summary-row cart-discount">
            <span>Promo Discount{{ cartData.pricingRuleDiscount.type === 'percentage' ? ` (${cartData.pricingRuleDiscount.value}%)` : '' }}</span>
            <span>-{{ fmt(cartData.subtotal - cartData.netTotal, cartData.currency) }}</span>
          </div>
          <div v-else-if="cartData.discountValue > 0" class="cart-summary-row cart-discount">
            <span>Discount{{ cartData.discountType === 'percentage' ? ` (${cartData.discountValue}%)` : '' }}</span>
            <span>-{{ fmt(cartData.subtotal - cartData.netTotal, cartData.currency) }}</span>
          </div>
          <div v-if="cartData.taxAmount > 0" class="cart-summary-row">
            <span>Tax</span>
            <span>{{ fmt(cartData.taxAmount, cartData.currency) }}</span>
          </div>
          <div class="cart-total-row">
            <span>Total</span>
            <span class="cart-total-amount">{{ fmt(cartData.roundedTotal || cartData.grandTotal, cartData.currency) }}</span>
          </div>
        </div>
      </div>

      <!-- ============================== -->
      <!-- PAYMENT — Processing           -->
      <!-- ============================== -->
      <div v-else-if="state === 'payment'" key="payment" class="screen pay-screen">
        <div class="pay-top">
          <p v-if="paymentData?.customerName" class="pay-customer">{{ paymentData.customerName }}</p>
        </div>

        <div class="pay-center">
          <!-- Grand total -->
          <div class="pay-total-block">
            <span class="pay-total-label">Amount Due</span>
            <span v-if="paymentData" class="pay-total-value">{{ fmt(paymentData.grandTotal, paymentData.currency) }}</span>
            <div class="pay-total-bar"></div>
          </div>

          <!-- Payment breakdown -->
          <div v-if="paymentData && paymentData.payments.length > 0" class="pay-breakdown">
            <div v-for="(p, i) in paymentData.payments" :key="i" class="pay-method">
              <div class="pay-method-left">
                <!-- Icons -->
                <div class="pay-method-icon" :class="'pay-method-icon--' + paymentIcon(p.mode_of_payment)">
                  <svg v-if="paymentIcon(p.mode_of_payment) === 'cash'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else-if="paymentIcon(p.mode_of_payment) === 'card'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
                  <svg v-else-if="paymentIcon(p.mode_of_payment) === 'bank'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 21 1.65-3.8a9 9 0 1 1 3.4 2.9L3 21"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                </div>
                <span class="pay-method-name">{{ p.mode_of_payment }}</span>
              </div>
              <span class="pay-method-amount">{{ fmt(p.amount, paymentData!.currency) }}</span>
            </div>

            <!-- Change due -->
            <div v-if="paymentData.changeDue > 0" class="pay-change">
              <div class="pay-change-left">
                <div class="pay-change-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                </div>
                <span>Change Due</span>
              </div>
              <span class="pay-change-amount">{{ fmt(paymentData.changeDue, paymentData.currency) }}</span>
            </div>
          </div>
        </div>

        <div class="pay-bottom">
          <div class="pay-pulse"></div>
          <span class="pay-status-text">Processing payment</span>
        </div>
      </div>

      <!-- ============================== -->
      <!-- COMPLETE — Thank You           -->
      <!-- ============================== -->
      <div v-else-if="state === 'complete'" key="complete" class="screen done-screen">
        <div class="done-badge">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <h1 class="done-heading">Thank You!</h1>
        <p v-if="paymentData?.customerName" class="done-customer">{{ paymentData.customerName }}</p>
        <div v-if="completedTotal" class="done-total">
          <span class="done-total-label">Total Paid</span>
          <span class="done-total-value">{{ fmt(completedTotal.grandTotal, completedTotal.currency) }}</span>
        </div>
        <p class="done-sub">Have a great day!</p>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ============================================ */
/*  ROOT & SHARED                                */
/* ============================================ */
.pole {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
}

.screen {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.35s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ============================================ */
/*  IDLE SCREEN                                  */
/* ============================================ */
.idle-screen {
  background: linear-gradient(170deg, #ffffff 0%, #f1f5f9 100%);
  align-items: center;
  justify-content: safe center;
  position: relative;
  overflow-y: auto;
  padding: 1.5rem 1rem;
}

.idle-top {
  position: absolute;
  top: 1.25rem;
  right: 1.5rem;
}

.idle-time {
  font-size: 0.9rem;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 0.02em;
}

.idle-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.idle-logo-wrap { margin-bottom: 0.5rem; }

.idle-logo {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.idle-logo img { width: 72%; height: 72%; object-fit: contain; }

.idle-logo-fallback {
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.idle-name {
  font-size: 1.6rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.02em;
}

.idle-tagline {
  font-size: 0.9rem;
  color: #64748b;
  margin: 0;
}

/* Numpad section */
.numpad-section {
  margin-top: 1.25rem;
  width: 100%;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

/* Display field */
.numpad-display {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem 1rem;
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  min-height: 48px;
}

.numpad-display-icon { color: #94a3b8; flex-shrink: 0; }

.numpad-display-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.06em;
}

.numpad-display-placeholder {
  font-size: 1rem;
  color: #cbd5e1;
}

/* Number pad grid */
.numpad-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 0.25rem;
}

.numpad-key {
  height: 52px;
  border: none;
  border-radius: 10px;
  background: #ffffff;
  color: #1e293b;
  font-size: 1.3rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: background 0.1s, transform 0.1s;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

.numpad-key:active:not(:disabled) {
  background: #e2e8f0;
  transform: scale(0.95);
}

.numpad-key:disabled { opacity: 0.4; cursor: not-allowed; }

.numpad-key--fn {
  background: #f1f5f9;
  color: #64748b;
  font-size: 1rem;
  font-weight: 700;
}

.numpad-key--fn:active:not(:disabled) {
  background: #e2e8f0;
}

/* Submit button spans full width */
.numpad-submit {
  grid-column: 1 / -1;
  height: 48px;
  border: none;
  border-radius: 10px;
  background: #4f46e5;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background 0.15s;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

.numpad-submit:active:not(:disabled) { background: #4338ca; }
.numpad-submit:disabled { opacity: 0.4; cursor: not-allowed; }

.m-spinner {
  width: 18px; height: 18px;
  border: 2.5px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.5s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Status */
.m-status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 1rem;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 600;
}
.m-status--ok { background: #ecfdf5; color: #047857; }
.m-status--err { background: #fef2f2; color: #b91c1c; }

.slide-up-enter-active { transition: all 0.25s ease-out; }
.slide-up-leave-active { transition: all 0.2s ease-in; }
.slide-up-enter-from { opacity: 0; transform: translateY(8px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-4px); }

.idle-hint {
  position: absolute;
  bottom: 1rem;
  font-size: 0.7rem;
  color: #cbd5e1;
}

/* ============================================ */
/*  CART SCREEN                                  */
/* ============================================ */
.cart-screen { background: #f8fafc; }

.cart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.5rem;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.cart-header-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.cart-logo {
  width: 32px; height: 32px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.cart-logo img { width: 100%; height: 100%; object-fit: contain; }
.cart-logo-text {
  background: #4f46e5;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
}

.cart-brand {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
}

.cart-customer {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #4f46e5;
}

.cart-customer-name {
  font-size: 1.35rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

/* Items */
.cart-items {
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem 0;
}

.cart-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.cart-item-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  flex: 1;
}

.cart-item-name-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.cart-item-name {
  font-size: 1.05rem;
  font-weight: 500;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cart-free-badge {
  font-size: 0.6rem;
  font-weight: 700;
  color: #059669;
  background: #ecfdf5;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.cart-promo-badge {
  font-size: 0.6rem;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.cart-item-meta {
  font-size: 0.8rem;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.cart-strike {
  text-decoration: line-through;
  color: #cbd5e1;
}

.cart-disc-badge {
  font-size: 0.65rem;
  font-weight: 700;
  color: #ea580c;
  background: #fff7ed;
  padding: 0 0.3rem;
  border-radius: 3px;
}

.cart-item-amount {
  font-size: 1.05rem;
  font-weight: 600;
  color: #334155;
  flex-shrink: 0;
  margin-left: 1rem;
}

.cart-item-amount--free {
  color: #059669;
  font-weight: 700;
}

.cart-item--free {
  background: #f0fdf4;
  border-bottom-color: #dcfce7;
}

.cart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 0;
  color: #cbd5e1;
  font-size: 0.95rem;
}

/* Item list transitions */
.item-list-enter-active { transition: all 0.3s ease-out; }
.item-list-leave-active { transition: all 0.2s ease-in; }
.item-list-enter-from { opacity: 0; transform: translateX(-16px); }
.item-list-leave-to { opacity: 0; transform: translateX(16px); }

/* Footer */
.cart-footer {
  padding: 0.75rem 1.5rem 1.25rem;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.cart-summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.3rem 0;
  font-size: 0.9rem;
  color: #64748b;
}
.cart-discount { color: #059669; }

.cart-total-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 0.5rem;
  padding-top: 0.6rem;
  border-top: 2px solid #e2e8f0;
}
.cart-total-row span:first-child {
  font-size: 1.1rem;
  font-weight: 600;
  color: #334155;
}

.cart-total-amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

/* Scrollbar */
.cart-items::-webkit-scrollbar { width: 3px; }
.cart-items::-webkit-scrollbar-track { background: transparent; }
.cart-items::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 3px; }

/* ============================================ */
/*  PAYMENT SCREEN                               */
/* ============================================ */
.pay-screen {
  background: #ffffff;
  align-items: center;
}

.pay-top {
  padding: 1.5rem 1.5rem 0;
  flex-shrink: 0;
}

.pay-customer {
  font-size: 1rem;
  color: #64748b;
  margin: 0;
  font-weight: 500;
}

.pay-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  width: 100%;
  max-width: 380px;
  padding: 1rem;
}

.pay-total-block {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}

.pay-total-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.pay-total-value {
  font-size: 3rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1;
}

.pay-total-bar {
  width: 48px;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, #4f46e5, #06b6d4);
  margin-top: 0.25rem;
}

/* Payment methods */
.pay-breakdown {
  width: 100%;
  background: #f8fafc;
  border-radius: 14px;
  padding: 0.3rem 0;
  border: 1px solid #f1f5f9;
}

.pay-method {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1rem;
}

.pay-method-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.pay-method-icon {
  width: 32px; height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.pay-method-icon svg { width: 18px; height: 18px; }

.pay-method-icon--cash { background: #ecfdf5; color: #059669; }
.pay-method-icon--card { background: #eff6ff; color: #2563eb; }
.pay-method-icon--bank { background: #f5f3ff; color: #7c3aed; }
.pay-method-icon--other { background: #ecfeff; color: #0891b2; }

.pay-method-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: #334155;
}

.pay-method-amount {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
}

/* Change due */
.pay-change {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1rem;
  margin-top: 0.15rem;
  border-top: 1px solid #e2e8f0;
}

.pay-change-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.pay-change-icon {
  width: 32px; height: 32px;
  border-radius: 8px;
  background: #fffbeb;
  color: #d97706;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pay-change-icon svg { width: 18px; height: 18px; }

.pay-change span {
  font-weight: 600;
  color: #92400e;
}

.pay-change-amount {
  font-size: 1.2rem;
  font-weight: 700;
  color: #d97706 !important;
}

/* Bottom status */
.pay-bottom {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 1.25rem;
  flex-shrink: 0;
}

.pay-pulse {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #4f46e5;
  animation: pulse-dot 1.4s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.pay-status-text {
  font-size: 0.85rem;
  color: #94a3b8;
  font-weight: 500;
}

/* ============================================ */
/*  COMPLETE SCREEN                              */
/* ============================================ */
.done-screen {
  background: #ffffff;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
}

.done-badge {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: #059669;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: badge-pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 8px 24px rgba(5, 150, 105, 0.2);
  margin-bottom: 0.5rem;
}
.done-badge svg { width: 40px; height: 40px; }

@keyframes badge-pop {
  0% { transform: scale(0) rotate(-20deg); opacity: 0; }
  100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

.done-heading {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.02em;
}

.done-customer {
  font-size: 1rem;
  color: #64748b;
  margin: 0;
}

.done-total {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  margin-top: 0.5rem;
}

.done-total-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.done-total-value {
  font-size: 2rem;
  font-weight: 700;
  color: #059669;
}

.done-sub {
  font-size: 0.95rem;
  color: #94a3b8;
  margin: 0.5rem 0 0;
}
</style>
