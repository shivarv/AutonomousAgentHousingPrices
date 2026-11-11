import { httpClient } from '@/services/httpClient'
import type { DataSource, ModelMetrics } from '@/features/methodology/types'

export const fetchSources = () => httpClient.get<DataSource[]>('/api/sources')
export const fetchModelMetrics = () => httpClient.get<ModelMetrics>('/api/model/metrics')
