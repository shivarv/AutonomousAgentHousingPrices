import type { MetricValue } from '@/types/figures'

export type TableLevel = 'county' | 'municipality'

/** Mirrors AreaStatsRow; homeless_estimate is a modelled estimate. */
export interface AreaStatsRow {
  id: string
  name: string
  county_geoid: string | null
  population: number | null
  need_index: number | null
  eli_renter_households: number | null
  affordable_gap_eli: number | null
  affordable_units_per_100_eli: number | null
  homeless_estimate: number | null
}

export interface AreaStatsTable {
  level: TableLevel
  rows: AreaStatsRow[]
  metrics: Record<string, MetricValue>
  homeless_label: 'estimate'
}
