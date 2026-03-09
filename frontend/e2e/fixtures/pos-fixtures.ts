import { test as base, expect, type Page } from '@playwright/test'
import { FrappeAPI } from './frappe-api'

export interface TestData {
  customer: string
  customerName: string
  posProfile: string
  warehouse: string
  company: string
  items: {
    stock: string
    nonStock: string
  }
}

/**
 * Extended Playwright test fixture with POS-specific setup.
 *
 * Instead of creating synthetic test data (which fails on sites with
 * custom item groups / missing "All Item Groups"), this fixture discovers
 * the existing POS Profile and picks real items from the site.
 */
export const test = base.extend<{
  api: FrappeAPI
  testData: TestData
  posPage: Page
}>({
  api: async ({ playwright, baseURL }, use) => {
    const request = await playwright.request.newContext({ ignoreHTTPSErrors: true })
    const api = new FrappeAPI(request, baseURL!)
    await api.login('Administrator', 'admin')
    await use(api)
    await request.dispose()
  },

  testData: async ({ api }, use) => {
    const data = await discoverTestData(api)
    await use(data)
  },

  posPage: async ({ page, baseURL }, use) => {
    // Login via browser
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(500)

    // Check if already logged in
    const currentUrl = page.url()
    if (currentUrl.includes('/login')) {
      await page.locator('input[type="text"]#login_email, input[data-fieldname="usr"]').first().fill('Administrator')
      await page.locator('input[type="password"]#login_password, input[data-fieldname="pwd"]').first().fill('admin')
      await page.locator('button[type="submit"], .btn-login, .btn-primary-dark').first().click()
      await page.waitForURL('**/app/**', { timeout: 15_000 }).catch(() => {
        // v16 uses /desk/ instead of /app/
      })
      await page.waitForTimeout(1000)
    }

    // Navigate to POS Prime
    await page.goto(`${baseURL}/pos-prime`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)

    await use(page)
  },
})

export { expect }

// ── Discover existing site data ─────────────────────────────────────────────

// Cache to avoid re-discovering on every test
let _cachedTestData: TestData | null = null

async function discoverTestData(api: FrappeAPI): Promise<TestData> {
  if (_cachedTestData) return _cachedTestData
  // 1. Find the first POS Profile assigned to Administrator
  const profiles = await api.getList(
    'POS Profile',
    {},
    ['name', 'company', 'warehouse', 'customer', 'selling_price_list'],
    10
  )
  if (!profiles.length) throw new Error('No POS Profile found on site')

  // Prefer one that has Administrator in applicable_for_users
  let profile = profiles[0]
  for (const p of profiles) {
    const doc = await api.getDoc('POS Profile', p.name)
    const users = doc?.applicable_for_users || []
    if (users.some((u: any) => u.user === 'Administrator')) {
      profile = { ...p, ...doc }
      break
    }
  }

  const posProfile = profile.name
  const company = profile.company
  const warehouse = profile.warehouse
  const priceList = profile.selling_price_list || 'Standard Selling'

  // 2. Find a customer
  let customer = profile.customer
  if (!customer) {
    const customers = await api.getList('Customer', {}, ['name'], 1)
    customer = customers[0]?.name || 'Guest'
  }

  // 3. Find stock items that have price in this price list and stock in the warehouse
  const stockItem = await findStockItem(api, priceList, warehouse, company)
  const nonStockItem = await findNonStockItem(api, priceList)

  if (!stockItem) throw new Error(`No stock item with price found in price list "${priceList}"`)
  if (!nonStockItem) {
    // If no non-stock item, just reuse the stock item
    console.log('Warning: no non-stock item found, reusing stock item for nonStock tests')
  }

  // Disable stock validation and pricing rules so tests aren't blocked by
  // stock errors or free-item pricing rules adding out-of-stock items
  try {
    await api.setDocValue('POS Profile', posProfile, 'validate_stock_on_save', 0)
  } catch {
    // Field may not exist on all versions
  }
  try {
    await api.setDocValue('POS Profile', posProfile, 'ignore_pricing_rule', 1)
  } catch {
    // Field may not exist on all versions
  }

  // Disable "Product" type Pricing Rules that add free items (these can add
  // out-of-stock items to invoices, causing submission failures)
  try {
    const productRules = await api.getList(
      'Pricing Rule',
      { disable: 0, price_or_product_discount: 'Product' },
      ['name'],
      50
    )
    for (const rule of productRules) {
      await api.setDocValue('Pricing Rule', rule.name, 'disable', 1)
    }
    if (productRules.length) {
      console.log(`Disabled ${productRules.length} product pricing rules for testing`)
    }
  } catch {
    // May fail on some versions
  }

  _cachedTestData = {
    customer,
    customerName: customer,
    posProfile,
    warehouse,
    company,
    items: {
      stock: stockItem,
      nonStock: nonStockItem || stockItem,
    },
  }
  return _cachedTestData
}

async function findStockItem(
  api: FrappeAPI,
  priceList: string,
  warehouse: string,
  company: string
): Promise<string | null> {
  // Strategy: Find bins with actual stock in the warehouse, then check if
  // the item has a selling price. This is faster than iterating price list entries.
  const bins = await api.getList(
    'Bin',
    { warehouse, actual_qty: ['>', 5] },
    ['item_code', 'actual_qty'],
    50
  )

  // Pre-fetch product bundle item codes to skip them (single API call)
  const bundles = await api.getList('Product Bundle', {}, ['new_item_code'], 100)
  const bundleItems = new Set(bundles.map((b: any) => b.new_item_code))

  // Get price list items for cross-reference
  const prices = await api.getList(
    'Item Price',
    { price_list: priceList, selling: 1 },
    ['item_code'],
    200
  )
  const pricedItems = new Set(prices.map((p: any) => p.item_code))

  // Sort bins by qty descending to prefer items with more stock
  bins.sort((a: any, b: any) => (b.actual_qty || 0) - (a.actual_qty || 0))

  for (const bin of bins) {
    if (!pricedItems.has(bin.item_code)) continue
    if (bundleItems.has(bin.item_code)) continue

    const item = await api.getDoc('Item', bin.item_code)
    if (!item || item.disabled || !item.is_stock_item) continue

    return bin.item_code
  }

  // Fallback: try items with lower stock (> 0)
  const lowBins = await api.getList(
    'Bin',
    { warehouse, actual_qty: ['>', 0] },
    ['item_code'],
    20
  )
  for (const bin of lowBins) {
    if (!pricedItems.has(bin.item_code)) continue
    if (bundleItems.has(bin.item_code)) continue

    const item = await api.getDoc('Item', bin.item_code)
    if (!item || item.disabled || !item.is_stock_item) continue

    return bin.item_code
  }

  // Last resort: any stock item with a price, ignore stock level
  for (const p of prices) {
    if (bundleItems.has(p.item_code)) continue
    const item = await api.getDoc('Item', p.item_code)
    if (item && !item.disabled && item.is_stock_item) return p.item_code
  }

  return null
}

async function findNonStockItem(
  api: FrappeAPI,
  priceList: string
): Promise<string | null> {
  const prices = await api.getList(
    'Item Price',
    { price_list: priceList, selling: 1 },
    ['item_code'],
    50
  )

  for (const p of prices) {
    const item = await api.getDoc('Item', p.item_code)
    if (item && !item.disabled && !item.is_stock_item) return p.item_code
  }

  return null
}
