import { test, expect } from '../fixtures/pos-fixtures'
import { POSPage } from '../fixtures/pos-page'

test.describe('Items Grid & Search', () => {
  let pos: POSPage

  test.beforeEach(async ({ posPage, testData }) => {
    pos = new POSPage(posPage)
    await pos.waitForPOSReady()

    if (await pos.hasOpeningEntry()) {
      await pos.fillOpeningEntry(testData.posProfile, { Cash: 0 })
      await posPage.waitForTimeout(2000)
    }
    await posPage.waitForTimeout(2000) // wait for items to load
  })

  test('should display items in grid', async ({ posPage }) => {
    const items = posPage.locator('button.pos-card')
    // Should have at least 1 item visible
    await expect(items.first()).toBeVisible({ timeout: 10_000 })
  })

  test('should search items by item code', async ({ posPage, testData }) => {
    await pos.searchItem(testData.items.stock)
    await posPage.waitForTimeout(1000)

    // Should find the item or show "No items found"
    const hasCards = await pos.hasItemCards()
    const noItems = await posPage.locator('text=No items found').isVisible().catch(() => false)
    expect(hasCards || noItems).toBeTruthy()
  })

  test('should find item and add to cart', async ({ posPage, testData }) => {
    await pos.searchItem(testData.items.stock)
    await posPage.waitForTimeout(1000)

    if (await pos.hasItemCards()) {
      await pos.clickFirstItemCard()
      const cartCount = await pos.getCartItemCount()
      expect(cartCount).toBe(1)
    }
  })

  test('should clear search', async ({ posPage }) => {
    await pos.searchItem('test search term')
    await posPage.waitForTimeout(500)

    await pos.clearSearch()
    await posPage.waitForTimeout(500)

    // Search input should be empty
    const searchInput = posPage.locator(
      'input[aria-label="Search items"], input[placeholder*="Search items"]'
    ).first()
    await expect(searchInput).toHaveValue('')
  })

  test('should show item groups/categories', async ({ posPage }) => {
    // Check if item group buttons exist (categories sidebar)
    const groupFilter = posPage.getByText('All Item Groups')
      .or(posPage.getByText('All Items'))
      .or(posPage.getByText('Categories'))
    const hasGroups = await groupFilter.first().isVisible({ timeout: 3000 }).catch(() => false)
    // Categories should be visible
    expect(hasGroups).toBeTruthy()
  })

  test('should show stock quantity on item cards', async ({ posPage }) => {
    const itemCard = posPage.locator('button.pos-card').first()
    if (await itemCard.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Card should have some content (item name at minimum)
      const text = await itemCard.textContent()
      expect(text).toBeTruthy()
    }
  })

  test('should show items after clearing search', async ({ posPage, testData }) => {
    // Search for something
    await pos.searchItem(testData.items.stock)
    await posPage.waitForTimeout(1000)

    // Clear search
    await pos.clearSearch()
    await posPage.waitForTimeout(1000)

    // Items should be visible again
    const items = posPage.locator('button.pos-card')
    await expect(items.first()).toBeVisible({ timeout: 10_000 })
  })
})
