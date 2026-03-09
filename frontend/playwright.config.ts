import { defineConfig, devices } from '@playwright/test'

/**
 * POS Prime E2E Tests — v14 / v15 / v16
 *
 * Usage:
 *   npx playwright test                    # all versions
 *   npx playwright test --project=v15      # v15 only
 *   npx playwright test --project=v14      # v14 only
 *   npx playwright test --project=v16      # v16 only
 */
export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 120_000,
  expect: { timeout: 15_000 },

  use: {
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'v15',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.V15_URL || 'http://pos.localhost:8000',
      },
    },
    {
      name: 'v14',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.V14_URL || 'http://v14.localhost:8001',
      },
    },
    {
      name: 'v16',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.V16_URL || 'http://v16.localhost:8002',
      },
    },
  ],
})
