<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Search, X, ScanBarcode } from 'lucide-vue-next'
import { useTouchDevice } from '@/composables/useTouchDevice'

const { isTouchDevice } = useTouchDevice()

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  openScanner: []
}>()

const localValue = ref(props.modelValue)
const isFocused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
let debounceTimer: ReturnType<typeof setTimeout>

onMounted(() => {
  inputRef.value?.focus()
})

onUnmounted(() => {
  clearTimeout(debounceTimer)
})

watch(
  () => props.modelValue,
  (v) => {
    localValue.value = v
  }
)

function onInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  localValue.value = value
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('update:modelValue', value)
  }, 300)
}

function clear() {
  localValue.value = ''
  emit('update:modelValue', '')
}
</script>

<template>
  <div
    class="relative flex items-center rounded-xl border transition-all duration-200"
    :class="isFocused
      ? 'border-blue-400 dark:border-blue-600 ring-2 ring-blue-100 dark:ring-blue-900/50 bg-white dark:bg-gray-800 shadow-sm'
      : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:bg-white dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
  >
    <Search
      class="ml-3 shrink-0 transition-colors duration-200"
      :class="isFocused ? 'text-blue-500 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'"
      :size="16"
    />
    <input
      ref="inputRef"
      :value="localValue"
      @input="onInput"
      @focus="isFocused = true"
      @blur="isFocused = false"
      type="text"
      placeholder="Search items... (F1 or /)"
      aria-label="Search items"
      class="flex-1 bg-transparent pl-2 pr-2 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none placeholder-gray-400 dark:placeholder-gray-500"
    />
    <div class="flex items-center gap-0.5 mr-1.5">
      <button
        v-if="localValue"
        @click="clear"
        aria-label="Clear search"
        class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <X :size="14" />
      </button>
      <button
        v-if="isTouchDevice"
        @click="emit('openScanner')"
        class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
        title="Scan barcode"
        aria-label="Scan barcode"
      >
        <ScanBarcode :size="16" />
      </button>
    </div>
  </div>
</template>
