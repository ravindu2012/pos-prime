import { defineStore } from 'pinia'
import { ref } from 'vue'
import { call } from 'frappe-ui'
import type { POSInvoice } from '@/types'

let fetchRequestId = 0

export interface OrderSummary {
  name: string
  customer: string
  customer_name: string
  grand_total: number
  net_total: number
  paid_amount: number
  posting_date: string
  posting_time: string
  status: string
  docstatus: number
  is_return: boolean
  return_against: string | null
  owner: string
  modified: string
  currency: string
  total_qty: number
  rounded_total: number
  change_amount: number
  outstanding_amount: number
  total_taxes_and_charges: number
  discount_amount: number
  additional_discount_percentage: number
  write_off_amount: number
  loyalty_points: number
  loyalty_amount: number
  coupon_code: string | null
  sales_partner: string | null
  po_no: string | null
  project: string | null
  remarks: string | null
  consolidated_invoice: string | null
}

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref<OrderSummary[]>([])
  const selectedOrder = ref<POSInvoice | null>(null)
  const searchTerm = ref('')
  const statusFilter = ref('')
  const loading = ref(false)
  const loadingDetail = ref(false)
  const hasMore = ref(true)
  const error = ref<string | null>(null)
  const pageSize = 20

  async function fetchOrders(posProfile: string, start = 0) {
    const currentId = ++fetchRequestId
    loading.value = true
    try {
      const data = await call('posify.api.orders.get_past_orders', {
        pos_profile: posProfile,
        search_term: searchTerm.value,
        status: statusFilter.value,
        limit: pageSize,
        start,
      })

      if (currentId !== fetchRequestId) return

      const newOrders = data || []
      if (start === 0) {
        orders.value = newOrders
      } else {
        orders.value = [...orders.value, ...newOrders]
      }
      hasMore.value = newOrders.length === pageSize
    } catch {
      if (currentId !== fetchRequestId) return
      error.value = 'Failed to load orders'
      if (start === 0) orders.value = []
    } finally {
      if (currentId === fetchRequestId) {
        loading.value = false
      }
    }
  }

  async function loadOrderDetail(invoiceName: string) {
    loadingDetail.value = true
    try {
      const data = await call('posify.api.orders.get_order_detail', {
        invoice_name: invoiceName,
      })
      selectedOrder.value = data
      return data
    } catch {
      error.value = 'Failed to load order'
      selectedOrder.value = null
      return null
    } finally {
      loadingDetail.value = false
    }
  }

  async function createReturn(sourceInvoice: string) {
    try {
      const data = await call('posify.api.orders.create_return_invoice', {
        source_invoice: sourceInvoice,
      })
      return data
    } catch {
      error.value = 'Failed to create return'
      return null
    }
  }

  function setSearchTerm(term: string) {
    searchTerm.value = term
  }

  function setStatusFilter(status: string) {
    statusFilter.value = status
  }

  function $reset() {
    orders.value = []
    selectedOrder.value = null
    searchTerm.value = ''
    statusFilter.value = ''
    hasMore.value = true
    loading.value = false
    loadingDetail.value = false
    error.value = null
    fetchRequestId++
  }

  return {
    orders,
    selectedOrder,
    searchTerm,
    statusFilter,
    loading,
    loadingDetail,
    hasMore,
    error,
    fetchOrders,
    loadOrderDetail,
    createReturn,
    setSearchTerm,
    setStatusFilter,
    $reset,
  }
})
