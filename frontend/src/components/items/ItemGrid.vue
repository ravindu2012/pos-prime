<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
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

onMounted(() => {
  itemsStore.fetchItemGroups()
  itemsStore.fetchItems()
})

watch(
  () => itemsStore.searchTerm,
  async () => {
    const newItems = await itemsStore.fetchItems(0)
    // Auto-add to cart if setting enabled and exactly 1 item matches
    if (settingsStore.autoAddItemToCart && newItems && newItems.length === 1 && itemsStore.searchTerm) {
      cartStore.addItem(newItems[0])
      itemsStore.setSearchTerm('')
    }
  }
)

watch(
  () => itemsStore.selectedGroup,
  () => {
    itemsStore.fetchItems(0)
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

function onScroll(e: Event) {
  const el = e.target as HTMLElement
  if (
    el.scrollTop + el.clientHeight >= el.scrollHeight - 100 &&
    itemsStore.hasMore &&
    !itemsStore.loading
  ) {
    itemsStore.fetchItems(itemsStore.items.length)
  }
}

// Hardware barcode scanner integration
async function handleBarcodeScan(barcode: string) {
  const result = await itemsStore.searchByBarcode(barcode)
  if (result && result.item_code) {
    // Find item in current list or create minimal item for cart
    const existingItem = itemsStore.items.find((i) => i.item_code === result.item_code)
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
        @scroll="onScroll"
        class="flex-1 overflow-y-auto p-3 bg-gray-50 dark:bg-gray-900"
      >
        <div
          v-if="itemsStore.loading && itemsStore.items.length === 0"
          class="flex items-center justify-center py-12"
        >
          <div class="text-gray-400 dark:text-gray-500 text-sm">Loading items...</div>
        </div>

        <div
          v-else-if="itemsStore.items.length === 0"
          class="flex flex-col items-center justify-center py-12"
        >
          <Package class="text-gray-300 dark:text-gray-600 mb-3" :size="48" />
          <p class="text-gray-500 dark:text-gray-400 text-sm">No items found</p>
        </div>

        <div
          v-else
          class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3"
        >
          <ItemCard
            v-for="item in itemsStore.items"
            :key="item.item_code"
            :item="item"
            @select="onItemSelect"
          />
        </div>

        <div
          v-if="itemsStore.loading && itemsStore.items.length > 0"
          class="flex items-center justify-center py-4"
        >
          <div class="text-gray-400 dark:text-gray-500 text-sm">Loading more...</div>
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
