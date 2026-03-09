import type { Page } from '@playwright/test'
import { expect } from '@playwright/test'

/**
 * Page Object Model for POS Prime UI interactions.
 */
export class POSPage {
  constructor(public page: Page) {}

  // ── Navigation ─────────────────────────────────────────────────────────

  async waitForPOSReady() {
    // Wait for either the POS layout or the opening entry dialog
    await this.page.locator(
      'input[aria-label="Search items"], input[placeholder*="Search items"]'
    ).or(
      this.page.getByText('Opening Entry')
    ).or(
      this.page.getByText('POS Opening Entry')
    ).first().waitFor({ state: 'visible', timeout: 20_000 })
  }

  // ── Opening Entry ──────────────────────────────────────────────────────

  async hasOpeningEntry(): Promise<boolean> {
    return this.page.locator('text=Opening Entry').isVisible({ timeout: 3000 }).catch(() => false)
  }

  async fillOpeningEntry(posProfile: string, amounts: Record<string, number> = {}) {
    // Select POS Profile if dropdown is visible
    const profileSelect = this.page.locator('select, [data-fieldname="pos_profile"]').first()
    if (await profileSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await profileSelect.selectOption({ label: posProfile })
    }

    // Fill opening amounts
    for (const [mode, amount] of Object.entries(amounts)) {
      const row = this.page.locator(`text=${mode}`).locator('..')
      const input = row.locator('input[type="number"]')
      if (await input.isVisible({ timeout: 1000 }).catch(() => false)) {
        await input.fill(String(amount))
      }
    }

    // Submit opening entry
    await this.page.locator('button:has-text("Open POS"), button:has-text("Submit"), button:has-text("Open Session")').first().click()
    await this.page.waitForTimeout(2000)
  }

  // ── Item Search & Selection ────────────────────────────────────────────

  async searchItem(term: string) {
    const searchInput = this.page.locator(
      'input[aria-label="Search items"], input[placeholder*="Search items"]'
    ).first()
    await searchInput.fill(term)
    await this.page.waitForTimeout(500) // debounce
  }

  async clearSearch() {
    const clearBtn = this.page.locator('button[aria-label="Clear search"]')
    if (await clearBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await clearBtn.click()
    }
  }

  async clickFirstItemCard() {
    const card = this.page.locator('button.pos-card').first()
    await card.waitFor({ state: 'visible', timeout: 5000 })
    await card.click()
    await this.page.waitForTimeout(300)
  }

  async hasItemCards(): Promise<boolean> {
    return this.page.locator('button.pos-card').first()
      .isVisible({ timeout: 5000 }).catch(() => false)
  }

  async clickItem(itemName: string) {
    await this.page.locator(`button[aria-label*="${itemName}"], button.pos-card:has-text("${itemName}")`).first().click()
    await this.page.waitForTimeout(300)
  }

  async selectItemGroup(groupName: string) {
    await this.page.locator(`button:has-text("${groupName}")`).first().click()
    await this.page.waitForTimeout(500)
  }

  async getVisibleItemCount(): Promise<number> {
    return this.page.locator('button.pos-card').count()
  }

  // ── Cart Operations ────────────────────────────────────────────────────

  async getCartItemCount(): Promise<number> {
    return this.page.locator('[role="listitem"]').count()
  }

  async getCartItemNames(): Promise<string[]> {
    const items = this.page.locator('[role="listitem"]')
    const count = await items.count()
    const names: string[] = []
    for (let i = 0; i < count; i++) {
      const text = await items.nth(i).locator('span.font-bold.truncate, span.text-sm.font-bold').first().textContent()
      if (text) names.push(text.trim())
    }
    return names
  }

  async getCartItemQty(itemIndex: number): Promise<number> {
    const item = this.page.locator('[role="listitem"]').nth(itemIndex)
    const qtySpan = item.locator('span.w-7.text-center')
    const text = await qtySpan.textContent()
    return parseInt(text?.trim() || '0', 10)
  }

  async increaseQty(itemIndex: number) {
    const item = this.page.locator('[role="listitem"]').nth(itemIndex)
    await item.locator('button[aria-label="Increase quantity"]').click()
    await this.page.waitForTimeout(300)
  }

  async decreaseQty(itemIndex: number) {
    const item = this.page.locator('[role="listitem"]').nth(itemIndex)
    await item.locator('button[aria-label="Decrease quantity"]').click()
    await this.page.waitForTimeout(300)
  }

