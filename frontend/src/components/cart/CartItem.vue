<script setup lang="ts">
import { Minus, Plus, Trash2, Gift, Zap } from 'lucide-vue-next'
import { useCurrency } from '@/composables/useCurrency'
import type { CartItem } from '@/types'

const props = defineProps<{
  item: CartItem
  index: number
  selected: boolean
}>()

const emit = defineEmits<{
  select: [index: number]
  updateQty: [index: number, qty: number]
  remove: [index: number]
}>()

const { formatCurrency } = useCurrency()
</script>

<template>
  <div
    role="listitem"
    @click="emit('select', index)"
    class="group flex items-center gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200"
    :class="[
      item.is_free_item
        ? 'bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800/50'
        : selected
          ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 shadow-sm'
          : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'
    ]"
  >
    <!-- Item Info -->
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-1.5">
        <span class="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate leading-tight">
          {{ item.item_name }}
        </span>
        <span
          v-if="item.is_free_item"
          class="inline-flex items-center gap-0.5 px-1.5 py-0 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 rounded text-[9px] font-bold shrink-0"
        >
          <Gift :size="8" />
          {{ __('Free') }}
        </span>
        <span
          v-else-if="item.pricing_rules"
          class="inline-flex items-center gap-0.5 px-1.5 py-0 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 rounded text-[9px] font-bold shrink-0"
        >
          <Zap :size="8" />
          {{ __('Promo') }}
        </span>
      </div>
      <div class="flex items-center gap-1.5 mt-0.5 text-xs text-gray-500 dark:text-gray-400">
        <span v-if="item.is_free_item" class="text-green-600 dark:text-green-400 font-medium">{{ formatCurrency(0) }}</span>
        <template v-else>
          <span v-if="item.price_list_rate && item.price_list_rate !== item.rate" class="line-through text-gray-400 dark:text-gray-500 text-[10px]">{{ formatCurrency(item.price_list_rate) }}</span>
          <span>{{ formatCurrency(item.rate) }}</span>
        </template>
        <span class="text-gray-300 dark:text-gray-600">&times;</span>
        <span class="font-medium text-gray-700 dark:text-gray-300">{{ item.qty }}</span>
        <span v-if="!item.is_free_item && item.discount_percentage > 0" class="inline-flex items-center px-1 py-0 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded text-[10px] font-semibold">
          -{{ item.discount_percentage }}%
        </span>
        <span v-else-if="!item.is_free_item && item.discount_amount > 0" class="inline-flex items-center px-1 py-0 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded text-[10px] font-semibold">
          -{{ formatCurrency(item.discount_amount) }}
        </span>
      </div>
      <div v-if="item.batch_no || item.serial_no" class="flex items-center gap-1 mt-0.5">
        <span v-if="item.batch_no" class="inline-flex items-center px-1.5 py-0 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded text-[9px] font-medium">
          B: {{ item.batch_no }}
        </span>
        <span v-if="item.serial_no" class="inline-flex items-center px-1.5 py-0 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded text-[9px] font-medium">
          SN: {{ item.serial_no }}
        </span>
      </div>
      <div v-if="item.uom !== item.stock_uom" class="text-[9px] text-gray-400 dark:text-gray-500 mt-0.5">
        {{ item.uom }} ({{ item.conversion_factor }}x)
      </div>
      <div v-if="item.item_tax_template" class="text-[9px] text-purple-500 dark:text-purple-400 mt-0.5">
        {{ item.item_tax_template }}
      </div>
    </div>

    <!-- Qty Controls (hidden for free items) -->
    <div v-if="!item.is_free_item" class="flex items-center gap-0.5 shrink-0">
      <button
        @click.stop="emit('updateQty', index, item.qty - 1)"
        aria-label="Decrease quantity"
        class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-600 dark:hover:text-gray-300 active:scale-90 transition-all duration-150"
      >
        <Minus :size="14" />
      </button>
      <span class="w-7 text-center text-xs font-bold text-gray-800 dark:text-gray-200">
        {{ item.qty }}
      </span>
      <button
        @click.stop="emit('updateQty', index, item.qty + 1)"
        aria-label="Increase quantity"
        class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-600 dark:hover:text-gray-300 active:scale-90 transition-all duration-150"
      >
        <Plus :size="14" />
      </button>
    </div>
    <div v-else class="shrink-0">
      <span class="text-xs font-bold text-green-600 dark:text-green-400">×{{ item.qty }}</span>
    </div>

    <!-- Amount -->
    <div class="w-[72px] text-right shrink-0">
      <span class="text-sm font-bold" :class="item.is_free_item ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-gray-100'">
        {{ formatCurrency(item.is_free_item ? 0 : item.amount) }}
      </span>
    </div>

    <!-- Delete (hidden for free items — they're managed by pricing rules) -->
    <button
      v-if="!item.is_free_item"
      @click.stop="emit('remove', index)"
      aria-label="Remove item"
      class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-300 dark:text-gray-600 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 active:scale-90 transition-all duration-150 opacity-0 group-hover:opacity-100"
      :class="{ 'opacity-100': selected }"
    >
      <Trash2 :size="13" />
    </button>
    <div v-else class="w-7" />
  </div>
</template>
