<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCartStore } from '@/stores/cart'
import { useCustomerStore } from '@/stores/customer'
import { usePaymentStore } from '@/stores/payment'
import { useSettingsStore } from '@/stores/settings'
import { useCurrency } from '@/composables/useCurrency'
import { useTouchDevice } from '@/composables/useTouchDevice'
import CartItemComp from './CartItem.vue'
import CartSummary from './CartSummary.vue'
import CouponCodeInput from './CouponCodeInput.vue'
import InvoiceDiscount from './InvoiceDiscount.vue'
import InvoiceOptions from './InvoiceOptions.vue'
import NumPad from './NumPad.vue'
import CustomerSelector from '@/components/customer/CustomerSelector.vue'
import { ShoppingCart, CreditCard, Pause, Check } from 'lucide-vue-next'

const { isTouchDevice } = useTouchDevice()

const cartStore = useCartStore()
const customerStore = useCustomerStore()
const paymentStore = usePaymentStore()
const settingsStore = useSettingsStore()
const { formatCurrency } = useCurrency()

const showNumPad = ref(false)
const numPadMode = ref<'qty' | 'discount' | 'discountAmt' | 'rate'>('qty')

const availableNumPadModes = computed(() => {
  const modes: ('qty' | 'discount' | 'discountAmt' | 'rate')[] = ['qty']
  if (settingsStore.allowDiscountChange) {
    modes.push('discount')
    modes.push('discountAmt')
  }
  if (settingsStore.allowRateChange) modes.push('rate')
  return modes
})

const numPadValue = computed(() => {
  if (cartStore.selectedItemIndex === null) return 0
  const item = cartStore.items[cartStore.selectedItemIndex]
  if (!item) return 0
  if (numPadMode.value === 'qty') return item.qty
  if (numPadMode.value === 'discount') return item.discount_percentage
  if (numPadMode.value === 'discountAmt') return item.discount_amount
  return item.rate
})

const numPadLabel = computed(() => {
  if (numPadMode.value === 'qty') return 'Quantity'
  if (numPadMode.value === 'discount') return 'Discount %'
  if (numPadMode.value === 'discountAmt') return 'Discount Amt'
  return 'Price'
})

function onItemSelect(index: number) {
  cartStore.selectItem(index)
  showNumPad.value = true
  numPadMode.value = 'qty'
  // Sync keyboard input
  const item = cartStore.items[index]
  if (item) keyboardInput.value = String(item.qty)
}

function onUpdateQty(index: number, qty: number) {
  cartStore.updateQty(index, qty)
}

function onRemove(index: number) {
  cartStore.removeItem(index)
  showNumPad.value = false
}

function onNumPadUpdate(value: number) {
  if (cartStore.selectedItemIndex === null) return
  if (numPadMode.value === 'qty') {
    cartStore.updateQty(cartStore.selectedItemIndex, value)
  } else if (numPadMode.value === 'discount') {
    cartStore.updateItemDiscount(cartStore.selectedItemIndex, value)
  } else if (numPadMode.value === 'discountAmt') {
    cartStore.updateItemDiscountAmount(cartStore.selectedItemIndex, value)
  } else {
    cartStore.updateRate(cartStore.selectedItemIndex, value)
  }
}

function switchNumPadMode(mode: 'qty' | 'discount' | 'discountAmt' | 'rate') {
  numPadMode.value = mode
}

// Keyboard input for non-touch desktops
const keyboardInput = ref('')

function onKeyboardInputChange() {
  const val = parseFloat(keyboardInput.value) || 0
  onNumPadUpdate(val)
}

function closeKeyboardInput() {
  onKeyboardInputChange()
  showNumPad.value = false
}

function openPayment() {
  paymentStore.openPaymentDialog()
}

