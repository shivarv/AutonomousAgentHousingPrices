import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'
import {
  fetchAreaAt,
  fetchAreaStats,
  fetchAreaSummary,
  fetchGeocode,
  fetchOutlines,
  fetchTracts,
} from '@/features/site-explorer/api/explorerApi'
import type { AreaLevel, LatLon } from '@/features/site-explorer/types'

export function useAreaStats(pin: LatLon | null, radii: number[], enabled: boolean) {
  return useQuery({
    queryKey: ['area-stats', pin, radii],
    queryFn: () => fetchAreaStats(pin!, radii),
    enabled: enabled && pin !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export function useAreaAt(pin: LatLon | null, level: AreaLevel, enabled: boolean) {
  return useQuery({
    queryKey: ['area-at', pin, level],
    queryFn: () => fetchAreaAt(pin!, level),
    enabled: enabled && pin !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export function useOutlines(level: AreaLevel | null) {
  return useQuery({
    queryKey: ['outlines', level],
    queryFn: () => fetchOutlines(level!),
    enabled: level !== null,
    staleTime: Infinity,
  })
}

export function useAreaSummary(level: AreaLevel, ids: string[]) {
  return useQuery({
    queryKey: ['area-summary', level, ids],
    queryFn: () => fetchAreaSummary(level, ids),
    enabled: ids.length > 1,
    placeholderData: keepPreviousData,
  })
}

export function useTracts() {
  return useQuery({ queryKey: ['tracts'], queryFn: fetchTracts, staleTime: Infinity })
}

export function useGeocode() {
  return useMutation({ mutationFn: fetchGeocode })
}
