import { httpClient } from '@/services/httpClient'
import type { AreaStatsTable, TableLevel } from '@/features/areas/types'

export const fetchAreaTable = (level: TableLevel) =>
  httpClient.get<AreaStatsTable>(`/api/stats/areas?level=${level}`)
