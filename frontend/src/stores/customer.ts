import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { call } from 'frappe-ui'
import type { Customer, CustomerAddress, CustomerContact } from '@/types'

export interface LoyaltyData {
  loyalty_program: string
  loyalty_points: number
  conversion_factor: number
  expense_account: string
  cost_center: string
  max_redeemable_amount: number
}

export const useCustomerStore = defineStore('customer', () => {
  const customer = ref<Customer | null>(null)
  const loading = ref(false)
  const loyaltyData = ref<LoyaltyData | null>(null)
  const addresses = ref<CustomerAddress[]>([])
  const contacts = ref<CustomerContact[]>([])
  const selectedAddress = ref<string | null>(null)
  const selectedShippingAddress = ref<string | null>(null)
  const selectedContact = ref<string | null>(null)
  const outstanding = ref(0)
  const creditLimit = ref(0)
  const storeCredit = ref(0)

  const loyaltyProgram = computed(() => loyaltyData.value?.loyalty_program ?? null)
  const loyaltyPoints = computed(() => loyaltyData.value?.loyalty_points ?? 0)
  const maxRedeemableAmount = computed(() => loyaltyData.value?.max_redeemable_amount ?? 0)

  async function searchCustomers(searchTerm: string, posProfile?: string) {
    try {
      const data = await call('pos_prime.api.customers.search_customers', {
        search_term: searchTerm,
        pos_profile: posProfile || '',
      })
      return data || []
    } catch {
      return []
    }
  }

  async function setCustomer(customerName: string) {
    loading.value = true
    try {
      const data = await call('pos_prime.api.customers.get_customer', {
        customer_name: customerName,
      })
      customer.value = {
        name: data.name,
        customer_name: data.customer_name,
        email_id: data.email_id,
        mobile_no: data.mobile_no,
        loyalty_program: data.loyalty_program,
        loyalty_points: 0,
        territory: data.territory,
        customer_group: data.customer_group,
      }

      // Fetch loyalty data
      loyaltyData.value = null
      if (data.loyalty_program) {
        try {
          const loyalty = await call('pos_prime.api.loyalty.get_customer_loyalty', {
            customer: customerName,
          })
          if (loyalty) {
            loyaltyData.value = loyalty
            customer.value.loyalty_points = loyalty.loyalty_points
          }
        } catch {
          // Ignore loyalty fetch errors
        }
      }

      // Fetch addresses and contacts
      addresses.value = []
      contacts.value = []
      selectedAddress.value = null
      selectedShippingAddress.value = null
      selectedContact.value = null
      try {
        const [addrData, contactData] = await Promise.all([
          call('pos_prime.api.addresses.get_customer_addresses', { customer: customerName }),
          call('pos_prime.api.addresses.get_customer_contacts', { customer: customerName }),
        ])
        addresses.value = addrData || []
        contacts.value = contactData || []

        // Auto-select primary address
        const primaryAddr = addresses.value.find((a) => a.is_primary_address)
        if (primaryAddr) selectedAddress.value = primaryAddr.name

        // Auto-select primary shipping address
        const shippingAddr = addresses.value.find((a) => a.is_shipping_address)
        if (shippingAddr) selectedShippingAddress.value = shippingAddr.name

        // Auto-select primary contact
        const primaryContact = contacts.value.find((c) => c.is_primary_contact)
        if (primaryContact) selectedContact.value = primaryContact.name
      } catch {
        // Ignore address/contact fetch errors
      }

      // Fetch outstanding, credit limit, and store credit
      try {
        const { usePosSessionStore } = await import('@/stores/posSession')
        const session = usePosSessionStore()
        const company = session.company || ''
        const [outstandingData, storeCreditData] = await Promise.all([
          call('pos_prime.api.customer_profile.get_customer_outstanding', {
            customer: customerName,
            company,
          }),
          call('pos_prime.api.customer_profile.get_store_credit', {
            customer: customerName,
            company,
          }),
        ])
        outstanding.value = outstandingData?.outstanding || 0
        creditLimit.value = outstandingData?.credit_limit || 0
        storeCredit.value = storeCreditData?.total_advance || 0
      } catch {
        outstanding.value = 0
        creditLimit.value = 0
        storeCredit.value = 0
      }
    } finally {
      loading.value = false
    }
  }

  async function quickCreateCustomer(args: {
    customer_name: string
    mobile_no?: string
    email_id?: string
    customer_type?: string
    customer_group?: string
    pos_profile?: string
    [key: string]: string | undefined
  }) {
    loading.value = true
    try {
      const data = await call('pos_prime.api.customers.quick_create_customer', args)
      if (data) {
        await setCustomer(data)
      }
      return data
    } finally {
      loading.value = false
    }
  }

  function setSelectedAddress(name: string | null) {
    selectedAddress.value = name
  }

  function setSelectedShippingAddress(name: string | null) {
    selectedShippingAddress.value = name
  }

  function setSelectedContact(name: string | null) {
    selectedContact.value = name
  }

  function $reset() {
    customer.value = null
    loyaltyData.value = null
    addresses.value = []
    contacts.value = []
    selectedAddress.value = null
    selectedShippingAddress.value = null
    selectedContact.value = null
    outstanding.value = 0
    creditLimit.value = 0
    storeCredit.value = 0
    loading.value = false
  }

  return {
    customer,
    loading,
    loyaltyData,
    addresses,
    contacts,
    selectedAddress,
    selectedShippingAddress,
    selectedContact,
    outstanding,
    creditLimit,
    storeCredit,
    loyaltyProgram,
    loyaltyPoints,
    maxRedeemableAmount,
    searchCustomers,
    setCustomer,
    quickCreateCustomer,
    setSelectedAddress,
    setSelectedShippingAddress,
    setSelectedContact,
    $reset,
  }
})
