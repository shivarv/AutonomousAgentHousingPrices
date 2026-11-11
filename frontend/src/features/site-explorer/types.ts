import type { GapStatus, GeoJsonGeometry, HomelessFigure } from '@/types/figures'

export type ExplorerMode = 'areas' | 'rings'
export type AreaLevel = 'tract' | 'neighbourhood' | 'municipality' | 'county' | 'coc'
export type BackgroundLayer = 'need_index' | 'affordable_gap_eli' | 'homeless_estimate' | 'sites'

export interface LatLon {
  lat: number
  lon: number
}

export interface AreaFigures {
  population: number | null
  homeless: HomelessFigure
  at_risk_households: number | null
  eli_renter_households: number | null
  affordable_units_available: number | null
  affordable_gap: number | null
  gap_status: GapStatus | null
  subsidised_units: number | null
  need_index: number | null
  shelters: number
  shelter_beds: number | null
  tract_count: number
}

export interface RingStats extends AreaFigures {
  radius_km: number
}

export interface NearbyTract {
  geoid: string
  lat: number
  lon: number
  homeless: HomelessFigure
}

export interface NearbyShelter {
  name: string
  shelter_type: string
  beds: number | null
  lat: number
  lon: number
}

export interface AreaStatsResponse {
  lat: number
  lon: number
  rings: RingStats[]
  nearby_tracts: NearbyTract[]
  nearby_shelters: NearbyShelter[]
  sources: Record<string, { year: number | null; source: string | null }>
  notes: string[]
}

export interface AreaRef {
  id: string
  name: string
}

export interface AreaAt {
  level: AreaLevel
  id: string
  name: string
  boundary: GeoJsonGeometry
  neighbours: AreaRef[]
  figures: AreaFigures
  homeless_estimate_sum: HomelessFigure
  homeless_basis: 'official CoC count' | 'sum of tract estimates'
  note: string
}

export interface AreaSummary {
  level: AreaLevel
  areas: AreaRef[]
  figures: AreaFigures
  homeless_estimate_sum: HomelessFigure
  homeless_basis: 'official CoC count' | 'sum of tract estimates'
  note: string
}

export interface OutlineFeature {
  type: 'Feature'
  id: string
  geometry: GeoJsonGeometry
  properties: { name: string; level: AreaLevel }
}

export interface AreaOutlines {
  type: 'FeatureCollection'
  level: AreaLevel
  features: OutlineFeature[]
}

export interface TractFeature {
  type: 'Feature'
  id: string
  geometry: GeoJsonGeometry
  properties: Record<string, string | number | null>
}

export interface TractCollection {
  type: 'FeatureCollection'
  features: TractFeature[]
  metrics: Record<string, { year: number | null; source: string | null; label: string | null }>
}

export interface GeocodeResult {
  query: string
  matches: { address: string; lat: number; lon: number }[]
  source: string
}
