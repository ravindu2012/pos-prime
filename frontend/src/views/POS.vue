<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import { useCartStore } from '@/stores/cart'
import { useCustomerStore } from '@/stores/customer'
import { usePaymentStore } from '@/stores/payment'
import { useDraftsStore } from '@/stores/drafts'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import AppShell from '@/components/layout/AppShell.vue'
import ItemGrid from '@/components/items/ItemGrid.vue'
import Cart from '@/components/cart/Cart.vue'
import PaymentDialog from '@/components/payment/PaymentDialog.vue'
import ReceiptPreview from '@/components/receipt/ReceiptPreview.vue'
import HeldOrdersDrawer from '@/components/orders/HeldOrdersDrawer.vue'
import { LayoutGrid, ShoppingCart } from 'lucide-vue-next'

const router = useRouter()
const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()
const cartStore = useCartStore()
const customerStore = useCustomerStore()
const paymentStore = usePaymentStore()
const draftsStore = useDraftsStore()

const mobileTab = ref<'items' | 'cart'>('items')
const showReceipt = ref(false)
const showHeldOrders = ref(false)
const loading = ref(true)

// Keyboard shortcuts
useKeyboardShortcuts({
  onHoldOrder: () => holdOrder(),
  onPay: () => {
    if (cartStore.items.length > 0 && customerStore.customer) {
      paymentStore.openPaymentDialog()
    }
  },
  onCloseDialog: () => {
    if (showReceipt.value) showReceipt.value = false
    else if (paymentStore.showPaymentDialog) paymentStore.closePaymentDialog()
    else if (showHeldOrders.value) showHeldOrders.value = false
  },
  onOpenOrders: () => router.push('/posify/orders'),
  onNewOrder: () => startNewOrder(),
})

onMounted(async () => {
  try {
    await sessionStore.checkOpeningEntry()
    if (!sessionStore.hasOpenShift) {
      router.replace('/posify/open')
      return
    }
    await settingsStore.loadPOSProfile(sessionStore.posProfile)
    // Set default customer from POS Profile
    if (settingsStore.posProfile?.customer && !customerStore.customer) {
      await customerStore.setCustomer(settingsStore.posProfile.customer)
    }
  } catch (e) {
    console.error('POS initialization error:', e)
  } finally {
    loading.value = false
  }
})

// Watch for invoice completion to show receipt
watch(
  () => paymentStore.lastInvoice,
  (invoice) => {
    if (invoice) {
      showReceipt.value = true
    }
  }
)

async function startNewOrder() {
  cartStore.$reset()
  paymentStore.$reset()
  draftsStore.clearActiveDraft()
  showReceipt.value = false
  // Reset to default customer
  customerStore.$reset()
  if (settingsStore.posProfile?.customer) {
    await customerStore.setCustomer(settingsStore.posProfile.customer)
  }
}

async function holdOrder() {
  if (cartStore.items.length === 0) return
  if (!customerStore.customer) return

  try {
    await draftsStore.saveDraft({
      customer: customerStore.customer.name,
      pos_profile: sessionStore.posProfile,
      items: cartStore.items.map((item) => ({
        item_code: item.item_code,
        qty: item.qty,
        rate: item.rate,
        discount_percentage: item.discount_percentage,
        serial_no: item.serial_no || undefined,
        batch_no: item.batch_no || undefined,
        uom: item.uom || undefined,
        conversion_factor: item.conversion_factor || 1,
      })),
    })
    startNewOrder()
  } catch {
    // Show error via toast or similar
  }
}

