import { computed } from 'vue'

const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ps']

export function useRTL() {
  const isRTL = computed(() => {
    const lang = (window as any).frappe?.boot?.lang || document.documentElement.lang || 'en'
    return RTL_LANGUAGES.includes(lang.split('-')[0])
  })

  return { isRTL }
}
