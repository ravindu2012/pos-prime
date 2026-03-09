/**
 * Build a Frappe desk URL that works across v14/v15 (/app/) and v16+ (/desk/).
 * Detects the correct prefix from the current page or frappe router.
 *
 * Usage: deskUrl('customer/CUST-001') → '/app/customer/CUST-001' or '/desk/customer/CUST-001'
 */
export function deskUrl(path: string): string {
  // Frappe v16+ uses /desk/, v14-v15 use /app/
  const frappe = (window as any).frappe
  if (frappe?.router?.is_app_route) {
    // Use Frappe's own detection: v16 checks for "desk", v14-v15 check for "app"
    const prefix = window.location.pathname.startsWith('/desk') ? '/desk' : '/app'
    return `${prefix}/${path}`
  }
  // Fallback: detect from current URL
  if (window.location.pathname.startsWith('/desk')) {
    return `/desk/${path}`
  }
  return `/app/${path}`
}