async function resumeDraft(invoiceName: string) {
  showHeldOrders.value = false
  try {
    const draft = await draftsStore.loadDraft(invoiceName)
    if (!draft) return

    // Reset cart and populate from draft
    cartStore.$reset()
    paymentStore.$reset()

    // Set customer
    if (draft.customer) {
      await customerStore.setCustomer(draft.customer)
    }

    // Add items to cart
    for (const item of draft.items || []) {
      cartStore.items.push({
        item_code: item.item_code,
        item_name: item.item_name,
        rate: item.rate,
        qty: item.qty,
        amount: item.amount || item.rate * item.qty,
        uom: item.uom || '',
        discount_percentage: item.discount_percentage || 0,
        discount_amount: item.discount_amount || 0,
        image: null,
        stock_uom: item.stock_uom || item.uom || '',
        has_serial_no: !!item.serial_no,
        has_batch_no: !!item.batch_no,
        serial_no: item.serial_no || null,
        batch_no: item.batch_no || null,
        serial_and_batch_bundle: item.serial_and_batch_bundle || null,
        conversion_factor: item.conversion_factor || 1,
        item_tax_template: item.item_tax_template || null,
        margin_type: item.margin_type || null,
        margin_rate_or_amount: item.margin_rate_or_amount || 0,
        description: item.description || null,
        project: item.project || null,
        weight_per_unit: item.weight_per_unit || null,
        weight_uom: item.weight_uom || null,
      })
    }

    // Restore invoice-level options from draft
    cartStore.setInvoiceOptions({
      customer_address: draft.customer_address || null,
      shipping_address_name: draft.shipping_address_name || null,
      contact_person: draft.contact_person || null,
      sales_partner: draft.sales_partner || null,
      project: draft.project || null,
      remarks: draft.remarks || null,
      po_no: draft.po_no || null,
      po_date: draft.po_date || null,
      shipping_rule: draft.shipping_rule || null,
      payment_terms_template: draft.payment_terms_template || null,
    })

    // Restore discount
    if (draft.additional_discount_percentage) {
      cartStore.setDiscount('percentage', draft.additional_discount_percentage)
    } else if (draft.discount_amount) {
      cartStore.setDiscount('amount', draft.discount_amount)
    }
    if (draft.coupon_code) {
      cartStore.setCouponCode(draft.coupon_code)
    }

    // Trigger tax recalculation
    cartStore.calculateTaxes()
  } catch {
    // Handle error
  }
}
</script>

<template>
  <div v-if="loading" class="h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <div class="text-gray-400 dark:text-gray-500 text-sm">Loading POS...</div>
  </div>

  <AppShell v-else @toggle-held-orders="showHeldOrders = !showHeldOrders">
    <div class="flex h-full">
      <!-- Items panel -->
      <div
        class="flex-1 flex flex-col overflow-hidden border-r border-gray-200 dark:border-gray-800"
        :class="{ 'hidden sm:flex': mobileTab === 'cart' }"
      >
        <ItemGrid />
      </div>

      <!-- Cart panel -->
      <div
        class="w-full sm:w-[340px] lg:w-[380px] shrink-0 flex flex-col overflow-hidden"
        :class="{ 'hidden sm:flex': mobileTab === 'items' }"
      >
        <Cart @hold-order="holdOrder" />
      </div>
    </div>

    <!-- Mobile tab switcher -->
    <div class="sm:hidden fixed bottom-14 left-0 right-0 flex bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 z-10">
      <button
        @click="mobileTab = 'items'"
        class="flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors"
        :class="mobileTab === 'items' ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30' : 'text-gray-500 dark:text-gray-400'"
      >
        <LayoutGrid :size="16" />
        Items
      </button>
      <button
        @click="mobileTab = 'cart'"
        class="flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors relative"
        :class="mobileTab === 'cart' ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30' : 'text-gray-500 dark:text-gray-400'"
      >
        <ShoppingCart :size="16" />
        Cart
        <span
          v-if="cartStore.totalItems > 0"
          class="absolute top-1 right-1/4 bg-blue-600 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center"
        >
          {{ cartStore.totalItems > 9 ? '9+' : cartStore.totalItems }}
        </span>
      </button>
    </div>

    <!-- Payment dialog -->
    <PaymentDialog v-if="paymentStore.showPaymentDialog" />

    <!-- Receipt preview -->
    <ReceiptPreview
      v-if="showReceipt"
      @new-order="startNewOrder"
      @close="showReceipt = false"
    />

    <!-- Held orders drawer -->
    <HeldOrdersDrawer
      v-if="showHeldOrders"
      @close="showHeldOrders = false"
      @resume="resumeDraft"
    />
  </AppShell>
</template>
