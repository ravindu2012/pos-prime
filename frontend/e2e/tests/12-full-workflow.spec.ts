import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

/**
 * Full end-to-end workflow tests that exercise the complete POS cycle.
 */
test.describe('Full POS Workflow', () => {
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

  test('complete workflow: search → add → pay → receipt', async ({ posPage, testData }) => {
    // 1. Search for item
    await pos.searchItem(testData.items.stock)
    await posPage.waitForTimeout(1000)

    // 2. Verify item appears
    expect(await pos.hasItemCards()).toBeTruthy()

    // 3. Add to cart
    await pos.clickFirstItemCard()

    // 4. Verify cart has item
    expect(await pos.getCartItemCount()).toBe(1)

    // 5. Checkout and pay
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()

    // 6. Verify cart is cleared
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('workflow with multiple items and quantity changes', async ({ posPage, testData }) => {
    // Add stock item x3
    await pos.addItemBySearch(testData.items.stock)
    await pos.increaseQty(0)
    await pos.increaseQty(0)
    await posPage.waitForTimeout(300)

    const qty = await pos.getCartItemQty(0)
    expect(qty).toBe(3)

    // Checkout and pay
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('workflow with invoice discount', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    // Apply 10% discount
    await pos.applyInvoiceDiscount('percentage', 10)
    await pos.waitForTaxCalculation()

    // Checkout and pay
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('workflow with customer change', async ({ posPage, testData }) => {
    // Select specific customer
    await pos.selectCustomer(testData.customer)
    await posPage.waitForTimeout(1000)

    // Add item and pay
    await pos.addItemBySearch(testData.items.stock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('workflow: hold → resume → pay', async ({ posPage, testData }) => {
    // Add item and hold
    await pos.addItemBySearch(testData.items.stock)
    await posPage.waitForTimeout(500)

    await pos.holdOrder()

    // Cart should be empty
    expect(await pos.getCartItemCount()).toBe(0)

    // Resume held order
    await pos.openHeldOrders()
    await posPage.waitForTimeout(1000)

    await pos.resumeHeldOrder(0)
    await posPage.waitForTimeout(2000)

    // Cart should have the held item
    expect(await pos.getCartItemCount()).toBeGreaterThanOrEqual(1)

    // Pay
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('workflow: add items → remove one → pay remaining', async ({ posPage, testData }) => {
    // Add item twice (qty 2)
    await pos.addItemBySearch(testData.items.stock)
    await pos.increaseQty(0)
    await posPage.waitForTimeout(300)

    expect(await pos.getCartItemQty(0)).toBe(2)

    // Decrease qty back to 1
    await pos.decreaseQty(0)
    await posPage.waitForTimeout(300)

    expect(await pos.getCartItemQty(0)).toBe(1)

    // Pay for remaining
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('consecutive invoices in same session', async ({ posPage, testData }) => {
    // Invoice 1
    await pos.addItemBySearch(testData.items.stock)
    let success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)

    // Invoice 2
    await pos.addItemBySearch(testData.items.stock)
    await pos.increaseQty(0)
    success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)

    // Invoice 3
    await pos.addItemBySearch(testData.items.stock)
    success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })
})
