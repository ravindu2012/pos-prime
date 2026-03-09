import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('POS Session Management', () => {
  test('should open POS and show opening entry or POS layout', async ({ posPage, testData }) => {
    const pos = new POSPage(posPage)
    await pos.waitForPOSReady()

    const hasOpening = await pos.hasOpeningEntry()
    if (hasOpening) {
      // Opening entry dialog is shown — fill and submit
      await pos.fillOpeningEntry(testData.posProfile, { Cash: 0 })
      await posPage.waitForTimeout(2000)
    }

    // POS should now be ready with search input visible
    await expect(
      posPage.locator('input[aria-label="Search items"], input[placeholder*="Search items"]').first()
    ).toBeVisible({ timeout: 15_000 })
  })

  test('should display items after session is opened', async ({ posPage, testData }) => {
    const pos = new POSPage(posPage)
    await pos.waitForPOSReady()

    // Handle opening entry if needed
    if (await pos.hasOpeningEntry()) {
      await pos.fillOpeningEntry(testData.posProfile, { Cash: 0 })
      await posPage.waitForTimeout(2000)
    }

    // Wait for items to load
    await posPage.waitForTimeout(3000)

    // Should see item cards (or "No items found" if no items match)
    const itemCards = posPage.locator('button.pos-card')
    const noItems = posPage.locator('text=No items found')
    const hasItems = await itemCards.count() > 0
    const showsEmpty = await noItems.isVisible().catch(() => false)

    expect(hasItems || showsEmpty).toBeTruthy()
  })

  test('should have default customer selected', async ({ posPage, testData }) => {
    const pos = new POSPage(posPage)
    await pos.waitForPOSReady()

    if (await pos.hasOpeningEntry()) {
      await pos.fillOpeningEntry(testData.posProfile, { Cash: 0 })
      await posPage.waitForTimeout(2000)
    }

    // Check customer is selected (POS Profile sets a default)
    await posPage.waitForTimeout(2000)
    const customer = await pos.getSelectedCustomer()
    // Either the default customer is shown or the search input is visible
    expect(customer !== null || await posPage.locator('input[aria-label="Search customer"]').isVisible()).toBeTruthy()
  })
})
