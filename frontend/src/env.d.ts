/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

/** Frappe translation function — available globally via window.__ */
declare function __(msg: string, replace?: Record<string, string> | string[], context?: string): string

interface Window {
  posPageSetProfile?: (profileName: string) => void
  posPageClearProfile?: () => void
}

declare module 'frappe-ui' {
  export const FrappeUI: any
  export const setConfig: any
  export const frappeRequest: any
  export const resourcesPlugin: any
  export function createResource(options: any): any
  export function createListResource(options: any): any
  export function call(method: string, args?: any): Promise<any>
  export const Badge: any
  export const Button: any
  export const Dialog: any
  export const Input: any
  export const Autocomplete: any
  export const Spinner: any
  export const Avatar: any
  export const FeatherIcon: any
  export const TextInput: any
  export const FormControl: any
  export const ErrorMessage: any
  export const Tooltip: any
  export const Dropdown: any
}
