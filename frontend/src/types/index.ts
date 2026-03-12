// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

export interface POSProfile {
  name: string
  company: string
  warehouse: string
  currency: string
  write_off_account: string
  write_off_cost_center: string
  selling_price_list: string
  customer: string
  income_account: string
  expense_account: string
  cost_center: string
  taxes_and_charges: string
  tax_category: string
  apply_discount_on: string
  item_groups: POSItemGroup[]
  payments: POSPaymentMethod[]
  // POS Profile settings flags
  allow_discount_change: boolean
  allow_rate_change: boolean
  allow_partial_payment: boolean
  hide_images: boolean
  hide_unavailable_items: boolean
  auto_add_item_to_cart: boolean
  disable_rounded_total: boolean
  disable_grand_total_to_default_mop: boolean
  ignore_pricing_rule: boolean
  validate_stock_on_save: boolean
  print_receipt_on_order_complete: boolean
  campaign: string | null
  company_address: string | null
  account_for_change_amount: string | null
  write_off_limit: number
  applicable_for_users: { user: string }[]
  customer_groups: { customer_group: string }[]
  letter_head: string | null
  print_format: string | null
  tc_name: string | null
  select_print_heading: string | null
  project: string | null
}

export interface POSItemGroup {
  item_group: string
}

export interface POSPaymentMethod {
  mode_of_payment: string
  default: boolean
  allow_in_returns: boolean
}

export interface Item {
  item_code: string
  item_name: string
  description: string
  item_group: string
  stock_uom: string
  image: string | null
  rate: number
  actual_qty: number
  is_stock_item: boolean
  currency: string
  has_batch_no: boolean
  has_serial_no: boolean
  brand: string | null
  weight_per_unit: number | null
  weight_uom: string | null
  barcode: string | null
  barcodes?: string[]
  item_tax_template: string | null
  is_product_bundle: boolean
}

export interface CartItem {
  item_code: string
  item_name: string
  rate: number
  qty: number
  amount: number
  uom: string
  discount_percentage: number
  discount_amount: number
  image: string | null
  stock_uom: string
  has_serial_no: boolean
  has_batch_no: boolean
  serial_no: string | null
  batch_no: string | null
  serial_and_batch_bundle: string | null
  conversion_factor: number
  // Extended fields
  item_tax_template: string | null
  margin_type: string | null
  margin_rate_or_amount: number
  description: string | null
  project: string | null
  weight_per_unit: number | null
  weight_uom: string | null
  // Pricing rule fields
  is_free_item?: boolean
  pricing_rules?: string | null
  price_list_rate?: number | null
}

export interface TaxRow {
  charge_type: string
  account_head: string
  description: string
  rate: number
  tax_amount: number
  total: number
  base_tax_amount?: number
  base_total?: number
}

export interface Customer {
  name: string
  customer_name: string
  email_id: string | null
  mobile_no: string | null
  loyalty_program: string | null
  loyalty_points: number
  territory: string | null
  customer_group: string | null
  tax_id?: string | null
}

export interface CustomerAddress {
  name: string
  address_title: string
  address_type: string
  address_line1: string
  address_line2: string | null
  city: string
  state: string | null
  pincode: string | null
  country: string
  phone: string | null
  email_id: string | null
  is_primary_address: boolean
  is_shipping_address: boolean
  display: string
}

export interface CustomerContact {
  name: string
  first_name: string
  last_name: string | null
  full_name: string
  email_id: string | null
  phone: string | null
  mobile_no: string | null
  is_primary_contact: boolean
  is_billing_contact: boolean
}

export interface PaymentEntry {
  mode_of_payment: string
  amount: number
}

export interface InvoiceOptions {
  // Address & contact
  customer_address?: string | null
  shipping_address_name?: string | null
  contact_person?: string | null
  // Currency
  conversion_rate?: number | null
  price_list_currency?: string | null
  plc_conversion_rate?: number | null
  // Commission
  sales_partner?: string | null
  commission_rate?: number | null
  // Document details
  project?: string | null
  cost_center?: string | null
  remarks?: string | null
  po_no?: string | null
  po_date?: string | null
  set_posting_time?: boolean
  posting_date?: string | null
  posting_time?: string | null
  naming_series?: string | null
  // Shipping & terms
  shipping_rule?: string | null
  tc_name?: string | null
  terms?: string | null
  // Printing
  letter_head?: string | null
  select_print_heading?: string | null
  group_same_items?: boolean
  language?: string | null
  // Payment terms
  payment_terms_template?: string | null
  allocate_advances_automatically?: boolean
  // Write-off
  write_off_amount?: number
  debit_to?: string | null
  // Sales team
  sales_team?: { sales_person: string; allocated_percentage: number }[]
}

