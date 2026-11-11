import type { BackgroundLayer } from '@/features/site-explorer/types'

export interface LegendClass {
  min: number
  color: string
  label: string
}

/** Colour-blind-safe classed scales (ColorBrewer Blues, BrBG, Purples). */
export const LAYER_SCALES: Record<Exclude<BackgroundLayer, 'sites'>, LegendClass[]> = {
  need_index: [
    { min: -Infinity, color: '#eff3ff', label: 'under 40' },
    { min: 40, color: '#c6dbef', label: '40-45' },
    { min: 45, color: '#9ecae1', label: '45-50' },
    { min: 50, color: '#6baed6', label: '50-55' },
    { min: 55, color: '#3182bd', label: '55-60' },
    { min: 60, color: '#08519c', label: '60 and over' },
  ],
  affordable_gap_eli: [
    { min: -Infinity, color: '#018571', label: 'surplus of 50+' },
    { min: -50, color: '#80cdc1', label: 'surplus 10-50' },
    { min: -10, color: '#f5f5f5', label: 'within 10' },
    { min: 10, color: '#dfc27d', label: 'shortage 10-50' },
    { min: 50, color: '#bf812d', label: 'shortage 50-150' },
    { min: 150, color: '#8c510a', label: 'shortage 150+' },
  ],
  homeless_estimate: [
    { min: -Infinity, color: '#f2f0f7', label: 'under 2' },
    { min: 2, color: '#dadaeb', label: '2-5' },
    { min: 5, color: '#bcbddc', label: '5-10' },
    { min: 10, color: '#9e9ac8', label: '10-20' },
    { min: 20, color: '#756bb1', label: '20-40' },
    { min: 40, color: '#54278f', label: '40 and over' },
  ],
}

export const LAYER_TITLES: Record<BackgroundLayer, string> = {
  need_index: 'Housing Need Index (0-100)',
  affordable_gap_eli: 'Affordable homes for extremely-low-income renters',
  homeless_estimate: 'People experiencing homelessness (estimate)',
  sites: 'Candidate construction sites',
}

export const NO_DATA_COLOR = '#d9d9d9'

export function colorFor(layer: Exclude<BackgroundLayer, 'sites'>, v: number | null): string {
  if (v === null || v === undefined) return NO_DATA_COLOR
  const classes = LAYER_SCALES[layer]
  let color = classes[0].color
  for (const c of classes) if (v >= c.min) color = c.color
  return color
}

export const RING_COLORS = ['#14324a', '#14324a', '#14324a']
export const RING_DASH = [undefined, '6 4', '2 6']
