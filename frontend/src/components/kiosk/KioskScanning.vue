<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useCartStore } from '@/stores/cart'
import { useItemsStore } from '@/stores/items'
import { useSettingsStore } from '@/stores/settings'

const props = defineProps<{
  formatCurrency: (value: number) => string
}>()

const emit = defineEmits<{
  'review-cart': []
  cancel: []
}>()

const cartStore = useCartStore()
const settingsStore = useSettingsStore()
const itemsStore = useItemsStore()
const lastScanned = ref<string | null>(null)
const scanError = ref<string | null>(null)
const manualBarcode = ref('')
const manualInputRef = ref<HTMLInputElement | null>(null)
const manualLoading = ref(false)

onMounted(() => {
  nextTick(() => manualInputRef.value?.focus())
})

function incrementQty(index: number) {
  cartStore.updateQty(index, cartStore.items[index].qty + 1)
}

function decrementQty(index: number) {
  const item = cartStore.items[index]
  if (item.qty <= 1) {
    cartStore.removeItem(index)
  } else {
    cartStore.updateQty(index, item.qty - 1)
  }
}

function removeItem(index: number) {
  cartStore.removeItem(index)
}

function showScannedFeedback(itemName: string) {
  scanError.value = null
  lastScanned.value = itemName
  setTimeout(() => { lastScanned.value = null }, 2000)
}

function showScanError(barcode: string) {
  lastScanned.value = null
  scanError.value = `Barcode "${barcode}" not found`
  nextTick(() => manualInputRef.value?.focus())
  setTimeout(() => { scanError.value = null }, 4000)
}

async function submitManualBarcode() {
  if (!manualBarcode.value.trim()) return
  manualLoading.value = true
  scanError.value = null
  try {
    const result = await itemsStore.searchByBarcode(manualBarcode.value.trim())
    if (result) {
      // Check stock availability for stock items
      if (settingsStore.validateStockOnSave && result.is_stock_item && result.actual_qty !== undefined && result.actual_qty <= 0) {
        scanError.value = `${result.item_name} is out of stock`
        manualBarcode.value = ''
        nextTick(() => manualInputRef.value?.focus())
        setTimeout(() => { scanError.value = null }, 4000)
        return
      }
      cartStore.addItem(result, settingsStore.validateStockOnSave)
      manualBarcode.value = ''
      lastScanned.value = result.item_name
      setTimeout(() => { lastScanned.value = null }, 2000)
      nextTick(() => manualInputRef.value?.focus())
    } else {
      scanError.value = `Item "${manualBarcode.value}" not found`
      manualBarcode.value = ''
      nextTick(() => manualInputRef.value?.focus())
    }
  } catch {
    scanError.value = 'Lookup failed. Try again.'
  } finally {
    manualLoading.value = false
  }
}

defineExpose({ showScannedFeedback, showScanError })
</script>

