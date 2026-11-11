import { httpClient } from '@/services/httpClient'
import type {
  AreaAt,
  AreaLevel,
  AreaOutlines,
  AreaStatsResponse,
  AreaSummary,
  GeocodeResult,
  LatLon,
  TractCollection,
} from '@/features/site-explorer/types'

export const fetchAreaStats = (pin: LatLon, radii: number[]) =>
  httpClient.post<AreaStatsResponse>('/api/area-stats', { ...pin, radii_km: radii })

export const fetchAreaAt = (pin: LatLon, level: AreaLevel) =>
  httpClient.get<AreaAt>(`/api/areas/at?lat=${pin.lat}&lon=${pin.lon}&level=${level}`)

export const fetchOutlines = (level: AreaLevel) =>
  httpClient.get<AreaOutlines>(`/api/areas?level=${level}`)

export const fetchAreaSummary = (level: AreaLevel, ids: string[]) =>
  httpClient.post<AreaSummary>('/api/areas/summary', { level, ids })

export const fetchTracts = () => httpClient.get<TractCollection>('/api/tracts')

export const fetchGeocode = (q: string) =>
  httpClient.get<GeocodeResult>(`/api/geocode?q=${encodeURIComponent(q)}`)
