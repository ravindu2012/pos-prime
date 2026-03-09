import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Draft / Held Orders', () => {
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

  test('should hold/save order as draft', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await posPage.waitForTimeout(500)

    // Click hold order
    await pos.holdOrder()

    // Cart should be cleared after holding
    const cartCount = await pos.getCartItemCount()
    expect(cartCount).toBe(0)
  })

  test('should show held orders drawer', async ({ posPage, testData }) => {
    // First create a held order
    await pos.addItemBySearch(testData.items.stock)
    await pos.holdOrder()

    // Open held orders
    await pos.openHeldOrders()
    await posPage.waitForTimeout(1000)

    // Should see the held orders drawer/dialog
    const drawer = posPage.locator('[role="dialog"][aria-label*="Held"]')
      .or(posPage.getByText('Held Orders'))
    const isVisible = await drawer.first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isVisible).toBeTruthy()
  })

  test('should resume a held order', async ({ posPage, testData }) => {
    // Create a held order
    await pos.addItemBySearch(testData.items.stock)
    await pos.holdOrder()

    // Open held orders and resume
    await pos.openHeldOrders()
    await posPage.waitForTimeout(1000)

    await pos.resumeHeldOrder(0)
    await posPage.waitForTimeout(2000)

    // Cart should now have items from the resumed order
    const cartCount = await pos.getCartItemCount()
    expect(cartCount).toBeGreaterThanOrEqual(1)
  })

  test('should submit a previously held order', async ({ posPage, testData }) => {
    // Create and hold an order
    await pos.addItemBySearch(testData.items.stock)
    await pos.holdOrder()

    // Resume it
    await pos.openHeldOrders()
    await posPage.waitForTimeout(1000)
    await pos.resumeHeldOrder(0)
    await posPage.waitForTimeout(2000)

    // Now checkout and pay
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })
})