const emit = defineEmits<{
  holdOrder: []
}>()
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-900">
    <!-- Customer selector -->
    <div class="p-3 border-b border-gray-100 dark:border-gray-800">
      <CustomerSelector />
    </div>

    <!-- Cart items -->
    <div class="flex-1 overflow-y-auto px-1.5 py-2">
      <div
        v-if="cartStore.items.length === 0"
        class="flex flex-col items-center justify-center h-full"
      >
        <div class="w-16 h-16 bg-gray-50 dark:bg-gray-800 rounded-2xl flex items-center justify-center mb-3">
          <ShoppingCart :size="28" class="text-gray-300 dark:text-gray-600" />
        </div>
        <span class="text-sm font-medium text-gray-400 dark:text-gray-500">Cart is empty</span>
        <span class="text-xs text-gray-300 dark:text-gray-600 mt-0.5">Add items to get started</span>
      </div>
      <TransitionGroup v-else name="cart-item" tag="div" class="space-y-0.5">
        <CartItemComp
          v-for="(item, index) in cartStore.items"
          :key="`${item.item_code}-${item.batch_no || ''}-${index}`"
          :item="item"
          :index="index"
          :selected="cartStore.selectedItemIndex === index"
          @select="onItemSelect"
          @update-qty="onUpdateQty"
          @remove="onRemove"
        />
      </TransitionGroup>
    </div>

    <!-- NumPad for touch devices -->
    <Transition name="numpad">
      <div v-if="isTouchDevice && showNumPad && cartStore.selectedItemIndex !== null" class="px-2 pb-2 border-t border-gray-100 dark:border-gray-800">
        <div class="flex gap-1 my-2">
          <button
            v-for="mode in availableNumPadModes"
            :key="mode"
            @click="switchNumPadMode(mode)"
            class="flex-1 py-1.5 text-[10px] font-bold rounded-lg transition-all duration-150 uppercase tracking-wider"
            :class="numPadMode === mode
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
          >
            {{ mode === 'qty' ? 'Qty' : mode === 'discount' ? 'Disc%' : mode === 'discountAmt' ? 'Disc$' : 'Price' }}
          </button>
        </div>
        <NumPad
          :value="numPadValue"
          :label="numPadLabel"
          @update:value="onNumPadUpdate"
          @close="showNumPad = false"
        />
      </div>
    </Transition>

    <!-- Keyboard input for non-touch desktops -->
    <Transition name="numpad">
      <div v-if="!isTouchDevice && showNumPad && cartStore.selectedItemIndex !== null" class="px-3 py-2 border-t border-gray-100 dark:border-gray-800">
        <div class="flex gap-1 mb-2">
          <button
            v-for="mode in availableNumPadModes"
            :key="mode"
            @click="() => { switchNumPadMode(mode); const item = cartStore.items[cartStore.selectedItemIndex!]; if (item) keyboardInput = String(mode === 'qty' ? item.qty : mode === 'discount' ? item.discount_percentage : mode === 'discountAmt' ? item.discount_amount : item.rate) }"
            class="flex-1 py-1.5 text-[10px] font-bold rounded-lg transition-all duration-150 uppercase tracking-wider"
            :class="numPadMode === mode
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
          >
            {{ mode === 'qty' ? 'Qty' : mode === 'discount' ? 'Disc%' : mode === 'discountAmt' ? 'Disc$' : 'Price' }}
          </button>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider shrink-0">{{ numPadLabel }}</span>
          <input
            v-model="keyboardInput"
            type="number"
            step="any"
            min="0"
            @input="onKeyboardInputChange"
            @keydown.enter="closeKeyboardInput"
            class="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-1.5 text-sm font-semibold text-right focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
            autofocus
          />
          <button
            @click="closeKeyboardInput"
            class="flex items-center gap-1 text-[10px] font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors px-2 py-1.5 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/30"
          >
            <Check :size="12" />
            Done
          </button>
        </div>
      </div>
    </Transition>

    <!-- Summary + Actions (sticky bottom) -->
    <div class="border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
      <!-- Expandable extras -->
      <div v-if="cartStore.items.length > 0" class="px-3 pt-2 space-y-1.5">
        <InvoiceDiscount />
        <CouponCodeInput />
        <InvoiceOptions />
      </div>

      <!-- Summary -->
      <div class="px-3 pt-2 pb-2">
        <CartSummary />
      </div>

      <!-- Action Buttons -->
      <div class="px-3 pb-3 flex gap-2">
        <button
          @click="emit('holdOrder')"
          :disabled="cartStore.items.length === 0"
          class="py-3 px-4 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 rounded-xl text-sm font-bold hover:bg-amber-100 dark:hover:bg-amber-900/30 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 flex items-center justify-center gap-1.5"
          title="Hold Order"
        >
          <Pause :size="16" />
        </button>
        <button
          @click="openPayment"
          :disabled="cartStore.items.length === 0 || !customerStore.customer"
          class="flex-1 py-3 rounded-xl text-sm font-bold transition-all duration-200 flex items-center justify-center gap-2"
          :class="cartStore.items.length > 0 && customerStore.customer
            ? 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[0.98] shadow-lg shadow-blue-600/20'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 cursor-not-allowed'"
        >
          <CreditCard :size="16" />
          Pay {{ cartStore.items.length > 0 ? formatCurrency(cartStore.grandTotal) : '' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cart-item-enter-active {
  transition: all 0.25s ease-out;
}
.cart-item-leave-active {
  transition: all 0.2s ease-in;
}
.cart-item-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.cart-item-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
.cart-item-move {
  transition: transform 0.25s ease;
}

.numpad-enter-active {
  transition: all 0.2s ease-out;
}
.numpad-leave-active {
  transition: all 0.15s ease-in;
}
.numpad-enter-from,
.numpad-leave-to {
  opacity: 0;
  max-height: 0;
}
.numpad-enter-to,
.numpad-leave-from {
  max-height: 400px;
}
</style>
