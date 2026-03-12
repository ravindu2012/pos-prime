<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useVirtualizer } from '@tanstack/vue-virtual'
import { useItemsStore } from '@/stores/items'
import { useCartStore } from '@/stores/cart'
import { useSettingsStore } from '@/stores/settings'
import { useBarcodeScanner } from '@/composables/useBarcodeScanner'
import ItemCard from './ItemCard.vue'
import ItemSearch from './ItemSearch.vue'
import ItemGroupFilter from './ItemGroupFilter.vue'
import BatchSerialSelector from './BatchSerialSelector.vue'
import CameraScanner from '@/components/scanner/CameraScanner.vue'
import { Package, PanelLeftClose, PanelLeftOpen } from 'lucide-vue-next'
import { useDeskMode } from '@/composables/useDeskMode'
import type { Item } from '@/types'

const { isDeskMode } = useDeskMode()

const itemsStore = useItemsStore()
const cartStore = useCartStore()
const settingsStore = useSettingsStore()
const scrollContainer = ref<HTMLElement | null>(null)
const showCameraScanner = ref(false)
const columnCount = ref(4)
const showCategories = ref(localStorage.getItem('pos_show_categories') !== 'false')

function toggleCategories() {
  showCategories.value = !showCategories.value
  localStorage.setItem('pos_show_categories', String(showCategories.value))
}

function delayedUpdateColumnCount() {
  // Delay to let sidebar CSS transition finish before measuring
  setTimeout(updateColumnCount, 300)
}

onMounted(() => {
  itemsStore.fetchItemGroups()
  itemsStore.fetchAllItems()
  updateColumnCount()
  window.addEventListener('resize', updateColumnCount)
  // Adapt when Frappe desk sidebar is toggled
  $(document.body).on('toggleSidebar', delayedUpdateColumnCount)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateColumnCount)
  $(document.body).off('toggleSidebar', delayedUpdateColumnCount)
})

function updateColumnCount() {
  const width = scrollContainer.value?.clientWidth || window.innerWidth
  if (width < 640) columnCount.value = 2
  else if (width < 768) columnCount.value = 3
  else columnCount.value = 4
}

// Group filtered items into rows for virtual scrolling
const rows = computed(() => {
  const items = itemsStore.filteredItems
  const cols = columnCount.value
  const result: Item[][] = []
  for (let i = 0; i < items.length; i += cols) {
    result.push(items.slice(i, i + cols))
  }
  return result
})

const virtualizer = useVirtualizer(
  computed(() => ({
    count: rows.value.length,
    getScrollElement: () => scrollContainer.value,
    estimateSize: () => settingsStore.hideImages ? 70 : (isDeskMode.value ? 185 : 200),
    overscan: 5,
  }))
)

// Auto-add to cart if setting enabled and exactly 1 item matches
watch(
  () => [itemsStore.searchTerm, itemsStore.filteredItems.length],
  () => {
    if (
      settingsStore.autoAddItemToCart &&
      itemsStore.filteredItems.length === 1 &&
      itemsStore.searchTerm
    ) {
      const err = cartStore.addItem(itemsStore.filteredItems[0], settingsStore.validateStockOnSave)
      if (err) showStockError(err)
      itemsStore.setSearchTerm('')
    }
  }
)

function onSearchChange(term: string) {
  itemsStore.setSearchTerm(term)
}

function onGroupSelect(group: string) {
  itemsStore.setSelectedGroup(group)
}

// Batch/Serial selector state
const batchSerialItem = ref<Item | null>(null)

function showStockError(msg: string) {
  const frappe = (window as any).frappe
  if (frappe?.show_alert) {
    frappe.show_alert({ message: msg, indicator: 'orange' }, 3)
  }
}

function onItemSelect(item: Item) {
  if (item.has_batch_no || item.has_serial_no) {
    // Show batch/serial selector dialog
    batchSerialItem.value = item
    return
  }
  const err = cartStore.addItem(item, settingsStore.validateStockOnSave)
  if (err) showStockError(err)
}

function onBatchSerialConfirm(batchNo: string | null, serialNo: string | null) {
  const item = batchSerialItem.value
  if (!item) return

  // For serial items, serials may span multiple batches — auto-split
  if (serialNo && item.has_batch_no && item.has_serial_no && !batchNo) {
    // This case shouldn't happen with current UI (batch is required first),
    // but handle it for safety
    cartStore.addItem(item, settingsStore.validateStockOnSave)
    const lastIndex = cartStore.items.length - 1
    cartStore.updateItemBatchSerial(lastIndex, null, serialNo)
  } else {
    // Normal case: add item and set batch/serial
    cartStore.addItem(item, settingsStore.validateStockOnSave)
    const lastIndex = cartStore.items.length - 1
    cartStore.updateItemBatchSerial(lastIndex, batchNo, serialNo)
    // Set qty from serial count if serials were selected
    if (serialNo) {
      const serialCount = serialNo.split('\n').filter(s => s.trim()).length
      if (serialCount > 1) {
        cartStore.updateQty(lastIndex, serialCount)
      }
    }
  }
  batchSerialItem.value = null
}

