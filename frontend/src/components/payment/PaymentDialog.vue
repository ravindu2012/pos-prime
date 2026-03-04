<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useCartStore } from '@/stores/cart'
import { usePaymentStore } from '@/stores/payment'
import { useCustomerStore } from '@/stores/customer'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import { useCurrency } from '@/composables/useCurrency'
import { useTouchDevice } from '@/composables/useTouchDevice'
import { X, Check, Banknote, CreditCard, Wallet, Coins, Award, Eraser, Delete, Loader2 } from 'lucide-vue-next'

const { isTouchDevice } = useTouchDevice()

const cartStore = useCartStore()
const paymentStore = usePaymentStore()
const customerStore = useCustomerStore()
const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()
const { formatCurrency } = useCurrency()

const error = ref('')
const errorMessages = ref<string[]>([])
const applyWriteOff = ref(false)
const redeemLoyalty = ref(false)
const loyaltyPointsToRedeem = ref(0)

onMounted(() => {
  paymentStore.initializePayments(
    settingsStore.paymentMethods,
    cartStore.grandTotal,
    settingsStore.disableGrandTotalToDefaultMop
  )
})

const activeAmount = computed(() => {
  const payment = paymentStore.payments.find(
    (p) => p.mode_of_payment === paymentStore.activePaymentMethod
  )
  return payment?.amount ?? 0
})

const displayValue = ref('')
watch(activeAmount, (v) => {
  displayValue.value = v > 0 ? String(v) : ''
}, { immediate: true })

watch(() => paymentStore.activePaymentMethod, () => {
  const payment = paymentStore.payments.find(
    (p) => p.mode_of_payment === paymentStore.activePaymentMethod
  )
  displayValue.value = payment?.amount ? String(payment.amount) : ''
})

const change = computed(() => paymentStore.changeAmount(cartStore.grandTotal))
const remaining = computed(() => paymentStore.remainingAmount(cartStore.grandTotal))
const possibleWriteOff = computed(() =>
  paymentStore.writeOffAmount(cartStore.grandTotal, settingsStore.writeOffLimit)
)

const paidPercentage = computed(() => {
  if (cartStore.grandTotal <= 0) return 100
  return Math.min(100, (paymentStore.totalPaid / cartStore.grandTotal) * 100)
})

const canSubmit = computed(() => {
  if (paymentStore.submitting) return false
  if (settingsStore.allowPartialPayment) return paymentStore.totalPaid > 0
  const effectiveGrandTotal = applyWriteOff.value
    ? cartStore.grandTotal - possibleWriteOff.value
    : cartStore.grandTotal
  return paymentStore.totalPaid >= effectiveGrandTotal
})

const isCashMethod = computed(() => {
  const mode = paymentStore.activePaymentMethod.toLowerCase()
  return mode === 'cash'
})

const cashShortcuts = computed(() => {
  const gt = cartStore.grandTotal
  if (gt <= 0) return []
  const values = [
    Math.ceil(gt),
    Math.ceil(gt / 10) * 10,
    Math.ceil(gt / 50) * 50,
    Math.ceil(gt / 100) * 100,
    Math.ceil(gt / 500) * 500,
    Math.ceil(gt / 1000) * 1000,
  ]
  return [...new Set(values)].filter(v => v >= gt).slice(0, 6)
})

function getMethodIcon(mode: string) {
  const lower = mode.toLowerCase()
  if (lower === 'cash') return Banknote
  if (lower.includes('card') || lower.includes('credit') || lower.includes('debit')) return CreditCard
  if (lower.includes('coin') || lower.includes('token')) return Coins
  return Wallet
}

function selectMethod(mode: string) {
  paymentStore.setActivePaymentMethod(mode)
}

function pressKey(key: string) {
  if (key === 'C') {
    displayValue.value = ''
    paymentStore.setPaymentAmount(paymentStore.activePaymentMethod, 0)
    return
  }
  if (key === 'DEL') {
    displayValue.value = displayValue.value.slice(0, -1)
  } else if (key === '.') {
    if (!displayValue.value.includes('.')) {
      displayValue.value = (displayValue.value || '0') + '.'
    }
  } else {
    displayValue.value += key
  }
  paymentStore.setPaymentAmount(
    paymentStore.activePaymentMethod,
    parseFloat(displayValue.value) || 0
  )
}

function onPaymentInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  displayValue.value = val
  paymentStore.setPaymentAmount(
    paymentStore.activePaymentMethod,
    parseFloat(val) || 0
  )
}

function setCashAmount(amount: number) {
  displayValue.value = String(amount)
  paymentStore.setPaymentAmount(paymentStore.activePaymentMethod, amount)
}

