import { useQuery } from '@tanstack/react-query'
import { fetchModelMetrics, fetchSources } from '@/features/methodology/api/methodologyApi'

export const useSources = () =>
  useQuery({ queryKey: ['sources'], queryFn: fetchSources, staleTime: Infinity })

export const useModelMetrics = () =>
  useQuery({ queryKey: ['model-metrics'], queryFn: fetchModelMetrics, staleTime: Infinity })
