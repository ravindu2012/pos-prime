// Ensure Frappe's translation function is available globally for Vue templates and script setup
// This must be imported BEFORE any component that uses __()
if (typeof window.__ === 'undefined') {
  window.__ = (msg: string, replace?: Record<string, string> | string[], _context?: string) => {
    if ((window as any).frappe?._) {
      return (window as any).frappe._(msg, replace, _context)
    }
    if (replace && !Array.isArray(replace)) {
      return Object.entries(replace).reduce(
        (s, [k, v]) => s.replace(`{${k}}`, v),
        msg
      )
    }
    return msg
  }
}