export interface POSInvoice {
  name: string
  naming_series?: string | null
  status: string
  docstatus: number
  owner?: string
  modified?: string | null

  // Customer
  customer: string
  customer_name: string
  tax_id?: string | null

  // Address & contact
  customer_address?: string | null
  address_display?: string | null
  contact_person?: string | null
  contact_display?: string | null
  contact_mobile?: string | null
  contact_email?: string | null
  territory?: string | null
  shipping_address_name?: string | null
  shipping_address?: string | null
  company_address?: string | null
  company_address_display?: string | null

  // Company & dates
  company?: string
  pos_profile?: string
  posting_date: string
  posting_time: string
  set_posting_time?: boolean
  due_date?: string | null

  // Currency
  currency: string
  conversion_rate?: number | null
  selling_price_list?: string | null
  price_list_currency?: string | null
  plc_conversion_rate?: number | null

  // Totals
  total_qty?: number
  total?: number
  net_total: number
  grand_total: number
  rounded_total: number
  rounding_adjustment: number
  in_words?: string | null

  // Base currency totals
  base_total?: number
  base_net_total?: number
  base_grand_total?: number
  base_rounded_total?: number
  base_rounding_adjustment?: number
  base_in_words?: string | null

  // Payment
  paid_amount: number
  base_paid_amount?: number
  change_amount: number
  base_change_amount?: number
  outstanding_amount?: number
  total_advance?: number
  account_for_change_amount?: string | null

  // Taxes
  taxes_and_charges?: string | null
  tax_category?: string | null
  shipping_rule?: string | null
  total_taxes_and_charges: number
  base_total_taxes_and_charges?: number

  // Discount
  apply_discount_on?: string
  additional_discount_percentage: number
  discount_amount: number
  base_discount_amount?: number
  coupon_code: string | null

  // Loyalty
  loyalty_points: number
  loyalty_amount: number
  redeem_loyalty_points?: boolean
  loyalty_program?: string | null
  loyalty_redemption_account?: string | null
  loyalty_redemption_cost_center?: string | null

  // Return
  is_return: boolean
  return_against: string | null

  // Write-off
  write_off_amount: number
  base_write_off_amount?: number
  write_off_account?: string | null
  write_off_cost_center?: string | null

  // Commission
  sales_partner?: string | null
  commission_rate?: number | null
  total_commission?: number | null

  // Document details
  project?: string | null
  cost_center?: string | null
  po_no?: string | null
  po_date?: string | null
  remarks?: string | null
  campaign?: string | null

  // Printing
  letter_head?: string | null
  select_print_heading?: string | null
  group_same_items?: boolean
  language?: string | null
  print_format?: string | null

  // Payment terms
  payment_terms_template?: string | null
  allocate_advances_automatically?: boolean

  // Consolidated
  consolidated_invoice?: string | null
  is_discounted?: boolean

  // Weight
  total_net_weight?: number

  // Child tables
  items: InvoiceItem[]
  payments: PaymentEntry[]
  taxes: TaxRow[]
}

export interface InvoiceItem {
  item_code: string
  item_name: string
  description?: string | null
  item_group?: string | null
  brand?: string | null
  qty: number
  stock_qty?: number
  rate: number
  amount: number
  price_list_rate?: number
  base_rate?: number
  base_amount?: number
  net_rate?: number
  net_amount?: number
  uom: string
  stock_uom?: string
  conversion_factor?: number
  discount_percentage: number
  discount_amount?: number
  margin_type?: string | null
  margin_rate_or_amount?: number
  rate_with_margin?: number
  item_tax_template?: string | null
  item_tax_rate?: string | null
  is_free_item?: boolean
  serial_no: string | null
  batch_no: string | null
  serial_and_batch_bundle?: string | null
  actual_qty?: number
  warehouse?: string
  income_account?: string
  expense_account?: string
  cost_center?: string
  project?: string | null
  weight_per_unit?: number
  total_weight?: number
  weight_uom?: string | null
}

export interface OpeningEntry {
  pos_profile: string
  company: string
  period_start_date: string
  balance_details: {
    mode_of_payment: string
    opening_amount: number
  }[]
}

export interface ClosingEntry {
  pos_profile: string
  company: string
  pos_opening_entry: string
  period_end_date: string
  grand_total: number
  net_total: number
  total_quantity: number
  payment_reconciliation: {
    mode_of_payment: string
    opening_amount: number
    expected_amount: number
    closing_amount: number
    difference: number
  }[]
}
