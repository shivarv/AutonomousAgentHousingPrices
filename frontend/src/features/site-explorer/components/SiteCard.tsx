import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { SiteDetailPanel } from '@/features/site-explorer/components/SiteDetailPanel'
import { useSite } from '@/features/sites'

export function SiteCard({ siteId }: { siteId: number }) {
  const { data, isPending, isError, error } = useSite(siteId)
  if (isPending) return <LoadingState label="Loading the site" />
  if (isError) return <ErrorState error={error} />
  return <SiteDetailPanel site={data} />
}