<template>
  <div class="flex h-full flex-col select-none" style="background: #0f172a;">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4" style="background: #1e293b; border-bottom: 1px solid rgba(255,255,255,0.06);">
      <div>
        <h1 class="text-2xl font-bold text-white">Scan Items</h1>
        <p class="text-sm" style="color: rgba(255,255,255,0.4);">
          {{ cartStore.totalItems }} item{{ cartStore.totalItems !== 1 ? 's' : '' }} scanned
        </p>
      </div>
      <div class="flex items-center gap-2">
        <div class="h-2 w-8 rounded-full" style="background: #16a34a;" />
        <div class="h-2 w-8 rounded-full" style="background: rgba(255,255,255,0.15);" />
        <div class="h-2 w-8 rounded-full" style="background: rgba(255,255,255,0.15);" />
      </div>
    </div>

    <!-- Main content area -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Empty cart: centered scan prompt -->
      <div
        v-if="cartStore.items.length === 0"
        class="flex flex-1 flex-col items-center justify-center px-8"
      >
        <div class="kiosk-scan-pulse mx-auto mb-8 flex h-36 w-36 items-center justify-center rounded-3xl" style="background: rgba(22,163,74,0.1); border: 2px solid rgba(22,163,74,0.2);">
          <svg class="h-20 w-20" style="color: #4ade80;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 3.75 9.375v-4.5ZM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 0 1-1.125-1.125v-4.5ZM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 13.5 9.375v-4.5Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 6.75h.75v.75h-.75v-.75ZM6.75 16.5h.75v.75h-.75v-.75ZM16.5 6.75h.75v.75h-.75v-.75ZM13.5 13.5h.75v.75h-.75v-.75ZM13.5 19.5h.75v.75h-.75v-.75ZM19.5 13.5h.75v.75h-.75v-.75ZM19.5 19.5h.75v.75h-.75v-.75ZM16.5 16.5h.75v.75h-.75v-.75Z" />
          </svg>
        </div>
        <h2 class="mb-3 text-3xl font-bold text-white">Scan Your Items</h2>
        <p class="text-lg" style="color: rgba(255,255,255,0.35);">
          Hold the barcode up to the scanner
        </p>
      </div>

      <!-- Has items: banner + item list -->
      <div v-else class="flex flex-1 flex-col overflow-hidden">
        <!-- Continue scanning banner -->
        <div class="flex items-center gap-4 px-6 py-4" style="background: rgba(22,163,74,0.08); border-bottom: 1px solid rgba(22,163,74,0.15);">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl" style="background: rgba(22,163,74,0.15);">
            <svg class="h-5 w-5" style="color: #4ade80;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 3.75 9.375v-4.5Z" />
            </svg>
          </div>
          <p class="text-sm font-medium" style="color: #4ade80;">Continue scanning or type item code below</p>
        </div>

        <!-- Item list (scrollable) -->
        <div class="flex-1 overflow-y-auto px-6 py-4">
          <div class="space-y-3">
            <div
              v-for="(item, index) in cartStore.items"
              :key="item.item_code + '-' + index"
              class="flex items-center gap-4 rounded-2xl p-4"
              style="background: #1e293b; border: 1px solid rgba(255,255,255,0.04);"
            >
              <!-- Thumbnail -->
              <div class="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl" style="background: #0f172a;">
                <img
                  v-if="item.image"
                  :src="item.image"
                  :alt="item.item_name"
                  class="h-full w-full object-cover"
                />
                <svg v-else class="h-6 w-6" style="color: rgba(255,255,255,0.1);" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
                </svg>
              </div>

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <p class="text-base font-semibold text-white truncate">{{ item.item_name }}</p>
                  <span v-if="item.is_free_item" class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase" style="background: rgba(22,163,74,0.2); color: #4ade80;">Free</span>
                  <span v-else-if="item.pricing_rules" class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase" style="background: rgba(96,165,250,0.15); color: #60a5fa;">Promo</span>
                </div>
                <div v-if="item.is_free_item" class="text-sm" style="color: rgba(255,255,255,0.35);">Promotional item</div>
                <div v-else class="flex items-center gap-2 text-sm" style="color: rgba(255,255,255,0.35);">
                  <span v-if="item.price_list_rate && item.price_list_rate !== item.rate" class="line-through" style="color: rgba(255,255,255,0.2);">{{ formatCurrency(item.price_list_rate) }}</span>
                  <span>{{ formatCurrency(item.rate) }} each</span>
                  <span v-if="item.discount_percentage > 0" class="rounded px-1.5 py-0.5 text-[10px] font-bold" style="background: rgba(251,146,60,0.15); color: #fb923c;">-{{ item.discount_percentage }}%</span>
                  <span v-else-if="item.discount_amount > 0" class="rounded px-1.5 py-0.5 text-[10px] font-bold" style="background: rgba(251,146,60,0.15); color: #fb923c;">-{{ formatCurrency(item.discount_amount) }}</span>
                </div>
              </div>

              <!-- Qty controls -->
              <div v-if="!item.is_free_item" class="flex items-center gap-2">
                <button
                  class="flex h-11 w-11 items-center justify-center rounded-full text-lg font-bold text-white active:scale-90"
                  style="background: rgba(255,255,255,0.08);"
                  @click="decrementQty(index)"
                >&minus;</button>
                <span class="w-8 text-center text-lg font-bold text-white">{{ item.qty }}</span>
                <button
                  class="flex h-11 w-11 items-center justify-center rounded-full text-lg font-bold text-white active:scale-90"
                  style="background: rgba(255,255,255,0.08);"
                  @click="incrementQty(index)"
                >+</button>
              </div>
              <div v-else class="flex items-center">
                <span class="text-lg font-bold" style="color: rgba(255,255,255,0.3);">×{{ item.qty }}</span>
              </div>

              <!-- Line total -->
              <p class="w-24 text-right text-lg font-bold" :style="item.is_free_item ? 'color: #4ade80;' : 'color: white;'">{{ item.is_free_item ? 'FREE' : formatCurrency(item.amount) }}</p>

              <!-- Remove -->
              <button
                v-if="!item.is_free_item"
                class="flex h-10 w-10 items-center justify-center rounded-lg active:scale-90"
                style="color: #f87171;"
                @click="removeItem(index)"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
              <div v-else class="w-10" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toasts + Manual input (always visible regardless of cart state) -->
    <div class="px-5">
      <Transition name="scan-toast">
        <div
          v-if="lastScanned"
          key="success"
          class="mb-2 flex items-center gap-3 rounded-xl px-5 py-3"
          style="background: rgba(22,163,74,0.15); border: 1px solid rgba(22,163,74,0.25);"
        >
          <svg class="h-5 w-5 shrink-0" style="color: #4ade80;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
          </svg>
          <p class="text-sm font-medium truncate" style="color: #4ade80;">Added: {{ lastScanned }}</p>
        </div>
      </Transition>

      <Transition name="scan-toast">
        <div
          v-if="scanError"
          key="error"
          class="mb-2 flex items-center gap-3 rounded-xl px-5 py-3"
          style="background: rgba(248,113,113,0.12); border: 1px solid rgba(248,113,113,0.2);"
        >
          <svg class="h-5 w-5 shrink-0" style="color: #f87171;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
          <p class="text-sm font-medium" style="color: #f87171;">{{ scanError }}</p>
        </div>
      </Transition>

      <!-- Always-visible manual barcode input -->
      <form class="mb-3 flex gap-3" @submit.prevent="submitManualBarcode">
        <input
          ref="manualInputRef"
          v-model="manualBarcode"
          type="text"
          inputmode="text"
          placeholder="Type item code or barcode"
          class="flex-1 rounded-xl border-0 px-5 py-4 text-base font-medium text-white outline-none"
          style="background: #1e293b; color: white;"
        />
        <button
          type="submit"
          class="shrink-0 rounded-xl px-6 py-4 text-base font-bold text-white active:scale-95 disabled:opacity-30"
          style="background: #16a34a;"
          :disabled="!manualBarcode.trim() || manualLoading"
        >
          {{ manualLoading ? '...' : 'Add' }}
        </button>
      </form>
    </div>

    <!-- Sticky bottom bar -->
    <div class="px-5 pb-5" style="background: #0f172a;">
      <div
        class="flex items-center justify-between rounded-2xl px-6 py-4"
        style="background: #1e293b; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 -4px 30px rgba(0,0,0,0.3);"
      >
        <div>
          <p class="text-sm" style="color: rgba(255,255,255,0.4);">
            {{ cartStore.items.length > 0 ? cartStore.totalItems + ' item' + (cartStore.totalItems !== 1 ? 's' : '') : 'No items yet' }}
          </p>
          <p class="text-2xl font-bold text-white">
            {{ formatCurrency(cartStore.roundedTotal ?? cartStore.grandTotal) }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <button
            class="rounded-xl px-5 py-3 text-sm font-semibold active:scale-95"
            style="color: rgba(255,255,255,0.35);"
            @click="emit('cancel')"
          >
            Cancel
          </button>
          <button
            class="rounded-xl px-8 py-4 text-lg font-bold text-white shadow-lg active:scale-95 disabled:opacity-30"
            style="background: #16a34a; box-shadow: 0 4px 20px rgba(22,163,74,0.4);"
            :disabled="cartStore.items.length === 0"
            @click="emit('review-cart')"
          >
            Review Order &rarr;
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kiosk-scan-pulse {
  animation: scan-pulse 2.5s ease-in-out infinite;
}

@keyframes scan-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.85; }
}

.scan-toast-enter-active {
  transition: all 0.3s ease-out;
}
.scan-toast-leave-active {
  transition: all 0.3s ease-in;
}
.scan-toast-enter-from {
  transform: translateY(-12px);
  opacity: 0;
}
.scan-toast-leave-to {
  opacity: 0;
}

input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
</style>
