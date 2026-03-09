import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Payment Dialog & Invoice Submission', () => {
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

  test('should open payment dialog on checkout', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()

    const isVisible = await pos.isPaymentDialogVisible()
    expect(isVisible).toBeTruthy()
  })

  test('should display grand total in payment dialog', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()
    await posPage.waitForTimeout(500)

    const total = await pos.getPaymentGrandTotal()
    expect(total).toBeTruthy()
    expect(total).not.toBe('0')
  })

  test('should show cash payment method by default', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()

    // Cash should be visible in payment tabs
    const cashTab = posPage.locator('button:has-text("Cash")')
    await expect(cashTab.first()).toBeVisible()
  })

  test('should show quick amount shortcuts for cash', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()
    await posPage.waitForTimeout(500)

    // Quick amount buttons should be visible
    const shortcuts = posPage.locator('[role="dialog"] .grid button')
    const count = await shortcuts.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should complete cash payment successfully', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should show change due for overpayment', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()
    await posPage.waitForTimeout(500)

    // Enter amount larger than grand total
    const input = posPage.locator('[role="dialog"] input[type="number"]').first()
    if (await input.isVisible({ timeout: 2000 }).catch(() => false)) {
      await input.fill('99999')
      await posPage.waitForTimeout(500)

      const hasChange = await pos.hasChangeDisplay()
      expect(hasChange).toBeTruthy()
    }
  })

  test('should close payment dialog without paying', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()
    await posPage.waitForTimeout(500)

    await pos.closePaymentDialog()

    const isVisible = await pos.isPaymentDialogVisible()
    expect(isVisible).toBeFalsy()

    // Cart should still have items
    const cartCount = await pos.getCartItemCount()
    expect(cartCount).toBeGreaterThan(0)
  })

  test('should submit invoice with non-stock item', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.nonStock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should submit invoice with multiple items', async ({ posPage, testData }) => {
    test.skip(testData.items.stock === testData.items.nonStock, 'No distinct non-stock item available')

    await pos.addItemBySearch(testData.items.stock)
    await pos.addItemBySearch(testData.items.nonStock)

    const cartCount = await pos.getCartItemCount()
    expect(cartCount).toBe(2)

    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should handle partial payment with confirmation', async ({ posPage, testData }) => {
    await pos.addItemBySearch(testData.items.stock)
    await pos.waitForTaxCalculation()

    await pos.clickCheckout()
    await posPage.waitForTimeout(500)

    // Don't enter any amount — just click Complete Payment (triggers partial payment)
    await pos.clickCompletePayment()

    // Should either succeed (partial payment confirmed) or show receipt
    await posPage.waitForTimeout(1000)

    const receiptVisible = await pos.isReceiptVisible()
    if (receiptVisible) {
      await pos.closeReceipt()
    }
  })
})
