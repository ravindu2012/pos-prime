import type { Page, APIRequestContext } from '@playwright/test'

/**
 * Low-level Frappe API helper for test setup/teardown.
 * Uses Playwright's request context which auto-manages cookies.
 */
export class FrappeAPI {
  private baseURL: string
  private request: APIRequestContext

  constructor(request: APIRequestContext, baseURL: string) {
    this.request = request
    this.baseURL = baseURL
  }

  async login(user = 'Administrator', password = 'admin'): Promise<void> {
    const resp = await this.request.post(`${this.baseURL}/api/method/login`, {
      form: { usr: user, pwd: password },
    })
    if (!resp.ok()) {
      throw new Error(`Login failed: ${resp.status()} ${await resp.text()}`)
    }
    // Playwright's request context automatically stores cookies from the response
  }

  async call(method: string, args: Record<string, any> = {}): Promise<any> {
    const resp = await this.request.post(
      `${this.baseURL}/api/method/${method}`,
      { data: args }
    )
    if (!resp.ok()) {
      const body = await resp.text()
      throw new Error(`API call ${method} failed: ${resp.status()} ${body}`)
    }
    const json = await resp.json()
    return json.message
  }

  async insert(doctype: string, data: Record<string, any>): Promise<any> {
    const resp = await this.request.post(
      `${this.baseURL}/api/resource/${doctype}`,
      { data }
    )
    if (!resp.ok()) {
      const body = await resp.text()
      if (body.includes('DuplicateEntryError') || body.includes('already exists')) {
        return null
      }
      throw new Error(`Insert ${doctype} failed: ${resp.status()} ${body}`)
    }
    const json = await resp.json()
    return json.data
  }

  async getDoc(doctype: string, name: string): Promise<any> {
    const resp = await this.request.get(
      `${this.baseURL}/api/resource/${doctype}/${encodeURIComponent(name)}`
    )
    if (!resp.ok()) return null
    const json = await resp.json()
    return json.data
  }

  async getList(
    doctype: string,
    filters: Record<string, any> = {},
    fields: string[] = ['name'],
    limit = 100
  ): Promise<any[]> {
    const params = new URLSearchParams({
      filters: JSON.stringify(filters),
      fields: JSON.stringify(fields),
      limit_page_length: String(limit),
    })
    const resp = await this.request.get(
      `${this.baseURL}/api/resource/${doctype}?${params}`
    )
    if (!resp.ok()) return []
    const json = await resp.json()
    return json.data || []
  }

  async getValue(doctype: string, name: string, field: string): Promise<any> {
    const doc = await this.getDoc(doctype, name)
    return doc?.[field]
  }

  async deleteDoc(doctype: string, name: string): Promise<boolean> {
    const resp = await this.request.delete(
      `${this.baseURL}/api/resource/${doctype}/${encodeURIComponent(name)}`
    )
    return resp.ok()
  }

  async setDocValue(
    doctype: string,
    name: string,
    field: string,
    value: any
  ): Promise<void> {
    await this.call('frappe.client.set_value', {
      doctype,
      name,
      fieldname: field,
      value,
    })
  }

  async exists(doctype: string, name: string): Promise<boolean> {
    const doc = await this.getDoc(doctype, name)
    return doc !== null
  }
}

/**
 * Login to Frappe via the browser page (sets session cookies).
 */
export async function loginViaPage(
  page: Page,
  baseURL: string,
  user = 'Administrator',
  password = 'admin'
): Promise<void> {
  await page.goto(`${baseURL}/api/method/login`, { waitUntil: 'domcontentloaded' })
  await page.evaluate(
    async ({ user, password }) => {
      const resp = await fetch('/api/method/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `usr=${encodeURIComponent(user)}&pwd=${encodeURIComponent(password)}`,
      })
      if (!resp.ok) throw new Error('Login failed')
    },
    { user, password }
  )
}
