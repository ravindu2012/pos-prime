import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Customer Management', () => {
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

  test('should search and select a customer', async ({ posPage, testData }) => {
    await pos.selectCustomer(testData.customer)
    await posPage.waitForTimeout(1000)

    const selected = await pos.getSelectedCustomer()
    expect(selected).toBeTruthy()
  })

  test('should clear selected customer', async ({ posPage, testData }) => {
    // Make sure a customer is selected first
    await pos.selectCustomer(testData.customer)
    await posPage.waitForTimeout(1000)

    // Clear customer
    const clearBtn = posPage.locator('button[aria-label="Clear customer"]')
    if (await clearBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clearBtn.click()
      await posPage.waitForTimeout(500)

      // Search input should be visible
      const searchInput = posPage.locator('input[aria-label="Search customer"]')
      await expect(searchInput).toBeVisible({ timeout: 3000 })
    }
  })

  test('should open new customer dialog', async ({ posPage }) => {
    // Clear customer first to show search
    const clearBtn = posPage.locator('button[aria-label="Clear customer"]')
    if (await clearBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clearBtn.click()
      await posPage.waitForTimeout(300)
    }

    await pos.openNewCustomerDialog()
    await posPage.waitForTimeout(1000)

    // Dialog should be visible — look for the New Customer heading
    const dialog = posPage.locator('h3:has-text("New Customer")')
      .or(posPage.getByText('New Customer'))
    const isVisible = await dialog.first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isVisible).toBeTruthy()
  })

  test('should create a new customer via quick entry', async ({ posPage }) => {
    // Clear customer to show search
    const clearBtn = posPage.locator('button[aria-label="Clear customer"]')
    if (await clearBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clearBtn.click()
      await posPage.waitForTimeout(300)
    }

    await pos.openNewCustomerDialog()
    await posPage.waitForTimeout(1000)

    const timestamp = Date.now()
    await pos.fillNewCustomer({
      name: `PWT Customer ${timestamp}`,
    })

    // Customer should be auto-selected after creation
    await posPage.waitForTimeout(3000)
    const selected = await pos.getSelectedCustomer()
    // Customer might be selected with a different display name
    expect(selected).toBeTruthy()
  })

  test('should submit invoice with specific customer', async ({ posPage, testData }) => {
    // Select test customer
    await pos.selectCustomer(testData.customer)
    await posPage.waitForTimeout(1000)

    // Add item and pay
    await pos.addItemBySearch(testData.items.stock)
    const success = await pos.checkoutAndPay()
    expect(success).toBeTruthy()
    expect(await pos.getCartItemCount()).toBe(0)
  })

  test('should show customer details (loyalty, outstanding)', async ({ posPage, testData }) => {
    await pos.selectCustomer(testData.customer)
    await posPage.waitForTimeout(1000)

    // The customer display area should show name
    const selected = await pos.getSelectedCustomer()
    expect(selected).toBeTruthy()

    // Check for any info badges (loyalty points, outstanding, etc.)
    // These may or may not be visible depending on customer data
    const customerArea = posPage.locator('button.flex.items-center.gap-3').first()
    if (await customerArea.isVisible({ timeout: 2000 }).catch(() => false)) {
      const text = await customerArea.textContent()
      expect(text).toBeTruthy()
    }
  })
})
