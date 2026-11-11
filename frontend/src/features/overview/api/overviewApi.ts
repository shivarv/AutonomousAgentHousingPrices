import { httpClient } from '@/services/httpClient'
import type { StatsOverview } from '@/features/overview/types'

export function fetchOverview(county: string, municipality: string) {
  if (municipality)
    return httpClient.get<StatsOverview>(
      `/api/stats/overview?level=municipality&id=${municipality}`,
    )
  if (county) return httpClient.get<StatsOverview>(`/api/stats/overview?level=county&id=${county}`)
  return httpClient.get<StatsOverview>('/api/stats/overview?level=state')
}