  async removeItem(itemIndex: number) {
    const item = this.page.locator('[role="listitem"]').nth(itemIndex)
    // Hover to reveal delete button
    await item.hover()
    await item.locator('button[aria-label="Remove item"]').click()
    await this.page.waitForTimeout(300)
  }

  async getCartTotal(): Promise<string> {
    const total = this.page.locator('text=Grand Total').locator('..').locator('span').last()
    return (await total.textContent())?.trim() || '0'
  }

  async getNetTotal(): Promise<string> {
    const net = this.page.locator('text=Net Total').locator('..').locator('span').last()
    return (await net.textContent())?.trim() || '0'
  }

  async getTotalQty(): Promise<string> {
    const qty = this.page.locator('text=Total Qty').locator('..').locator('span').last()
    return (await qty.textContent())?.trim() || '0'
  }

  // ── Customer ───────────────────────────────────────────────────────────

  async selectCustomer(customerName: string) {
    // Click customer area to open search
    const clearBtn = this.page.locator('button[aria-label="Clear customer"]')
    if (await clearBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await clearBtn.click()
      await this.page.waitForTimeout(300)
    }

    const searchInput = this.page.locator('input[aria-label="Search customer"]')
    await searchInput.fill(customerName)
    await this.page.waitForTimeout(1000) // wait for search results

    // Click first result
    await this.page.locator(`button:has-text("${customerName}")`).first().click()
    await this.page.waitForTimeout(500)
  }

  async getSelectedCustomer(): Promise<string | null> {
    // The customer name is in a div with text-sm font-bold truncate inside the customer button
    const customerBtn = this.page.locator('button.flex.items-center.gap-3')
    const name = customerBtn.locator('.text-sm.font-bold.truncate').first()
    if (await name.isVisible({ timeout: 5000 }).catch(() => false)) {
      return (await name.textContent())?.trim() || null
    }
    return null
  }

  async openNewCustomerDialog() {
    await this.page.locator('button[aria-label="New Customer"]').click()
    await this.page.waitForTimeout(500)
  }

  async fillNewCustomer(data: { name: string }) {
    // The POS Prime new customer dialog has: Customer Name (textbox "Full name"),
    // Customer Type, Customer Group, NIC Number, and contact/address sections
    const nameInput = this.page.getByRole('textbox', { name: 'Full name' })
    await nameInput.fill(data.name)
    await this.page.waitForTimeout(300)

    // Click Create button (at the bottom of the dialog)
    await this.page.locator('button:has-text("Create")').click()

    // Wait for the "New Customer" heading to disappear (dialog closing)
    try {
      await this.page.getByRole('heading', { name: 'New Customer' })
        .waitFor({ state: 'hidden', timeout: 10_000 })
    } catch {
      // Dialog may still be open if creation failed
    }
    await this.page.waitForTimeout(1000)
  }

  // ── Discount ───────────────────────────────────────────────────────────

  async applyInvoiceDiscount(type: 'percentage' | 'amount', value: number) {
    // Open discount section
    await this.page.locator('button:has-text("Invoice Discount"), button:has-text("More Options")').first().click()
    await this.page.waitForTimeout(300)

    // Select type
    if (type === 'percentage') {
      await this.page.locator('button:has-text("Percent")').click()
    } else {
      await this.page.locator('button:has-text("Amount")').click()
    }

    // Enter value
    const input = this.page.locator('input[type="number"][step="0.01"]').last()
    await input.fill(String(value))
    await this.page.waitForTimeout(1000) // wait for tax recalculation
  }

  // ── Payment ────────────────────────────────────────────────────────────

  async clickCheckout() {
    await this.page.locator('button.checkout-btn, button:has-text("Checkout")').first().click()
    await this.page.waitForTimeout(1000)
  }

  async isPaymentDialogVisible(): Promise<boolean> {
    return this.page.locator('[role="dialog"][aria-modal="true"]').isVisible({ timeout: 3000 }).catch(() => false)
  }

  async selectPaymentMethod(method: string) {
    await this.page.locator(`button:has-text("${method}")`).first().click()
    await this.page.waitForTimeout(300)
  }

  async enterPaymentAmount(amount: number) {
    const input = this.page.locator('[role="dialog"] input[type="number"]').first()
    if (await input.isVisible({ timeout: 1000 }).catch(() => false)) {
      await input.fill(String(amount))
    }
    await this.page.waitForTimeout(300)
  }

