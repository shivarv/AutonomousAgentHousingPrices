import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchOverview } from '@/features/overview/api/overviewApi'

export function useOverview(county: string, municipality: string) {
  return useQuery({
    queryKey: ['overview', county, municipality],
    queryFn: () => fetchOverview(county, municipality),
    placeholderData: keepPreviousData,
  })
}
