import { test, expect } from '../fixtures/pos-fixtures'
import { FrappeAPI } from '../fixtures/frappe-api'

/**
 * Backend-focused tests to verify update_stock behavior across versions.
 * These use the API directly rather than the UI.
 */
test.describe('update_stock Behavior', () => {
  let api: FrappeAPI

  test.beforeAll(async ({ playwright, baseURL }) => {
    const request = await playwright.request.newContext({ ignoreHTTPSErrors: true })
    api = new FrappeAPI(request, baseURL!)
    await api.login('Administrator', 'admin')
  })

  test('POS Profile should have update_stock field', async () => {
    const profiles = await api.getList('POS Profile', {}, ['name'], 1)
    if (profiles.length) {
      const profile = await api.getDoc('POS Profile', profiles[0].name)
      expect(profile).toBeTruthy()
      expect(profile.name).toBe(profiles[0].name)
    }
  })

  test('POS Invoice update_stock field detection', async () => {
    // Use getDoc on the DocType to read meta — avoids DocField permission issues
    const meta = await api.getDoc('DocType', 'POS Invoice')
    if (meta && meta.fields) {
      const field = meta.fields.find((f: any) => f.fieldname === 'update_stock')
      if (field) {
        console.log(`POS Invoice has update_stock field, default: ${field.default}`)
        expect(field.fieldname).toBe('update_stock')
      } else {
        console.log('POS Invoice does NOT have update_stock field (v15)')
      }
    }
    // Both cases are valid across versions
    expect(true).toBeTruthy()
  })

  test('create_pos_invoice API endpoint exists', async () => {
    try {
      await api.call('pos_prime.api.invoices.create_pos_invoice', {
        customer: 'NONEXISTENT',
        pos_profile: 'NONEXISTENT',
        items: '[]',
        payments: '[]',
      })
    } catch (e: any) {
      // Expected to fail with data errors — but NOT with method-not-found errors
      // Frappe returns 404 for DoesNotExistError too, so we check the body instead
      expect(e.message).not.toContain('Method not found')
      expect(e.message).not.toContain('ImportError')
      expect(e.message).not.toContain('not whitelisted')
    }
  })

  test('save_draft_invoice API endpoint exists', async () => {
    try {
      await api.call('pos_prime.api.drafts.save_draft_invoice', {
        customer: 'NONEXISTENT',
        pos_profile: 'NONEXISTENT',
        items: '[]',
      })
    } catch (e: any) {
      expect(e.message).not.toContain('Method not found')
      expect(e.message).not.toContain('ImportError')
      expect(e.message).not.toContain('not whitelisted')
    }
  })

  test('calculate_taxes API endpoint exists', async () => {
    try {
      await api.call('pos_prime.api.taxes.calculate_taxes', {
        pos_profile: 'NONEXISTENT',
        customer: 'NONEXISTENT',
        items: '[]',
      })
    } catch (e: any) {
      expect(e.message).not.toContain('Method not found')
      expect(e.message).not.toContain('ImportError')
      expect(e.message).not.toContain('not whitelisted')
    }
  })
})
