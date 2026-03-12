// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { call } from 'frappe-ui'

export interface DraftSummary {
  name: string
  customer: string
  customer_name: string
  grand_total: number
  net_total: number
  posting_date: string
  posting_time: string
  item_count: number
  owner: string
  modified: string
  currency: string
  total_qty: number
  status: string
  remarks: string | null
  sales_partner: string | null
  po_no: string | null
  project: string | null
}

export const useDraftsStore = defineStore('drafts', () => {
  const drafts = ref<DraftSummary[]>([])
  const activeDraftName = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchDrafts(posProfile: string) {
    loading.value = true
    try {
      const data = await call('pos_prime.api.drafts.get_draft_invoices', {
        pos_profile: posProfile,
      })
      drafts.value = data || []
    } catch {
      drafts.value = []
    } finally {
      loading.value = false
    }
  }

  async function saveDraft(args: {
    customer: string
    pos_profile: string
    items: { item_code: string; qty: number; rate: number; discount_percentage?: number; [key: string]: any }[]
    payments?: { mode_of_payment: string; amount: number }[]
  }) {
    loading.value = true
    try {
      const data = await call('pos_prime.api.drafts.save_draft_invoice', args)
      return data
    } finally {
      loading.value = false
    }
  }

  async function loadDraft(invoiceName: string) {
    loading.value = true
    try {
      const data = await call('pos_prime.api.drafts.load_draft_invoice', {
        invoice_name: invoiceName,
      })
      activeDraftName.value = invoiceName
      return data
    } finally {
      loading.value = false
    }
  }

  async function deleteDraft(invoiceName: string) {
    try {
      await call('pos_prime.api.drafts.delete_draft_invoice', {
        invoice_name: invoiceName,
      })
      drafts.value = drafts.value.filter((d) => d.name !== invoiceName)
      if (activeDraftName.value === invoiceName) {
        activeDraftName.value = null
      }
    } catch {
      error.value = 'Failed to delete draft'
    }
  }

  async function submitDraft(args: {
    invoice_name: string
    customer: string
    items: { item_code: string; qty: number; rate: number; discount_percentage?: number; [key: string]: any }[]
    payments: { mode_of_payment: string; amount: number }[]
    taxes?: string
    additional_discount_percentage?: number
    discount_amount?: number
    coupon_code?: string
  }) {
    loading.value = true
    try {
      const data = await call('pos_prime.api.drafts.update_and_submit_draft', args)
      activeDraftName.value = null
      return data
    } finally {
      loading.value = false
    }
  }

  function clearActiveDraft() {
    activeDraftName.value = null
  }

  function $reset() {
    drafts.value = []
    activeDraftName.value = null
    loading.value = false
    error.value = null
  }

  return {
    drafts,
    activeDraftName,
    loading,
    error,
    fetchDrafts,
    saveDraft,
    loadDraft,
    deleteDraft,
    submitDraft,
    clearActiveDraft,
    $reset,
  }
})