// Hardware barcode scanner integration
async function handleBarcodeScan(barcode: string) {
  const result = await itemsStore.searchByBarcode(barcode)
  if (result && result.item_code) {
    // Find item in full list or create minimal item for cart
    const existingItem = itemsStore.allItems.find((i) => i.item_code === result.item_code)
    if (existingItem) {
      const err = cartStore.addItem(existingItem, settingsStore.validateStockOnSave)
      if (err) { showStockError(err); return }
    } else {
      // Add as minimal item — the backend will resolve full details
      const err = cartStore.addItem({
        item_code: result.item_code,
        item_name: result.item_name || result.item_code,
        rate: result.rate || 0,
        actual_qty: result.actual_qty || 0,
        is_stock_item: result.is_stock_item ?? true,
        stock_uom: result.stock_uom || 'Nos',
        description: '',
        item_group: '',
        image: null,
        currency: settingsStore.currency,
        has_batch_no: !!result.batch_no || !!result.has_batch_no,
        has_serial_no: !!result.serial_no || !!result.has_serial_no,
        brand: null,
        weight_per_unit: null,
        weight_uom: null,
        barcode: result.barcode || null,
        item_tax_template: null,
        is_product_bundle: false,
      }, settingsStore.validateStockOnSave)
      if (err) { showStockError(err); return }

      // If scanned item has batch/serial info, update the cart item
      if (result.batch_no || result.serial_no) {
        const lastIndex = cartStore.items.length - 1
        cartStore.updateItemBatchSerial(
          lastIndex,
          result.batch_no || null,
          result.serial_no || null
        )
      }
    }

    // Apply barcode-specific UOM if returned by backend
    if (result.barcode_uom) {
      const lastIndex = cartStore.items.length - 1
      cartStore.updateItemUom(lastIndex, result.barcode_uom, result.barcode_conversion_factor || 1)
    }
  }
}

useBarcodeScanner(handleBarcodeScan)

function onCameraScan(value: string) {
  showCameraScanner.value = false
  handleBarcodeScan(value)
}

// Display label: show selected group or "All Items"
const headerLabel = computed(() => {
  return itemsStore.selectedGroup === 'All Item Groups'
    ? __('All Items')
    : itemsStore.selectedGroup || __('All Items')
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Filter section — ERPNext-style: label + search + category toggle -->
    <div class="flex items-center gap-2 px-3 py-2">
      <!-- Section label (like ERPNext's "All Items") -->
      <div class="hidden sm:flex items-center gap-2 shrink-0">
        <button
          v-if="itemsStore.itemGroups.length > 1"
          class="hidden lg:flex items-center justify-center shrink-0 w-7 h-7 rounded-md text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          :title="showCategories ? __('Hide categories') : __('Show categories')"
          @click="toggleCategories"
        >
          <PanelLeftClose v-if="showCategories" :size="16" />
          <PanelLeftOpen v-else :size="16" />
        </button>
        <span class="text-base font-bold text-gray-900 dark:text-gray-100 whitespace-nowrap">{{ headerLabel }}</span>
      </div>

      <!-- Search -->
      <ItemSearch
        class="flex-1"
        :model-value="itemsStore.searchTerm"
        @update:model-value="onSearchChange"
        @open-scanner="showCameraScanner = true"
      />
    </div>

    <!-- Mobile/tablet horizontal categories -->
    <ItemGroupFilter
      v-if="itemsStore.itemGroups.length > 1"
      mode="mobile"
      class="lg:hidden"
      :groups="itemsStore.itemGroups"
      :selected="itemsStore.selectedGroup"
      @select="onGroupSelect"
    />

    <div class="flex flex-1 overflow-hidden">
      <!-- Desktop sidebar categories -->
      <ItemGroupFilter
        v-if="itemsStore.itemGroups.length > 1 && showCategories"
        mode="desktop"
        class="hidden lg:flex"
        :groups="itemsStore.itemGroups"
        :selected="itemsStore.selectedGroup"
        @select="onGroupSelect"
      />

      <div
        ref="scrollContainer"
        class="flex-1 overflow-y-auto"
      >
        <div
          v-if="itemsStore.loading && itemsStore.allItems.length === 0"
          class="flex items-center justify-center py-12"
        >
          <div class="text-gray-400 dark:text-gray-500 text-sm">{{ __('Loading items...') }}</div>
        </div>

        <div
          v-else-if="itemsStore.filteredItems.length === 0"
          class="flex flex-col items-center justify-center py-12"
        >
          <Package class="text-gray-300 dark:text-gray-600 mb-3" :size="48" />
          <p class="text-gray-500 dark:text-gray-400 text-sm">{{ __('No items found') }}</p>
        </div>

        <!-- Virtual scrolling grid -->
        <div
          v-else
          :style="{ height: `${virtualizer.getTotalSize()}px`, width: '100%', position: 'relative' }"
        >
          <div
            v-for="virtualRow in virtualizer.getVirtualItems()"
            :key="virtualRow.index"
            :ref="(el) => { if (el) virtualizer.measureElement(el as Element) }"
            :data-index="virtualRow.index"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualRow.start}px)`,
            }"
            style="padding-left: var(--padding-sm, 8px); padding-right: var(--padding-sm, 8px);"
          >
            <div
              class="grid pb-2"
              style="gap: var(--margin-sm, 8px);"
              :style="{ gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))` }"
            >
              <ItemCard
                v-for="item in rows[virtualRow.index]"
                :key="item.item_code"
                :item="item"
                @select="onItemSelect"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Camera scanner overlay -->
    <CameraScanner
      v-if="showCameraScanner"
      @scan="onCameraScan"
      @close="showCameraScanner = false"
    />

    <!-- Batch/Serial selector dialog -->
    <BatchSerialSelector
      v-if="batchSerialItem"
      :item-code="batchSerialItem.item_code"
      :item-name="batchSerialItem.item_name"
      :has-batch-no="batchSerialItem.has_batch_no"
      :has-serial-no="batchSerialItem.has_serial_no"
      @confirm="onBatchSerialConfirm"
      @close="batchSerialItem = null"
    />
  </div>
</template>
