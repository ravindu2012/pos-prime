import { defineStore } from 'pinia'
import { ref } from 'vue'
import { call } from 'frappe-ui'
import type { Item } from '@/types'

let fetchRequestId = 0

export const useItemsStore = defineStore('items', () => {
  const items = ref<Item[]>([])
  const searchTerm = ref('')
  const selectedGroup = ref('All Item Groups')
  const itemGroups = ref<string[]>([])
  const loading = ref(false)
  const pageLength = ref(20)
  const hasMore = ref(true)
  const error = ref<string | null>(null)

  async function fetchItems(start = 0, posProfile?: string) {
    const currentId = ++fetchRequestId
    loading.value = true
    try {
      // Lazy import to avoid circular deps
      const { usePosSessionStore } = await import('@/stores/posSession')
      const session = usePosSessionStore()

      const profile = posProfile || session.posProfile || ''

      const data = await call('posify.api.items.get_items', {
        start,
        page_length: pageLength.value,
        search_term: searchTerm.value,
        item_group: selectedGroup.value === 'All Item Groups' ? '' : selectedGroup.value,
        pos_profile: profile,
      })

      if (currentId !== fetchRequestId) return []

      const newItems: Item[] = data.items || []

      if (start === 0) {
        items.value = newItems
      } else {
        items.value = [...items.value, ...newItems]
      }
      hasMore.value = newItems.length === pageLength.value
      return newItems
    } catch (e) {
      if (currentId !== fetchRequestId) return []
      error.value = 'Failed to load items'
      return []
    } finally {
      if (currentId === fetchRequestId) {
        loading.value = false
      }
    }
  }

  async function fetchItemGroups(posProfile?: string) {
    try {
      const { usePosSessionStore } = await import('@/stores/posSession')
      const session = usePosSessionStore()
      const profile = posProfile || session.posProfile || ''

      const data = await call('posify.api.items.get_item_groups', {
        pos_profile: profile,
      })
      itemGroups.value = ['All Item Groups', ...(data || [])]
    } catch {
      itemGroups.value = ['All Item Groups']
    }
  }

  async function searchByBarcode(barcode: string) {
    try {
      const data = await call(
        'posify.api.items.search_barcode',
        { search_value: barcode }
      )
      return data
    } catch {
      return null
    }
  }

  function setSearchTerm(term: string) {
    searchTerm.value = term
  }

  function setSelectedGroup(group: string) {
    selectedGroup.value = group
  }

  function $reset() {
    items.value = []
    searchTerm.value = ''
    selectedGroup.value = 'All Item Groups'
    itemGroups.value = []
    hasMore.value = true
    loading.value = false
    pageLength.value = 20
    error.value = null
    fetchRequestId++
  }

  return {
    items,
    searchTerm,
    selectedGroup,
    itemGroups,
    loading,
    hasMore,
    fetchItems,
    fetchItemGroups,
    error,
    searchByBarcode,
    setSearchTerm,
    setSelectedGroup,
    $reset,
  }
})
