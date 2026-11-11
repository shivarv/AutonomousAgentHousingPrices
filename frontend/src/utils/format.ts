const whole = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const oneDecimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })
const compactMoney = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  notation: 'compact',
  maximumFractionDigits: 1,
})

export const NO_DATA = 'no data'

export function formatCount(v: number | null | undefined): string {
  return v === null || v === undefined ? NO_DATA : whole.format(v)
}

export function formatDecimal(v: number | null | undefined): string {
  return v === null || v === undefined ? NO_DATA : oneDecimal.format(v)
}

/** 0-1 share as a percentage. */
export function formatShare(v: number | null | undefined): string {
  return v === null || v === undefined ? NO_DATA : `${oneDecimal.format(v * 100)}%`
}

export function formatMoney(v: number | null | undefined): string {
  return v === null || v === undefined ? NO_DATA : compactMoney.format(v)
}

export function formatKm(v: number | null | undefined): string {
  return v === null || v === undefined ? NO_DATA : `${oneDecimal.format(v)} km`
}

/** Affordable gap as words: positive = shortage, negative = surplus. */
export function describeGap(gap: number | null | undefined): string {
  if (gap === null || gap === undefined) return NO_DATA
  if (Math.abs(gap) < 0.5) return 'balanced'
  return gap > 0 ? `${whole.format(gap)} short` : `${whole.format(-gap)} surplus`
}
