<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const props = defineProps<{
  itemCode: string
  currentUom: string
}>()

const emit = defineEmits<{
  select: [uom: string, conversionFactor: number]
}>()

const uoms = ref<{ uom: string; conversion_factor: number }[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await call('pos_prime.api.stock.get_item_uoms', {
      item_code: props.itemCode,
    })
    uoms.value = data || []
  } finally {
    loading.value = false
  }
})

function selectUom(uom: string, factor: number) {
  emit('select', uom, factor)
}
</script>

<template>
  <select
    v-if="uoms.length > 1"
    :value="currentUom"
    @change="(e) => {
      const uom = (e.target as HTMLSelectElement).value
      const match = uoms.find(u => u.uom === uom)
      if (match) selectUom(match.uom, match.conversion_factor)
    }"
    class="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-1.5 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
  >
    <option v-for="u in uoms" :key="u.uom" :value="u.uom">
      {{ u.uom }}
    </option>
  </select>
  <span v-else class="text-xs text-gray-400 dark:text-gray-500">{{ currentUom }}</span>
</template>