async function submit() {
  error.value = ''
  errorMessages.value = []
  if (!customerStore.customer) {
    error.value = 'Please select a customer'
    return
  }
  try {
    const activePayments = paymentStore.payments.filter((p) => p.amount > 0)
    if (activePayments.length === 0) {
      error.value = 'Please enter a payment amount'
      return
    }

    const writeOff = applyWriteOff.value ? possibleWriteOff.value : 0

    const itemsPayload = cartStore.items.map((item) => ({
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
      project: item.project || undefined,
      weight_per_unit: item.weight_per_unit || undefined,
      weight_uom: item.weight_uom || undefined,
    }))

    const opts = cartStore.invoiceOptions || {}

    const invoice = await paymentStore.submitInvoice({
      customer: customerStore.customer.name,
      pos_profile: sessionStore.posProfile,
      items: itemsPayload,
      payments: activePayments,
      taxes: settingsStore.posProfile?.taxes_and_charges || undefined,
      additional_discount_percentage: cartStore.additionalDiscountPercentage || undefined,
      discount_amount: cartStore.additionalDiscountAmount || undefined,
      coupon_code: cartStore.couponCode || undefined,
      ...(redeemLoyalty.value && loyaltyPointsToRedeem.value > 0 && customerStore.loyaltyData
        ? {
            redeem_loyalty_points: true,
            loyalty_points: loyaltyPointsToRedeem.value,
            loyalty_program: customerStore.loyaltyData.loyalty_program,
            loyalty_redemption_account: customerStore.loyaltyData.expense_account || undefined,
            loyalty_redemption_cost_center: customerStore.loyaltyData.cost_center || undefined,
          }
        : {}),
      ...(writeOff > 0 ? { write_off_amount: writeOff } : {}),
      ...Object.fromEntries(
        Object.entries(opts).filter(([_, v]) => v != null && v !== '' && v !== false)
      ),
    })
    if (invoice) {
      paymentStore.closePaymentDialog()
    }
  } catch (e: any) {
    // ERPNext sends HTML-formatted error messages — extract all messages
    const rawMessages: string[] = e.messages || (e.message ? [e.message] : ['Failed to submit invoice'])
    errorMessages.value = rawMessages.map((msg: string) =>
      msg.replace(/<[^>]*>/g, '').trim()
    )
    error.value = errorMessages.value.join('; ')
  }
}

const numpadKeys = ['1','2','3','4','5','6','7','8','9','.','0','DEL']
</script>

