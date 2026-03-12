// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { onUnmounted } from 'vue'

export interface DisplayCartItem {
  item_name: string
  qty: number
  rate: number
  amount: number
  is_free_item?: boolean
  pricing_rules?: string | null
  price_list_rate?: number | null
  discount_percentage?: number
  discount_amount?: number
}

export interface CartUpdatePayload {
  items: DisplayCartItem[]
  subtotal: number
  netTotal: number
  taxAmount: number
  grandTotal: number
  roundedTotal: number
  totalItems: number
  currency: string
  customerName: string | null
  companyName: string | null
  discountValue: number
  discountType: 'percentage' | 'amount'
  pricingRuleDiscount?: { type: 'percentage' | 'amount'; value: number } | null
}

export interface PaymentStartPayload {
  grandTotal: number
  currency: string
  payments: { mode_of_payment: string; amount: number }[]
  customerName: string | null
  totalPaid: number
  changeDue: number
}

export interface PaymentCompletePayload {
  grandTotal: number
  currency: string
}

export interface InitPayload {
  companyName: string
  companyLogo: string | null
  currency: string
}

export interface CustomerMobilePayload {
  mobile: string
}

export interface CustomerResultPayload {
  found: boolean
  customerName: string | null
}

export type DisplayMessage =
  | { type: 'cart_update'; payload: CartUpdatePayload }
  | { type: 'payment_start'; payload: PaymentStartPayload }
  | { type: 'payment_complete'; payload: PaymentCompletePayload }
  | { type: 'idle' }
  | { type: 'init'; payload: InitPayload }
  | { type: 'customer_mobile'; payload: CustomerMobilePayload }
  | { type: 'customer_result'; payload: CustomerResultPayload }

const CHANNEL_PREFIX = 'pos-prime-display'

export function useBroadcastDisplay(channelId?: string) {
  const channelName = channelId ? `${CHANNEL_PREFIX}-${channelId}` : CHANNEL_PREFIX
  let channel: BroadcastChannel | null = null
  const listeners: Array<(event: MessageEvent<DisplayMessage>) => void> = []

  function getChannel(): BroadcastChannel {
    if (!channel) {
      channel = new BroadcastChannel(channelName)
    }
    return channel
  }

  function sendUpdate(message: DisplayMessage) {
    try {
      getChannel().postMessage(message)
    } catch {
      // BroadcastChannel not supported or closed
    }
  }

  function onUpdate(callback: (message: DisplayMessage) => void) {
    const ch = getChannel()
    const handler = (event: MessageEvent<DisplayMessage>) => {
      callback(event.data)
    }
    ch.addEventListener('message', handler)
    listeners.push(handler)
  }

  function close() {
    if (channel) {
      for (const handler of listeners) {
        channel.removeEventListener('message', handler)
      }
      listeners.length = 0
      channel.close()
      channel = null
    }
  }

  onUnmounted(close)

  return { sendUpdate, onUpdate, close }
}
