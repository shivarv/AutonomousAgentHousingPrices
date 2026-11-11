import { useQuery } from '@tanstack/react-query'
import { httpClient } from '@/services/httpClient'
import type { TractDetail } from '@/features/site-explorer/types'

export function useTractDetail(geoid: string | null) {
  return useQuery({
    queryKey: ['tract', geoid],
    queryFn: () => httpClient.get<TractDetail>(`/api/tracts/${geoid}`),
    enabled: geoid !== null,
  })
}
