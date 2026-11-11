import { httpClient } from '@/services/httpClient'
import type { Health } from '@/features/system/types'

export const fetchHealth = () => httpClient.get<Health>('/api/health')
