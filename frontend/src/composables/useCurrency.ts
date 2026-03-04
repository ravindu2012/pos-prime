import { useSettingsStore } from '@/stores/settings'

const formatterCache = new Map<string, Intl.NumberFormat>()
const numberFormatter = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

function getFormatter(currency: string): Intl.NumberFormat {
  let formatter = formatterCache.get(currency)
  if (!formatter) {
    try {
      formatter = new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    } catch {
      formatter = numberFormatter
    }
    formatterCache.set(currency, formatter)
  }
  return formatter
}

export function useCurrency() {
  const settings = useSettingsStore()

  function formatCurrency(value: number): string {
    const currency = settings.currency || 'USD'
    return getFormatter(currency).format(value)
  }

  function formatNumber(value: number): string {
    return numberFormatter.format(value)
  }

  return { formatCurrency, formatNumber }
}
