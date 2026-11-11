import { useQuery } from '@tanstack/react-query'
import { fetchAreaTable } from '@/features/areas/api/areasApi'
import type { TableLevel } from '@/features/areas/types'

export function useAreaTable(level: TableLevel) {
  return useQuery({
    queryKey: ['area-table', level],
    queryFn: () => fetchAreaTable(level),
    staleTime: Infinity,
  })
}
