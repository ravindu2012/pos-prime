<script setup lang="ts">
import { Package, Plus } from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { useCurrency } from '@/composables/useCurrency'
import type { Item } from '@/types'

const props = defineProps<{
  item: Item
}>()

const emit = defineEmits<{
  select: [item: Item]
}>()

const settingsStore = useSettingsStore()
const { formatCurrency } = useCurrency()
</script>

<template>
  <button
    @click="emit('select', props.item)"
    :aria-label="`Add ${props.item.item_name} to cart`"
    class="group relative flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md dark:hover:shadow-blue-900/10 transition-all duration-200 text-left"
  >
    <!-- Image -->
    <div v-if="!settingsStore.hideImages" class="relative aspect-square bg-gray-50 dark:bg-gray-800 flex items-center justify-center overflow-hidden">
      <img
        v-if="item.image"
        :src="item.image"
        :alt="item.item_name"
        loading="lazy"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />
      <Package v-else class="text-gray-200 dark:text-gray-700" :size="36" />

      <!-- Hover overlay -->
      <div class="absolute inset-0 bg-blue-600/0 group-hover:bg-blue-600/10 transition-colors duration-200 flex items-center justify-center">
        <div class="w-8 h-8 bg-white dark:bg-gray-800 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 scale-75 group-hover:scale-100 transition-all duration-200">
          <Plus :size="16" class="text-blue-600 dark:text-blue-400" />
        </div>
      </div>

      <!-- Stock badge -->
      <span
        v-if="item.actual_qty !== undefined"
        class="absolute top-1.5 right-1.5 text-[9px] font-bold px-1.5 py-0.5 rounded-md backdrop-blur-sm"
        :class="
          item.actual_qty > 10
            ? 'bg-emerald-500/90 text-white'
            : item.actual_qty > 0
              ? 'bg-amber-500/90 text-white'
              : 'bg-red-500/90 text-white'
        "
      >
        {{ item.actual_qty > 0 ? item.actual_qty : 'Out' }}
      </span>
    </div>

    <!-- Item Info -->
    <div class="p-2.5 flex-1 flex flex-col">
      <div class="text-xs font-semibold text-gray-800 dark:text-gray-200 line-clamp-2 leading-snug">
        {{ item.item_name }}
      </div>
      <div class="mt-auto pt-1.5">
        <span class="text-sm font-bold text-blue-600 dark:text-blue-400">
          {{ formatCurrency(item.rate) }}
        </span>
      </div>
    </div>
  </button>
</template>
