import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchBestSite, fetchSite, fetchSites } from '@/features/sites/api/sitesApi'
import type { SiteFilter } from '@/features/sites/types'

export function useSites(filter: SiteFilter, limit: number, offset = 0) {
  return useQuery({
    queryKey: ['sites', filter, limit, offset],
    queryFn: () => fetchSites(filter, limit, offset),
    placeholderData: keepPreviousData,
  })
}

/** offset 0 = best site for the filter, 1 = next best, ... (null = not requested yet) */
export function useBestSite(filter: SiteFilter, offset: number | null) {
  return useQuery({
    queryKey: ['best-site', filter, offset],
    queryFn: () => fetchBestSite(filter, offset ?? 0),
    enabled: offset !== null,
  })
}

export function useSite(id: number | null) {
  return useQuery({
    queryKey: ['site', id],
    queryFn: () => fetchSite(id ?? 0),
    enabled: id !== null,
  })
}