  /** Click the first quick-amount button to pay the full grand total */
  async clickFullPaymentShortcut() {
    // The first quick amount button is the grand total
    const shortcut = this.page.locator('[role="dialog"] .grid button').first()
    if (await shortcut.isVisible({ timeout: 2000 }).catch(() => false)) {
      await shortcut.click()
      await this.page.waitForTimeout(300)
    }
  }

  async clickCompletePayment() {
    await this.page.locator('button:has-text("Complete Payment")').click()
    await this.page.waitForTimeout(1000)

    // Handle "Partial Payment" confirmation if it appears
    const partialConfirm = this.page.locator('button:has-text("Confirm")')
    if (await partialConfirm.isVisible({ timeout: 2000 }).catch(() => false)) {
      await partialConfirm.click()
    }

    await this.page.waitForTimeout(3000) // wait for submission
  }

  /** Full payment flow: enter full amount via shortcut then complete */
  async payFullAmount() {
    await this.clickFullPaymentShortcut()
    await this.page.locator('button:has-text("Complete Payment")').click()
    await this.page.waitForTimeout(4000) // wait for submission
  }

  async closePaymentDialog() {
    await this.page.locator('button[aria-label="Close payment dialog"]').click()
    await this.page.waitForTimeout(500)
  }

  async getPaymentGrandTotal(): Promise<string> {
    const total = this.page.locator('[role="dialog"] .text-3xl.font-bold')
    return (await total.textContent())?.trim() || '0'
  }

  async hasChangeDisplay(): Promise<boolean> {
    return this.page.locator('text=Change Due').isVisible({ timeout: 1000 }).catch(() => false)
  }

  async getChangeAmount(): Promise<string> {
    const change = this.page.locator('text=Change Due').locator('..').locator('.text-xl.font-bold')
    return (await change.textContent())?.trim() || '0'
  }

  // ── Receipt ────────────────────────────────────────────────────────────

  async isReceiptVisible(): Promise<boolean> {
    return this.page.locator('[role="dialog"][aria-label="Receipt"]')
      .or(this.page.getByText('Payment Successful'))
      .or(this.page.getByText('Print Receipt'))
      .first()
      .isVisible({ timeout: 5000 }).catch(() => false)
  }

  async closeReceipt() {
    // Target the "New Order" button specifically inside the Receipt dialog
    const receiptDialog = this.page.locator('[role="dialog"][aria-label="Receipt"]')
    const newOrderBtn = receiptDialog.locator('button:has-text("New Order")')
    if (await newOrderBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await newOrderBtn.click()
    } else {
      // Fallback: any close/done button
      await this.page.locator('button:has-text("New Order")').first().click({ force: true })
    }
    // Wait for the receipt dialog to close
    try {
      await receiptDialog.waitFor({ state: 'hidden', timeout: 5000 })
    } catch {
      // Already closed
    }
    await this.page.waitForTimeout(500)
  }

  // ── Drafts / Held Orders ───────────────────────────────────────────────

  async holdOrder() {
    // The hold button has title="Hold Order" with only a Pause icon (no text)
    const holdBtn = this.page.locator('button[title="Hold Order"]')
    await holdBtn.waitFor({ state: 'visible', timeout: 5000 })
    await holdBtn.click()
    // Wait for cart to clear (hold saves draft and resets cart)
    try {
      await this.page.locator('[role="listitem"]').first().waitFor({ state: 'hidden', timeout: 10_000 })
    } catch {
      // Cart items may have already cleared
    }
    await this.page.waitForTimeout(500)
  }

  async openHeldOrders() {
    // The held orders button has aria-label="Held Orders" with only an icon (no text)
    await this.page.locator('button[aria-label="Held Orders"]').first().click()
    await this.page.waitForTimeout(1000)
  }

  async resumeHeldOrder(index: number) {
    await this.page.locator('button:has-text("Resume")').nth(index).click()
    await this.page.waitForTimeout(1000)
  }

  // ── Returns ────────────────────────────────────────────────────────────

  async openReturnDialog() {
    await this.page.locator('button:has-text("Return")').first().click()
    await this.page.waitForTimeout(1000)
  }

  // ── Utility ────────────────────────────────────────────────────────────

  async waitForTaxCalculation() {
    // Wait for the tax calculation indicator to disappear
    await this.page.waitForTimeout(1500)
  }

