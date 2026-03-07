import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call } from 'frappe-ui'
import type { POSProfile } from '@/types'

export const useSettingsStore = defineStore('settings', () => {
  const posProfile = ref<POSProfile | null>(null)
  const posProfiles = ref<{ name: string; company: string }[]>([])
  const loading = ref(false)

  // Computed settings flags
  const allowDiscountChange = computed(() => posProfile.value?.allow_discount_change ?? false)
  const allowRateChange = computed(() => posProfile.value?.allow_rate_change ?? false)
  const allowPartialPayment = computed(() => posProfile.value?.allow_partial_payment ?? false)
  const hideImages = computed(() => posProfile.value?.hide_images ?? false)
  const hideUnavailableItems = computed(() => posProfile.value?.hide_unavailable_items ?? false)
  const autoAddItemToCart = computed(() => posProfile.value?.auto_add_item_to_cart ?? false)
  const disableRoundedTotal = computed(() => posProfile.value?.disable_rounded_total ?? false)
  const disableGrandTotalToDefaultMop = computed(() => posProfile.value?.disable_grand_total_to_default_mop ?? false)
  const ignorePricingRule = computed(() => posProfile.value?.ignore_pricing_rule ?? false)
  const validateStockOnSave = computed(() => posProfile.value?.validate_stock_on_save ?? false)
  const printReceiptOnOrderComplete = computed(() => posProfile.value?.print_receipt_on_order_complete ?? false)
  const writeOffLimit = computed(() => posProfile.value?.write_off_limit ?? 0)
  const accountForChangeAmount = computed(() => posProfile.value?.account_for_change_amount ?? null)
  const currency = computed(() => posProfile.value?.currency ?? 'USD')
  const erpnextVersion = computed(() => (posProfile.value as any)?.erpnext_version ?? 15)

  const paymentMethods = computed(() => posProfile.value?.payments ?? [])
  const defaultPaymentMethod = computed(() =>
    paymentMethods.value.find((p) => p.default)?.mode_of_payment ?? paymentMethods.value[0]?.mode_of_payment ?? 'Cash'
  )

  const customerGroups = computed(() =>
    (posProfile.value?.customer_groups ?? []).map((g) => g.customer_group)
  )

  async function fetchPOSProfiles() {
    loading.value = true
    try {
      // Get POS profiles and open entry in a single call
      const data = await call('pos_prime.api.pos_session.get_opening_data')
      posProfiles.value = data?.pos_profiles || []

      return {
        profiles: posProfiles.value,
        openEntry: data?.opening_entry || null,
      }
    } finally {
      loading.value = false
    }
  }

  async function loadPOSProfile(profileName: string) {
    loading.value = true
    try {
      const data = await call(
        'pos_prime.api.pos_session.get_pos_profile',
        { pos_profile: profileName }
      )
      posProfile.value = data as POSProfile
      return data
    } finally {
      loading.value = false
    }
  }

  function $reset() {
    posProfile.value = null
    posProfiles.value = []
    loading.value = false
  }

  return {
    posProfile,
    posProfiles,
    loading,
    allowDiscountChange,
    allowRateChange,
    allowPartialPayment,
    hideImages,
    hideUnavailableItems,
    autoAddItemToCart,
    disableRoundedTotal,
    disableGrandTotalToDefaultMop,
    ignorePricingRule,
    validateStockOnSave,
    printReceiptOnOrderComplete,
    writeOffLimit,
    accountForChangeAmount,
    currency,
    erpnextVersion,
    paymentMethods,
    defaultPaymentMethod,
    customerGroups,
    fetchPOSProfiles,
    loadPOSProfile,
    $reset,
  }
})
