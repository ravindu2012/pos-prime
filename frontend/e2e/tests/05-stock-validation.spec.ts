import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Stock Validation', () => {
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

  test('should allow adding stock items with available stock', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)

    const cartCount = await pos.getCartItemCount()
    expect(cartCount).toBe(1)
  })

  test('should always allow adding non-stock items', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.nonStock)

    const cartCount = await pos.getCartItemCount()
    expect(cartCount).toBe(1)

    // Add multiple — non-stock items should not be limited
    for (let i = 0; i < 5; i++) {
      await pos.increaseQty(0)
      await posPage.waitForTimeout(200)
    }

    // Should still be in cart without stock errors
    const finalCount = await pos.getCartItemCount()
    expect(finalCount).toBe(1)
  })

  test('should submit non-stock item invoice without stock errors', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.nonStock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should submit stock item successfully when stock is available', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('validate_stock_on_save=OFF should allow invoice submission', async ({ posPage, testData, api }) => {
    // Ensure POS Profile has validate_stock_on_save = 0
    await api.setDocValue('POS Profile', testData.posProfile, 'validate_stock_on_save', 0)

    await pos.addItemBySearch(testData.items.stock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })
})