  async hasErrorAlert(): Promise<boolean> {
    return this.page.locator('.bg-red-50, .alert-danger, [role="alert"]').isVisible({ timeout: 2000 }).catch(() => false)
  }

  async getErrorMessage(): Promise<string> {
    const alert = this.page.locator('.bg-red-50, .alert-danger, [role="alert"]').first()
    return (await alert.textContent())?.trim() || ''
  }

  // ── Composite Helpers ──────────────────────────────────────────────────

  /** Search for an item and add the first result to cart */
  async addItemBySearch(itemCode: string) {
    await this.searchItem(itemCode)
    await this.page.waitForTimeout(1500) // wait for search results to load
    if (await this.hasItemCards()) {
      await this.clickFirstItemCard()
      await this.page.waitForTimeout(1000) // wait for cart update + API call
    }
    await this.clearSearch()
    await this.page.waitForTimeout(500)
  }

  /** Check if there's an error message in the payment dialog */
  async hasPaymentError(): Promise<boolean> {
    const errorDiv = this.page.locator('[role="dialog"][aria-label="Payment"] .bg-red-50, [role="dialog"][aria-label="Payment"] .text-red-600, [role="dialog"][aria-label="Payment"] [role="alert"]')
    return errorDiv.first().isVisible({ timeout: 1000 }).catch(() => false)
  }

  /** Full checkout flow: click checkout, pay full amount, close receipt.
   *  Returns true if payment succeeded, false if an error prevented submission. */
  async checkoutAndPay(): Promise<boolean> {
    await this.waitForTaxCalculation()
    await this.clickCheckout()

    const paymentDialog = this.page.locator('[role="dialog"][aria-label="Payment"]')
    await paymentDialog.waitFor({ state: 'visible', timeout: 10_000 })
    await this.page.waitForTimeout(500)

    // Try quick amount shortcut first
    await this.clickFullPaymentShortcut()
    await this.page.waitForTimeout(300)

    // Check if "Complete Payment" button is enabled; if not, enter amount directly
    const completeBtn = paymentDialog.locator('button:has-text("Complete Payment"), button:has-text("Processing")')
      .first()
    const isEnabled = await completeBtn.isEnabled({ timeout: 2000 }).catch(() => false)
    if (!isEnabled) {
      // Fallback: enter the grand total amount into the input
      const input = paymentDialog.locator('input[type="number"]').first()
      if (await input.isVisible({ timeout: 2000 }).catch(() => false)) {
        const totalText = await this.getPaymentGrandTotal()
        const amount = totalText.replace(/[^0-9.]/g, '')
        if (amount) {
          await input.fill(amount)
          await this.page.waitForTimeout(500)
        }
      }
    }

    // Set up API response interception to capture errors
    const responsePromise = this.page.waitForResponse(
      resp => resp.url().includes('create_pos_invoice') || resp.url().includes('pos_prime'),
      { timeout: 30_000 }
    ).catch(() => null)

    // Click Complete Payment
    await completeBtn.click({ timeout: 5000 })
    await this.page.waitForTimeout(500)

    // Handle partial payment confirmation
    const partialConfirm = this.page.locator('button:has-text("Confirm")')
    if (await partialConfirm.isVisible({ timeout: 2000 }).catch(() => false)) {
      await partialConfirm.click()
    }

    // Wait for the API response and log any errors
    const response = await responsePromise
    if (response) {
      try {
        const body = await response.json()
        if (body?.exc || body?._server_messages) {
          const msg = body._server_messages || body.exc
          console.log('Payment API error:', typeof msg === 'string' ? msg.substring(0, 500) : JSON.stringify(msg).substring(0, 500))
        }
      } catch { /* response might not be JSON */ }
    }

    // Wait for the payment dialog to disappear (indicates backend submission completed)
    try {
      await paymentDialog.waitFor({ state: 'hidden', timeout: 30_000 })
    } catch {
      // Dialog still open — capture error message from dialog
      const errorText = await paymentDialog.locator('.text-red-600, .bg-red-50').first()
        .textContent().catch(() => '')
      console.log('Payment dialog error:', errorText)
      await this.closePaymentDialog().catch(() => {})
      await this.page.waitForTimeout(500)
      return false
    }

    // Give a moment for receipt to render
    await this.page.waitForTimeout(1000)

    // Close receipt if visible
    if (await this.isReceiptVisible()) {
      await this.closeReceipt()
      await this.page.waitForTimeout(500)
    }

    return true
  }
}
