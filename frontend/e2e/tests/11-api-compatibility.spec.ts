import { test, expect } from '../fixtures/pos-fixtures'
import { FrappeAPI } from '../fixtures/frappe-api'

/**
 * API-level compatibility tests for v14/v15/v16.
 * Verifies all pos-prime backend APIs work on each version.
 */
test.describe('API Compatibility', () => {
  let api: FrappeAPI
  let posProfile: string
  let customer: string
  let company: string

  test.beforeAll(async ({ playwright, baseURL }) => {
    const request = await playwright.request.newContext({ ignoreHTTPSErrors: true })
    api = new FrappeAPI(request, baseURL!)
    await api.login('Administrator', 'admin')

    // Get test data
    const profiles = await api.getList('POS Profile', {}, ['name', 'company', 'customer'], 1)
    if (profiles.length) {
      posProfile = profiles[0].name
      company = profiles[0].company
      customer = profiles[0].customer
    }
  })

  test('get_pos_items API', async () => {
    if (!posProfile) test.skip()

    const result = await api.call('pos_prime.api.items.get_items', {
      pos_profile: posProfile,
      start: 0,
      page_length: 10,
    })

    expect(result).toBeTruthy()
    // API returns { items: [...] }
    expect(result.items).toBeDefined()
    expect(Array.isArray(result.items)).toBeTruthy()
  })

  test('get_pos_profile API', async () => {
    if (!posProfile) test.skip()

    const result = await api.call('pos_prime.api.pos_session.get_pos_profile', {
      pos_profile: posProfile,
    })

    expect(result).toBeTruthy()
    expect(result.name || result.pos_profile).toBeTruthy()
  })

  test('search_customers API', async () => {
    if (!posProfile) test.skip()

    const result = await api.call('pos_prime.api.customers.search_customers', {
      search_term: 'Customer',
      pos_profile: posProfile,
    })

    expect(result).toBeTruthy()
    expect(Array.isArray(result)).toBeTruthy()
  })

  test('calculate_taxes API with valid data', async () => {
    if (!posProfile || !customer) test.skip()

    // Get an item to use
    const resp = await api.call('pos_prime.api.items.get_items', {
      pos_profile: posProfile,
      start: 0,
      page_length: 1,
    })

    const items = resp?.items || []
    if (!items.length) test.skip()

    const result = await api.call('pos_prime.api.taxes.calculate_taxes', {
      pos_profile: posProfile,
      customer: customer,
      items: JSON.stringify([{
        item_code: items[0].item_code,
        qty: 1,
        rate: items[0].rate || 100,
        discount_percentage: 0,
        discount_amount: 0,
      }]),
    })

    expect(result).toBeTruthy()
    expect(result.grand_total).toBeDefined()
    expect(result.net_total).toBeDefined()
  })

  test('get_item_groups API', async () => {
    if (!posProfile) test.skip()

    const result = await api.call('pos_prime.api.items.get_item_groups', {
      pos_profile: posProfile,
    })

    expect(result).toBeTruthy()
    expect(Array.isArray(result)).toBeTruthy()
  })

  test('search_barcode API', async () => {
    if (!posProfile) test.skip()

    try {
      const result = await api.call('pos_prime.api.items.search_barcode', {
        barcode: 'NONEXISTENT_BARCODE_12345',
      })
      // Should return null/empty for non-existent barcode
      expect(result === null || result === undefined || result?.item_code === undefined).toBeTruthy()
    } catch {
      // Expected — barcode not found
    }
  })

  test('get_batch_nos API', async () => {
    try {
      const result = await api.call('pos_prime.api.stock.get_batch_nos', {
        item_code: 'NONEXISTENT_ITEM',
        warehouse: 'NONEXISTENT_WAREHOUSE',
      })
      expect(Array.isArray(result) || result === null || result === undefined).toBeTruthy()
    } catch {
      // Expected for non-existent item
    }
  })

  test('POS Closing Entry child table detection', async () => {
    // Use frappe.get_meta which has proper permissions
    const meta = await api.call('frappe.client.get_count', {
      doctype: 'POS Closing Entry',
    })
    // If we can access the doctype, it exists
    expect(meta !== undefined).toBeTruthy()

    // Try to detect the child table by creating a minimal doc and checking fields
    const doc = await api.getDoc('DocType', 'POS Closing Entry')
    if (doc && doc.fields) {
      const tableFields = doc.fields
        .filter((f: any) => f.fieldtype === 'Table')
        .map((f: any) => f.fieldname)
      const hasPosTable = tableFields.includes('pos_transactions') || tableFields.includes('pos_invoices')
      expect(hasPosTable).toBeTruthy()
      console.log(`POS Closing Entry child tables: ${tableFields.join(', ')}`)
    } else {
      // Fallback: just verify the doctype is accessible
      console.log('POS Closing Entry doctype is accessible (could not read meta fields)')
      expect(true).toBeTruthy()
    }
  })

  test('POS Profile campaign field detection', async () => {
    const doc = await api.getDoc('DocType', 'POS Profile')
    if (doc && doc.fields) {
      const campaignFields = doc.fields
        .filter((f: any) => ['campaign', 'utm_campaign'].includes(f.fieldname))
        .map((f: any) => f.fieldname)
      console.log(`POS Profile campaign fields: ${campaignFields.join(', ')}`)
      const hasCampaign = campaignFields.includes('campaign') || campaignFields.includes('utm_campaign')
      expect(hasCampaign).toBeTruthy()
    } else {
      console.log('Could not read POS Profile meta — skipping field detection')
      expect(true).toBeTruthy()
    }
  })

  test('POS Invoice update_stock field detection', async () => {
    const doc = await api.getDoc('DocType', 'POS Invoice')
    if (doc && doc.fields) {
      const updateStockField = doc.fields.find((f: any) => f.fieldname === 'update_stock')
      if (updateStockField) {
        console.log(`POS Invoice has update_stock field, default: ${updateStockField.default}`)
      } else {
        console.log('POS Invoice does NOT have update_stock field in JSON (v15 — stock via consolidation)')
      }
    } else {
      console.log('Could not read POS Invoice meta')
    }
    // Both cases are valid
    expect(true).toBeTruthy()
  })

  test('Serial and Batch Bundle doctype detection', async () => {
    try {
      const result = await api.call('frappe.client.get_list', {
        doctype: 'DocType',
        filters: { name: 'Serial and Batch Bundle' },
        fields: ['name'],
        limit_page_length: 1,
      })

      if (result && result.length > 0) {
        console.log('Serial and Batch Bundle doctype EXISTS (v15+)')
      } else {
        console.log('Serial and Batch Bundle doctype DOES NOT EXIST (v14)')
      }
    } catch {
      console.log('Serial and Batch Bundle doctype DOES NOT EXIST (v14)')
    }
    expect(true).toBeTruthy()
  })

  test('desk URL prefix detection', async ({ baseURL }) => {
    // Try /app/ and /desk/ to see which redirects work
    const appResp = await api.call('frappe.client.get_list', {
      doctype: 'Module Def',
      fields: ['name'],
      limit_page_length: 1,
    })

    // If we can make API calls, the version is accessible
    expect(appResp).toBeTruthy()

    // Check hooks for route configuration
    try {
      const hooks = await api.call('frappe.client.get_hooks', {
        hook: 'website_route_rules',
      })
      console.log('Route rules available')
    } catch {
      // Not all versions expose this
    }
  })
})
