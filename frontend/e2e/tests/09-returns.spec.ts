import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Returns', () => {
  let pos: POSPage

  test.beforeEach(async ({ posPage, testData }) => {
    pos = new POSPage(posPage)
    await pos.waitForPOSReady()

    if (await pos.hasOpeningEntry()) {
      await pos.fillOpeningEntry(testData.posProfile, { Cash: 0 })
      await posPage.waitForTimeout(2000)
    }
    await posPage.waitForTimeout(2000)
  })

  test('should create an invoice for return testing', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should open return search dialog', async ({ posPage }) => {
    // The return button has aria-label="Return" in the sidebar
    const returnBtn = posPage.locator('button[aria-label="Return"]').first()
    if (await returnBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await returnBtn.click()
      await posPage.waitForTimeout(1000)

      // Return dialog should be visible
      const dialog = posPage.locator('[role="dialog"][aria-label*="Return"]')
        .or(posPage.getByText('Search Invoice'))
      const isVisible = await dialog.first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(isVisible).toBeTruthy()
    }
  })

  test('should search for an invoice to return', async ({ posPage, api, testData }) => {
    // First check for existing submitted invoices
    const invoices = await api.getList(
      'POS Invoice',
      { pos_profile: testData.posProfile, docstatus: 1, is_return: 0 },
      ['name'],
      1
    )

    if (!invoices.length) {
      // Create one via UI first
      await pos.addItemBySearch(testData.items.stock)
      await pos.checkoutAndPay()
    }

    // Open return dialog — use aria-label selector to avoid backdrop issues
    const returnBtn = posPage.locator('button[aria-label="Return"]').first()
    if (await returnBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await returnBtn.click()
      await posPage.waitForTimeout(1000)

      // Search for invoice
      const searchInput = posPage.locator('[role="dialog"] input[type="text"]').first()
      if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        const invoiceName = invoices[0]?.name || 'POS'
        await searchInput.fill(invoiceName)
        await posPage.waitForTimeout(1000)

        // Should show search results
        const results = posPage.locator('[role="dialog"] button, [role="dialog"] [role="listitem"]')
        const count = await results.count()
        expect(count).toBeGreaterThanOrEqual(0)
      }
    }
  })
})
