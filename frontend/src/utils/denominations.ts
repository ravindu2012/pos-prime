// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

export const CURRENCY_DENOMINATIONS: Record<string, number[]> = {
  LKR: [5000, 1000, 500, 100, 50, 20, 10, 5, 2, 1],
  USD: [100, 50, 20, 10, 5, 2, 1, 0.50, 0.25, 0.10, 0.05, 0.01],
  INR: [2000, 500, 200, 100, 50, 20, 10, 5, 2, 1],
  EUR: [500, 200, 100, 50, 20, 10, 5, 2, 1, 0.50, 0.20, 0.10, 0.05, 0.02, 0.01],
  GBP: [50, 20, 10, 5, 2, 1, 0.50, 0.20, 0.10, 0.05, 0.02, 0.01],
  AUD: [100, 50, 20, 10, 5, 2, 1, 0.50, 0.20, 0.10, 0.05],
  CAD: [100, 50, 20, 10, 5, 2, 1, 0.25, 0.10, 0.05],
  JPY: [10000, 5000, 2000, 1000, 500, 100, 50, 10, 5, 1],
  CNY: [100, 50, 20, 10, 5, 1, 0.50, 0.10, 0.05, 0.01],
  SGD: [1000, 100, 50, 10, 5, 2, 1, 0.50, 0.20, 0.10, 0.05],
  MYR: [100, 50, 20, 10, 5, 1, 0.50, 0.20, 0.10, 0.05],
  THB: [1000, 500, 100, 50, 20, 10, 5, 2, 1, 0.50, 0.25],
  PKR: [5000, 1000, 500, 100, 50, 20, 10, 5, 2, 1],
  BDT: [1000, 500, 200, 100, 50, 20, 10, 5, 2, 1],
  ZAR: [200, 100, 50, 20, 10, 5, 2, 1, 0.50, 0.20, 0.10],
  AED: [1000, 500, 200, 100, 50, 20, 10, 5, 1, 0.50, 0.25],
  SAR: [500, 200, 100, 50, 20, 10, 5, 2, 1, 0.50, 0.25, 0.10, 0.05],
  KES: [1000, 500, 200, 100, 50, 40, 20, 10, 5, 1],
  NGN: [1000, 500, 200, 100, 50, 20, 10, 5, 2, 1],
  PHP: [1000, 500, 200, 100, 50, 20, 10, 5, 1, 0.25],
  BRL: [200, 100, 50, 20, 10, 5, 2, 1, 0.50, 0.25, 0.10, 0.05],
}

// Smallest note denomination per currency (values below this are coins)
const SMALLEST_NOTE: Record<string, number> = {
  LKR: 20,
  USD: 1,
  INR: 10,
  EUR: 5,
  GBP: 5,
  AUD: 5,
  CAD: 5,
  JPY: 1000,
  CNY: 1,
  SGD: 2,
  MYR: 1,
  THB: 20,
  PKR: 10,
  BDT: 2,
  ZAR: 10,
  AED: 5,
  SAR: 5,
  KES: 50,
  NGN: 5,
  PHP: 20,
  BRL: 2,
}

export function getDenominations(currency: string): number[] {
  return CURRENCY_DENOMINATIONS[currency] || generateFallback()
}

export function getSmallestNote(currency: string): number {
  return SMALLEST_NOTE[currency] ?? 1
}

function generateFallback(): number[] {
  return [1000, 500, 200, 100, 50, 20, 10, 5, 2, 1, 0.50, 0.25, 0.10, 0.05, 0.01]
}
