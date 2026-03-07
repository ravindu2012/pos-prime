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
import CameraScanner from '@/components/scanner/CameraScanner.vue'
import { Package } from 'lucide-vue-next'
import type { Item } from '@/types'

const itemsStore = useItemsStore()
const cartStore = useCartStore()
const settingsStore = useSettingsStore()
const scrollContainer = ref<HTMLElement | null>(null)
const showCameraScanner = ref(false)
const columnCount = ref(4)

onMounted(() => {
  itemsStore.fetchItemGroups()
  itemsStore.fetchAllItems()
  updateColumnCount()
  window.addEventListener('resize', updateColumnCount)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateColumnCount)
})

function updateColumnCount() {
  const width = scrollContainer.value?.clientWidth || window.innerWidth
  if (width < 640) columnCount.value = 2
  else if (width < 768) columnCount.value = 3
  else if (width < 1280) columnCount.value = 4
  else columnCount.value = 5
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
    estimateSize: () => settingsStore.hideImages ? 90 : 240,
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
      cartStore.addItem(itemsStore.filteredItems[0])
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

function onItemSelect(item: Item) {
  cartStore.addItem(item)
}

// Hardware barcode scanner integration
async function handleBarcodeScan(barcode: string) {
  const result = await itemsStore.searchByBarcode(barcode)
  if (result && result.item_code) {
    // Find item in full list or create minimal item for cart
    const existingItem = itemsStore.allItems.find((i) => i.item_code === result.item_code)
    if (existingItem) {
      cartStore.addItem(existingItem)
    } else {
      // Add as minimal item — the backend will resolve full details
      cartStore.addItem({
        item_code: result.item_code,
        item_name: result.item_name || result.item_code,
        rate: result.rate || 0,
        actual_qty: 0,
        stock_uom: result.uom || 'Nos',
        description: '',
        item_group: '',
        image: null,
        currency: settingsStore.currency,
        has_batch_no: !!result.batch_no,
        has_serial_no: !!result.serial_no,
        brand: null,
        weight_per_unit: null,
        weight_uom: null,
        barcode: result.barcode || null,
        item_tax_template: null,
      })

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
  }
}

useBarcodeScanner(handleBarcodeScan)

function onCameraScan(value: string) {
  showCameraScanner.value = false
  handleBarcodeScan(value)
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="p-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <ItemSearch
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
        v-if="itemsStore.itemGroups.length > 1"
        mode="desktop"
        class="hidden lg:flex"
        :groups="itemsStore.itemGroups"
        :selected="itemsStore.selectedGroup"
        @select="onGroupSelect"
      />

      <div
        ref="scrollContainer"
        class="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900"
      >
        <div
          v-if="itemsStore.loading && itemsStore.allItems.length === 0"
          class="flex items-center justify-center py-12"
        >
          <div class="text-gray-400 dark:text-gray-500 text-sm">Loading items...</div>
        </div>

        <div
          v-else-if="itemsStore.filteredItems.length === 0"
          class="flex flex-col items-center justify-center py-12"
        >
          <Package class="text-gray-300 dark:text-gray-600 mb-3" :size="48" />
          <p class="text-gray-500 dark:text-gray-400 text-sm">No items found</p>
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
            class="px-3"
          >
            <div class="grid gap-3 pb-3" :style="{ gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))` }">
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
  </div>
</template>
