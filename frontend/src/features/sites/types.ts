import type { GeoJsonGeometry, HomelessFigure } from '@/types/figures'

export interface SiteSummary {
  id: number
  rank_state: number
  rank_county: number
  score: number
  loc_id: string
  municipality_geoid: string
  municipality: string
  county_geoid: string
  county: string
  lat: number
  lon: number
  lot_size_acres: number
  use_code: string
  use_description: string | null
  in_mbta3a_district: boolean
  need_index_5km: number | null
  affordable_gap_eli_5km: number | null
  homeless_5km: HomelessFigure
  nearest_stop_km: number | null
  est_land_cost: number | null
  flags: string[]
  summary: string
}

export interface SiteList {
  total: number
  offset: number
  sites: SiteSummary[]
}

export interface SiteRing {
  radius_km: number
  need_index: number | null
  affordable_gap_eli: number | null
  homeless: HomelessFigure
  population: number | null
  shelters: number | null
}

export interface SiteDetail extends SiteSummary {
  boundary: GeoJsonGeometry
  rings: SiteRing[]
  components: Record<string, number | null>
  weights: Record<string, number>
  component_descriptions: Record<string, string>
  features: Record<string, unknown>
  overlaps: Record<string, number>
  land_value: number | null
  fiscal_year: number | null
  sources: string[]
  provenance: Record<string, { year: number | null; source: string; note: string | null }>
}

export interface SiteFilter {
  county: string
  municipality: string
}
