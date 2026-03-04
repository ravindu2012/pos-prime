import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call } from 'frappe-ui'
import { session } from './session'

export const usePosSessionStore = defineStore('posSession', () => {
  const openingEntry = ref<string | null>(null)
  const posProfile = ref<string>('')
  const company = ref<string>('')
  const isOpen = ref(false)
  const loading = ref(false)

  const hasOpenShift = computed(() => isOpen.value && !!openingEntry.value)

  async function checkOpeningEntry() {
    loading.value = true
    try {
      // check_opening_entry returns a LIST of open POS Opening Entries
      const data = await call(
        'posify.api.pos_session.check_opening_entry',
        { user: session.user.data }
      )
      const openVouchers = Array.isArray(data) ? data : []
      if (openVouchers.length > 0) {
        openingEntry.value = openVouchers[0].name
        posProfile.value = openVouchers[0].pos_profile
        company.value = openVouchers[0].company
        isOpen.value = true
      }
      return openVouchers
    } finally {
      loading.value = false
    }
  }

  async function createOpeningEntry(args: {
    pos_profile: string
    company: string
    balance_details: { mode_of_payment: string; opening_amount: number }[]
  }) {
    loading.value = true
    try {
      const data = await call(
        'posify.api.pos_session.create_opening_entry',
        {
          pos_profile: args.pos_profile,
          company: args.company,
          balance_details: JSON.stringify(args.balance_details),
        }
      )
      if (data.name) {
        openingEntry.value = data.name
        posProfile.value = args.pos_profile
        company.value = args.company
        isOpen.value = true
      }
      return data
    } finally {
      loading.value = false
    }
  }

  async function closeShift(closingAmounts: {
    mode_of_payment: string
    closing_amount: number
  }[]) {
    loading.value = true
    try {
      const data = await call('posify.api.pos_session.close_shift', {
        opening_entry: openingEntry.value,
        closing_amounts: closingAmounts,
      })
      $reset()
      return data
    } finally {
      loading.value = false
    }
  }

  function $reset() {
    openingEntry.value = null
    posProfile.value = ''
    company.value = ''
    isOpen.value = false
    loading.value = false
  }

  return {
    openingEntry,
    posProfile,
    company,
    isOpen,
    loading,
    hasOpenShift,
    checkOpeningEntry,
    createOpeningEntry,
    closeShift,
    $reset,
  }
})