<template>
  <Teleport to="body">
    <Transition name="payment-overlay">
      <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center" role="dialog" aria-label="Payment">
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/40 backdrop-blur-sm"
          @click="paymentStore.closePaymentDialog()"
        />

        <!-- Dialog -->
        <div class="relative bg-white dark:bg-gray-900 w-full sm:max-w-md sm:rounded-2xl sm:shadow-2xl dark:sm:shadow-black/30 max-h-[100dvh] sm:max-h-[92vh] flex flex-col overflow-hidden rounded-t-2xl animate-slide-up sm:animate-scale-in">

          <!-- Header with Grand Total -->
          <div class="bg-gradient-to-br from-gray-800 to-gray-900 text-white px-5 pt-4 pb-5 relative overflow-hidden">
            <!-- Decorative circles -->
            <div class="absolute -top-8 -right-8 w-32 h-32 bg-white/5 rounded-full" />
            <div class="absolute -bottom-4 -left-4 w-20 h-20 bg-white/5 rounded-full" />

            <div class="relative">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
                    <Banknote :size="18" />
                  </div>
                  <span class="text-sm font-medium text-white/80">Payment</span>
                </div>
                <button
                  @click="paymentStore.closePaymentDialog()"
                  class="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
                  aria-label="Close payment dialog"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Grand Total -->
              <div class="text-center mb-3">
                <div class="text-xs text-white/50 uppercase tracking-wider mb-1">Grand Total</div>
                <div class="text-3xl font-bold tracking-tight">
                  {{ formatCurrency(cartStore.grandTotal) }}
                </div>
              </div>

              <!-- Payment Progress Bar -->
              <div class="relative h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div
                  class="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
                  :class="paidPercentage >= 100 ? 'bg-green-400' : 'bg-blue-400'"
                  :style="{ width: `${paidPercentage}%` }"
                />
              </div>
              <div class="flex justify-between text-[10px] text-white/40 mt-1">
                <span>{{ formatCurrency(paymentStore.totalPaid) }} paid</span>
                <span v-if="remaining > 0">{{ formatCurrency(remaining) }} remaining</span>
                <span v-else-if="change > 0" class="text-green-300">{{ formatCurrency(change) }} change</span>
                <span v-else class="text-green-300">Fully paid</span>
              </div>
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMessages.length > 0" class="mx-4 mt-3 px-3 py-2 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-xl text-xs font-medium space-y-1">
            <div v-for="(msg, i) in errorMessages" :key="i">{{ msg }}</div>
          </div>
          <div v-else-if="error" class="mx-4 mt-3 px-3 py-2 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-xl text-xs font-medium">
            {{ error }}
          </div>

          <!-- Scrollable Content -->
          <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">

            <!-- Payment Method Tabs -->
            <div class="flex gap-1.5 overflow-x-auto pb-0.5 no-scrollbar" role="tablist">
              <button
                v-for="pm in settingsStore.paymentMethods"
                :key="pm.mode_of_payment"
                @click="selectMethod(pm.mode_of_payment)"
                role="tab"
                :aria-selected="paymentStore.activePaymentMethod === pm.mode_of_payment"
                class="relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 shrink-0"
                :class="
                  paymentStore.activePaymentMethod === pm.mode_of_payment
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                "
              >
                <component :is="getMethodIcon(pm.mode_of_payment)" :size="14" />
                {{ pm.mode_of_payment }}
                <!-- Amount badge -->
                <span
                  v-if="paymentStore.payments.find(p => p.mode_of_payment === pm.mode_of_payment)?.amount > 0 && paymentStore.activePaymentMethod !== pm.mode_of_payment"
                  class="ml-0.5 px-1.5 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 rounded-md text-[10px] font-bold"
                >
                  {{ formatCurrency(paymentStore.payments.find(p => p.mode_of_payment === pm.mode_of_payment)?.amount ?? 0) }}
                </span>
              </button>
            </div>

            <!-- Active Method Amount Display -->
            <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3">
              <div class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-1.5 font-semibold">
                {{ paymentStore.activePaymentMethod }} Amount
              </div>
              <!-- Keyboard input for non-touch -->
              <input
                v-if="!isTouchDevice"
                :value="displayValue"
                @input="onPaymentInput"
                type="number"
                step="any"
                min="0"
                placeholder="0"
                class="w-full text-2xl font-bold text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 rounded-lg px-3 py-2 border-2 transition-colors focus:outline-none focus:ring-1 focus:ring-blue-400"
                :class="activeAmount > 0 ? 'border-blue-200 dark:border-blue-800' : 'border-gray-200 dark:border-gray-700'"
              />
              <!-- Touch display -->
              <div
                v-else
                class="text-2xl font-bold text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 rounded-lg px-3 py-2 border-2 transition-colors"
                :class="activeAmount > 0 ? 'border-blue-200 dark:border-blue-800' : 'border-gray-200 dark:border-gray-700'"
              >
                {{ displayValue || '0' }}
              </div>
            </div>

            <!-- Cash Quick Amounts -->
            <div v-if="isCashMethod && cashShortcuts.length > 0" class="grid grid-cols-3 gap-1.5">
              <button
                v-for="amount in cashShortcuts"
                :key="amount"
                @click="setCashAmount(amount)"
                class="py-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-xl text-xs font-bold hover:bg-green-100 dark:hover:bg-green-900/40 active:scale-95 transition-all duration-150 border border-green-100 dark:border-green-800"
              >
                {{ formatCurrency(amount) }}
              </button>
            </div>

            <!-- NumPad (touch devices only) -->
            <div v-if="isTouchDevice" class="grid grid-cols-4 gap-1.5">
              <button
                v-for="key in numpadKeys"
                :key="key"
                @click="pressKey(key)"
                :aria-label="key === 'DEL' ? 'Delete' : `Press ${key}`"
                class="h-12 rounded-xl font-semibold transition-all duration-150 active:scale-95 flex items-center justify-center"
                :class="
                  key === 'DEL'
                    ? 'bg-red-50 dark:bg-red-900/30 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 text-sm'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 text-base'
                "
              >
                <Delete v-if="key === 'DEL'" :size="18" />
                <span v-else>{{ key }}</span>
              </button>
              <!-- Clear button in 4th column -->
              <button
                @click="pressKey('C')"
                aria-label="Clear"
                class="h-12 rounded-xl font-semibold bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 active:scale-95 transition-all duration-150 text-xs"
              >
                Clear
              </button>
            </div>

            <!-- Loyalty Points -->
            <div
              v-if="customerStore.loyaltyProgram && customerStore.loyaltyPoints > 0"
              class="bg-violet-50 dark:bg-violet-900/20 border border-violet-100 dark:border-violet-800 rounded-xl p-3"
            >
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="redeemLoyalty"
                  class="w-4 h-4 rounded border-violet-300 dark:border-violet-600 text-violet-600 focus:ring-violet-500"
                />
                <div class="flex-1">
                  <div class="text-xs font-semibold text-violet-800 dark:text-violet-300 flex items-center gap-1.5">
                    <Award :size="14" />
                    Redeem Loyalty Points
                  </div>
                  <div class="text-[10px] text-violet-500 dark:text-violet-400 mt-0.5">
                    {{ customerStore.loyaltyPoints }} pts available ({{ formatCurrency(customerStore.maxRedeemableAmount) }})
                  </div>
                </div>
              </label>
              <div v-if="redeemLoyalty" class="mt-2 pl-6">
                <div class="flex items-center gap-2">
                  <label class="text-[10px] text-violet-600 dark:text-violet-400 font-medium shrink-0">Points:</label>
                  <input
                    v-model.number="loyaltyPointsToRedeem"
                    type="number"
                    :min="0"
                    :max="customerStore.loyaltyPoints"
                    class="flex-1 rounded-lg border border-violet-200 dark:border-violet-700 px-2.5 py-1.5 text-xs text-right focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  />
                </div>
              </div>
            </div>

            <!-- Write-off -->
            <div
              v-if="possibleWriteOff > 0 && remaining > 0"
              class="bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 rounded-xl p-3"
            >
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="applyWriteOff"
                  class="w-4 h-4 rounded border-amber-300 dark:border-amber-600 text-amber-600 focus:ring-amber-500"
                />
                <div class="flex items-center gap-1.5">
                  <Eraser :size="14" class="text-amber-600 dark:text-amber-400" />
                  <span class="text-xs font-semibold text-amber-800 dark:text-amber-300">
                    Write off {{ formatCurrency(possibleWriteOff) }}
                  </span>
                </div>
              </label>
            </div>

            <!-- Payment Summary -->
            <div v-if="paymentStore.payments.filter(p => p.amount > 0).length > 1" class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 space-y-1.5">
              <div class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider font-semibold mb-1">Split Payment</div>
              <div
                v-for="pm in paymentStore.payments.filter(p => p.amount > 0)"
                :key="pm.mode_of_payment"
                class="flex items-center justify-between text-xs"
              >
                <span class="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                  <component :is="getMethodIcon(pm.mode_of_payment)" :size="12" class="text-gray-400 dark:text-gray-500" />
                  {{ pm.mode_of_payment }}
                </span>
                <span class="font-semibold text-gray-800 dark:text-gray-200">{{ formatCurrency(pm.amount) }}</span>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-1.5 flex items-center justify-between text-xs font-bold">
                <span class="text-gray-700 dark:text-gray-300">Total Paid</span>
                <span class="text-blue-600 dark:text-blue-400">{{ formatCurrency(paymentStore.totalPaid) }}</span>
              </div>
            </div>

            <!-- Change Display -->
            <div v-if="change > 0" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-3 text-center">
              <div class="text-[10px] text-green-500 dark:text-green-400 uppercase tracking-wider font-semibold mb-0.5">Change Due</div>
              <div class="text-xl font-bold text-green-700 dark:text-green-400">{{ formatCurrency(change) }}</div>
            </div>
          </div>

          <!-- Fixed Submit Button -->
          <div class="px-4 py-3 border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
            <button
              @click="submit"
              :disabled="!canSubmit"
              class="w-full py-3.5 rounded-xl text-sm font-bold transition-all duration-200 flex items-center justify-center gap-2"
              :class="canSubmit
                ? 'bg-green-600 text-white hover:bg-green-700 active:scale-[0.98] shadow-lg shadow-green-600/20'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 cursor-not-allowed'
              "
            >
              <Loader2 v-if="paymentStore.submitting" :size="18" class="animate-spin" />
              <Check v-else :size="18" />
              {{ paymentStore.submitting ? 'Processing...' : 'Complete Payment' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

@keyframes slide-up {
  from { transform: trangrayY(100%); opacity: 0; }
  to { transform: trangrayY(0); opacity: 1; }
}
@keyframes scale-in {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.animate-slide-up { animation: slide-up 0.3s ease-out; }
.animate-scale-in { animation: scale-in 0.2s ease-out; }

.payment-overlay-enter-active { transition: opacity 0.2s ease; }
.payment-overlay-leave-active { transition: opacity 0.15s ease; }
.payment-overlay-enter-from,
.payment-overlay-leave-to { opacity: 0; }
</style>
