/** Mirrors app.schemas.estimate.HomelessFigure: a homeless number always carries its label. */
export interface HomelessFigure {
  value: number | null
  label: 'estimate' | 'official CoC count'
  year: number | null
  method: string | null
  method_url: string
}

/** Mirrors app.schemas.metric.MetricValue: a number with its year and source. */
export interface MetricValue {
  value: number | null
  year: number | null
  source: string | null
  is_estimate: boolean
  label: string | null
  method: string | null
}

export type GapStatus = 'shortage' | 'surplus' | 'balanced'

export interface GeoJsonGeometry {
  type: 'Polygon' | 'MultiPolygon'
  coordinates: number[][][] | number[][][][]
}
