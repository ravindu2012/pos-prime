<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from 'lucide-vue-next'

const props = defineProps<{
  groups: string[]
  selected: string
  mode?: 'desktop' | 'mobile'
}>()

const emit = defineEmits<{
  select: [group: string]
}>()

const SEARCH_THRESHOLD = 10
const searchTerm = ref('')

const showSearch = computed(() => props.groups.length > SEARCH_THRESHOLD)

const filteredGroups = computed(() => {
  if (!searchTerm.value) return props.groups
  const term = searchTerm.value.toLowerCase()
  return props.groups.filter((g) => g.toLowerCase().includes(term))
})
</script>

<template>
  <!-- Desktop sidebar list -->
  <div
    v-if="mode === 'desktop'"
    class="w-48 shrink-0 bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800 flex flex-col"
  >
    <div class="p-2 flex flex-col min-h-0 flex-1">
      <div class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest px-3 py-2">
        Categories
      </div>
      <div v-if="showSearch" class="px-2 pb-2">
        <div class="relative">
          <Search class="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" :size="12" />
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Filter..."
            class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 pl-7 pr-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 placeholder-gray-400 dark:placeholder-gray-500"
          />
        </div>
      </div>
      <div class="overflow-y-auto flex-1 no-scrollbar">
        <button
          v-for="group in filteredGroups"
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
        <div v-if="filteredGroups.length === 0" class="px-3 py-2 text-xs text-gray-400 dark:text-gray-500">
          No match
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile/tablet horizontal scroll -->
  <div
    v-else
    class="bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800"
  >
    <div v-if="showSearch" class="px-3 pt-2">
      <div class="relative">
        <Search class="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" :size="12" />
        <input
          v-model="searchTerm"
          type="text"
          placeholder="Filter categories..."
          class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 pl-7 pr-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 placeholder-gray-400 dark:placeholder-gray-500"
        />
      </div>
    </div>
    <div class="flex gap-1.5 overflow-x-auto px-3 py-2 no-scrollbar">
      <button
        v-for="group in filteredGroups"
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
      <div v-if="filteredGroups.length === 0" class="text-xs text-gray-400 dark:text-gray-500 py-1">
        No match
      </div>
    </div>
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
