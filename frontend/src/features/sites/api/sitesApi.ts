import { httpClient } from '@/services/httpClient'
import type { SiteDetail, SiteFilter, SiteList } from '@/features/sites/types'

function query(filter: SiteFilter, extra: Record<string, string | number>): string {
  const params = new URLSearchParams()
  if (filter.county) params.set('county', filter.county)
  if (filter.municipality) params.set('municipality', filter.municipality)
  for (const [k, v] of Object.entries(extra)) params.set(k, String(v))
  return params.toString()
}

export const fetchSites = (filter: SiteFilter, limit: number, offset = 0) =>
  httpClient.get<SiteList>(`/api/sites?${query(filter, { limit, offset })}`)

export const fetchBestSite = (filter: SiteFilter, offset: number) =>
  httpClient.get<SiteDetail>(`/api/sites/best?${query(filter, { offset })}`)

export const fetchSite = (id: number) => httpClient.get<SiteDetail>(`/api/sites/${id}`)
