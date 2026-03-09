import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call } from 'frappe-ui'
import Fuse from 'fuse.js'
import type { Item } from '@/types'

export const useItemsStore = defineStore('items', () => {
  const allItems = ref<Item[]>([])
  const searchTerm = ref('')
  const selectedGroup = ref('All Item Groups')
  const itemGroups = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  let fuse: Fuse<Item> | null = null

  function buildIndex() {
    fuse = new Fuse(allItems.value, {
      keys: [
        { name: 'item_name', weight: 0.5 },
        { name: 'item_code', weight: 0.3 },
        { name: 'barcode', weight: 0.15 },
        { name: 'barcodes', weight: 0.15 },
      ],
      threshold: 0.4,
      distance: 200,
      ignoreLocation: true,
    })
  }

  const filteredItems = computed(() => {
    let items = allItems.value

    // Filter by group
    if (selectedGroup.value && selectedGroup.value !== 'All Item Groups') {
      items = items.filter(i => i.item_group === selectedGroup.value)
    }

    // Fuzzy search
    const term = searchTerm.value.trim()
    if (term && fuse) {
      const results = fuse.search(term)
      if (selectedGroup.value && selectedGroup.value !== 'All Item Groups') {
        return results
          .filter(r => r.item.item_group === selectedGroup.value)
          .map(r => r.item)
      }
      return results.map(r => r.item)
    }

    return items
  })

  async function fetchAllItems(posProfile?: string) {
    loading.value = true
    error.value = null
    try {
      const { usePosSessionStore } = await import('@/stores/posSession')
      const session = usePosSessionStore()
      const profile = posProfile || session.posProfile || ''

      const data = await call('pos_prime.api.items.get_items', {
        start: 0,
        page_length: 5000,
        search_term: '',
        item_group: '',
        pos_profile: profile,
      })

      allItems.value = data.items || []
      buildIndex()
    } catch (e) {
      error.value = 'Failed to load items'
    } finally {
      loading.value = false
    }
  }

  async function fetchItemGroups(posProfile?: string) {
    try {
      const { usePosSessionStore } = await import('@/stores/posSession')
      const session = usePosSessionStore()
      const profile = posProfile || session.posProfile || ''

      const data = await call('pos_prime.api.items.get_item_groups', {
        pos_profile: profile,
      })
      itemGroups.value = ['All Item Groups', ...(data || [])]
    } catch {
      itemGroups.value = ['All Item Groups']
    }
  }

  async function searchByBarcode(barcode: string, posProfile?: string) {
    try {
      const { usePosSessionStore } = await import('@/stores/posSession')
      const session = usePosSessionStore()
      const profile = posProfile || session.posProfile || ''

      const data = await call(
        'pos_prime.api.items.search_barcode',
        { search_value: barcode, pos_profile: profile }
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
    allItems.value = []
    searchTerm.value = ''
    selectedGroup.value = 'All Item Groups'
    itemGroups.value = []
    loading.value = false
    error.value = null
    fuse = null
  }

  return {
    allItems,
    items: filteredItems,
    filteredItems,
    searchTerm,
    selectedGroup,
    itemGroups,
    loading,
    error,
    fetchAllItems,
    fetchItemGroups,
    searchByBarcode,
    setSearchTerm,
    setSelectedGroup,
    $reset,
  }
})
