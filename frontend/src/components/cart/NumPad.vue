<!-- Copyright (c) 2026, Ravindu Gajanayaka -->
<!-- Licensed under GPLv3. See license.txt -->

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Delete, Check } from 'lucide-vue-next'

const props = defineProps<{
  value: number
  label?: string
}>()

const emit = defineEmits<{
  'update:value': [value: number]
  close: []
}>()

const display = ref(String(props.value))

watch(
  () => props.value,
  (v) => {
    display.value = String(v)
  }
)

const buttons = [
  '1', '2', '3',
  '4', '5', '6',
  '7', '8', '9',
  '.', '0', 'DEL',
]

function press(key: string) {
  if (key === 'DEL') {
    display.value = display.value.slice(0, -1) || '0'
  } else if (key === '.') {
    if (!display.value.includes('.')) {
      display.value += '.'
    }
  } else {
    if (display.value === '0') {
      display.value = key
    } else {
      display.value += key
    }
  }
  emit('update:value', parseFloat(display.value) || 0)
}
</script>

<template>
  <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-2.5">
    <div class="flex items-center justify-between mb-2">
      <span class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ label || 'Quantity' }}</span>
      <button
        @click="emit('close')"
        class="flex items-center gap-1 text-[10px] font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors px-2 py-0.5 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/30"
      >
        <Check :size="12" />
        Done
      </button>
    </div>
    <div class="text-right text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 px-3 py-1.5 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      {{ display }}
    </div>
    <div class="grid grid-cols-3 gap-1">
      <button
        v-for="btn in buttons"
        :key="btn"
        @click="press(btn)"
        :aria-label="btn === 'DEL' ? 'Delete' : `Press ${btn}`"
        class="h-10 rounded-lg font-semibold transition-all duration-150 active:scale-95 flex items-center justify-center"
        :class="
          btn === 'DEL'
            ? 'bg-red-50 dark:bg-red-900/30 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 text-sm'
            : 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm border border-gray-200 dark:border-gray-700'
        "
      >
        <Delete v-if="btn === 'DEL'" :size="16" />
        <span v-else>{{ btn }}</span>
      </button>
    </div>
  </div>
</template>
