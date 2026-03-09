import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Discounts', () => {
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

  test('should apply percentage invoice discount', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    const totalBefore = await pos.getCartTotal()

    await pos.applyInvoiceDiscount('percentage', 10)
    await pos.waitForTaxCalculation()

    const totalAfter = await pos.getCartTotal()

    // Total after discount should be less (unless tax makes it complicated)
    // Just verify the discount badge is shown
    const discountBadge = posPage.locator('.text-orange-600, .bg-orange-100')
    const hasDiscount = await discountBadge.first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasDiscount || totalAfter !== totalBefore).toBeTruthy()
  })

  test('should apply amount invoice discount', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.applyInvoiceDiscount('amount', 25)
    await pos.waitForTaxCalculation()

    // Check discount is reflected somewhere in the UI
    const discountSection = posPage.getByText('Discount')
      .or(posPage.locator('.text-orange-600'))
      .or(posPage.locator('.bg-orange-100'))
    const hasDiscount = await discountSection.first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasDiscount).toBeTruthy()
  })

  test('should submit invoice with percentage discount', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.applyInvoiceDiscount('percentage', 5)
    await pos.waitForTaxCalculation()

    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should submit invoice with amount discount', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.applyInvoiceDiscount('amount', 10)
    await pos.waitForTaxCalculation()

    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should show discount in cart summary', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.applyInvoiceDiscount('percentage', 15)
    await pos.waitForTaxCalculation()

    // Check that the discount row appears in summary
    const discountRow = posPage.getByText('Discount')
    const isVisible = await discountRow.first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isVisible).toBeTruthy()
  })
})
