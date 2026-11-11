import type { HomelessFigure, MetricValue } from '@/types/figures'

export interface PitYear {
  year: number
  sheltered: number | null
  unsheltered: number | null
  total: number
  change_from_previous: number | null
  pct_change_from_previous: number | null
  emergency_shelter_beds: number | null
  transitional_beds: number | null
  safe_haven_beds: number | null
  total_year_round_beds: number | null
}

export interface CocHomelessness {
  coc_number: string
  coc_name: string
  label: 'official CoC count'
  latest_year: number
  latest: PitYear
  years: PitYear[]
  sources: string[]
}

export interface StateHomelessness {
  label: 'official CoC count'
  geography: string
  coc_count: number
  years: PitYear[]
}

export interface StatsOverview {
  level: 'state' | 'county' | 'municipality'
  id: string
  name: string
  metrics: Record<string, MetricValue>
  homelessness: {
    official_state: StateHomelessness | null
    official_cocs: CocHomelessness[]
    area_estimate: HomelessFigure
    note: string
  }
  shelter_beds: {
    value: number | null
    year: number | null
    label: 'official CoC count'
    geography: string
    source: string
  }
}
