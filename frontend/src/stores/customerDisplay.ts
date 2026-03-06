import { defineStore } from 'pinia'
import { ref } from 'vue'
import { call } from 'frappe-ui'
import type { Customer, CustomerAddress, CustomerContact } from '@/types'
import type { LoyaltyData } from '@/stores/customer'

export interface CustomerInvoice {
  name: string
  posting_date: string
  grand_total: number
  status: string
  is_return: boolean
  currency: string
  total_qty: number
}

export interface CustomerOutstanding {
  outstanding: number
  credit_limit: number
}

export const useCustomerDisplayStore = defineStore('customerDisplay', () => {
  // List state
  const customers = ref<{ name: string; customer_name: string; mobile_no: string | null; email_id: string | null; last_invoice_date?: string }[]>([])
  const recentCustomers = ref<{ name: string; customer_name: string; mobile_no: string | null; email_id: string | null; last_invoice_date?: string }[]>([])
  const searchTerm = ref('')
  const listLoading = ref(false)

  // Detail state
  const selectedCustomer = ref<Customer | null>(null)
  const addresses = ref<CustomerAddress[]>([])
  const contacts = ref<CustomerContact[]>([])
  const loyaltyData = ref<LoyaltyData | null>(null)
  const invoices = ref<CustomerInvoice[]>([])
  const outstanding = ref<CustomerOutstanding>({ outstanding: 0, credit_limit: 0 })
  const detailLoading = ref(false)

  async function loadRecentCustomers() {
    listLoading.value = true
    try {
      const data = await call('posify.api.customers.get_recent_customers', { limit: 20 })
      recentCustomers.value = data || []
    } catch {
      recentCustomers.value = []
    } finally {
      listLoading.value = false
    }
  }

  async function searchCustomers(term: string) {
    searchTerm.value = term
    if (!term || term.length < 2) {
      customers.value = []
      return
    }
    listLoading.value = true
    try {
      const data = await call('posify.api.customers.search_customers', {
        search_term: term,
        pos_profile: '',
      })
      customers.value = data || []
    } catch {
      customers.value = []
    } finally {
      listLoading.value = false
    }
  }

  async function loadCustomerDetail(customerName: string) {
    detailLoading.value = true
    try {
      const [doc, addrData, contactData, invoiceData, outstandingData] = await Promise.all([
        call('frappe.client.get', { doctype: 'Customer', name: customerName }),
        call('posify.api.addresses.get_customer_addresses', { customer: customerName }).catch(() => []),
        call('posify.api.addresses.get_customer_contacts', { customer: customerName }).catch(() => []),
        call('posify.api.customer_profile.get_customer_pos_invoices', { customer: customerName }).catch(() => []),
        call('posify.api.customer_profile.get_customer_outstanding', { customer: customerName }).catch(() => ({ outstanding: 0, credit_limit: 0 })),
      ])

      selectedCustomer.value = {
        name: doc.name,
        customer_name: doc.customer_name,
        email_id: doc.email_id,
        mobile_no: doc.mobile_no,
        loyalty_program: doc.loyalty_program,
        loyalty_points: 0,
        territory: doc.territory,
        customer_group: doc.customer_group,
        tax_id: doc.tax_id,
      }

      addresses.value = addrData || []
      contacts.value = contactData || []
      invoices.value = invoiceData || []
      outstanding.value = outstandingData || { outstanding: 0, credit_limit: 0 }

      // Fetch loyalty if applicable
      loyaltyData.value = null
      if (doc.loyalty_program) {
        try {
          const loyalty = await call('posify.api.loyalty.get_customer_loyalty', { customer: customerName })
          if (loyalty) {
            loyaltyData.value = loyalty
            selectedCustomer.value!.loyalty_points = loyalty.loyalty_points
          }
        } catch {
          // ignore
        }
      }
    } catch (e) {
      selectedCustomer.value = null
    } finally {
      detailLoading.value = false
    }
  }

  function $reset() {
    customers.value = []
    recentCustomers.value = []
    searchTerm.value = ''
    listLoading.value = false
    selectedCustomer.value = null
    addresses.value = []
    contacts.value = []
    loyaltyData.value = null
    invoices.value = []
    outstanding.value = { outstanding: 0, credit_limit: 0 }
    detailLoading.value = false
  }

  return {
    customers,
    recentCustomers,
    searchTerm,
    listLoading,
    selectedCustomer,
    addresses,
    contacts,
    loyaltyData,
    invoices,
    outstanding,
    detailLoading,
    loadRecentCustomers,
    searchCustomers,
    loadCustomerDetail,
    $reset,
  }
})
