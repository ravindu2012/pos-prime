<script setup lang="ts">
import { ref, watch } from 'vue'
import { useCartStore } from '@/stores/cart'
import { useSettingsStore } from '@/stores/settings'
import { Percent, DollarSign, ChevronDown, ChevronUp } from 'lucide-vue-next'

const cartStore = useCartStore()
const settingsStore = useSettingsStore()

const expanded = ref(false)
const discountType = ref<'percentage' | 'amount'>(cartStore.discountType)
const discountValue = ref(cartStore.discountValue)

watch([discountType, discountValue], ([type, value]) => {
  cartStore.setDiscount(type, value)
})
</script>

<template>
  <div v-if="settingsStore.allowDiscountChange" class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
    <button
      @click="expanded = !expanded"
      class="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
    >
      <span class="flex items-center gap-1.5">
        <Percent :size="12" class="text-gray-400 dark:text-gray-500" />
        Invoice Discount
      </span>
      <div class="flex items-center gap-1.5">
        <span v-if="discountValue > 0" class="px-1.5 py-0.5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded text-[10px] font-bold">
          {{ discountType === 'percentage' ? `${discountValue}%` : `${discountValue}` }}
        </span>
        <ChevronDown v-if="!expanded" :size="14" class="text-gray-400 dark:text-gray-500" />
        <ChevronUp v-else :size="14" class="text-gray-400 dark:text-gray-500" />
      </div>
    </button>
    <Transition name="expand">
      <div v-if="expanded" class="px-3 pb-3 space-y-2">
        <div class="flex gap-1">
          <button
            @click="discountType = 'percentage'"
            class="flex-1 py-1.5 text-[10px] font-bold rounded-lg flex items-center justify-center gap-1 transition-all duration-150 uppercase tracking-wider"
            :class="discountType === 'percentage' ? 'bg-orange-500 text-white shadow-sm' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
          >
            <Percent :size="10" />
            Percent
          </button>
          <button
            @click="discountType = 'amount'"
            class="flex-1 py-1.5 text-[10px] font-bold rounded-lg flex items-center justify-center gap-1 transition-all duration-150 uppercase tracking-wider"
            :class="discountType === 'amount' ? 'bg-orange-500 text-white shadow-sm' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
          >
            <DollarSign :size="10" />
            Amount
          </button>
        </div>
        <input
          v-model.number="discountValue"
          type="number"
          :min="0"
          :max="discountType === 'percentage' ? 100 : undefined"
          step="0.01"
          :placeholder="discountType === 'percentage' ? '0%' : '0.00'"
          class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 focus:bg-white dark:focus:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400 transition-all duration-200"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.expand-enter-active {
  transition: all 0.2s ease-out;
}
.expand-leave-active {
  transition: all 0.15s ease-in;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
