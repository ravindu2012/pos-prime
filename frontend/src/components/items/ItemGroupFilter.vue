<script setup lang="ts">
defineProps<{
  groups: string[]
  selected: string
}>()

const emit = defineEmits<{
  select: [group: string]
}>()
</script>

<template>
  <!-- Desktop sidebar list -->
  <div class="hidden lg:block w-48 shrink-0 bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800 overflow-y-auto">
    <div class="p-2">
      <div class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest px-3 py-2">
        Categories
      </div>
      <button
        v-for="group in groups"
        :key="group"
        @click="emit('select', group)"
        class="w-full text-left px-3 py-2 rounded-lg text-sm transition-all duration-150"
        :class="
          selected === group
            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-semibold'
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-800 dark:hover:text-gray-200'
        "
      >
        {{ group }}
      </button>
    </div>
  </div>

  <!-- Mobile/tablet horizontal scroll -->
  <div class="lg:hidden flex gap-1.5 overflow-x-auto px-3 py-2 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 no-scrollbar">
    <button
      v-for="group in groups"
      :key="group"
      @click="emit('select', group)"
      class="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150"
      :class="
        selected === group
          ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/20'
          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
      "
    >
      {{ group }}
    </button>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
