import { useState } from 'react'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { SiteRow } from '@/features/sites/components/SiteRow'
import { useSites } from '@/features/sites/hooks/useSites'
import type { SiteFilter } from '@/features/sites/types'

const PAGE = 25

export function SiteRankingList({ filter }: { filter: SiteFilter }) {
  const [page, setPage] = useState(0)
  const [lastFilter, setLastFilter] = useState(filter)
  if (lastFilter !== filter) {
    setLastFilter(filter)
    setPage(0)
  }
  const { data, isPending, isError, error, refetch, isFetching } = useSites(
    filter,
    PAGE,
    page * PAGE,
  )
  if (isPending) return <LoadingState label="Loading candidate sites" />
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />
  if (data.sites.length === 0)
    return (
      <EmptyState title="No candidate sites here">
        No parcel in this area passed the screening (developable vacant land of at least half an
        acre, mostly outside open space, wetlands and flood zones).
      </EmptyState>
    )
  const pages = Math.ceil(data.total / PAGE)
  return (
    <div aria-busy={isFetching}>
      <p className="text-sm text-ink-soft">
        {data.total.toLocaleString('en-US')} screened sites, ranked by site score (0-100). Rank is
        statewide.
      </p>
      <ol className="mt-2">
        {data.sites.map((s) => (
          <SiteRow key={s.id} site={s} />
        ))}
      </ol>
      <nav className="mt-3 flex items-center gap-3 text-sm" aria-label="Site list pages">
        <button
          type="button"
          disabled={page === 0}
          onClick={() => setPage((p) => p - 1)}
          className="rounded-sm border border-rule px-3 py-1 disabled:opacity-40"
        >
          Previous
        </button>
        <span>
          Page {page + 1} of {pages}
        </span>
        <button
          type="button"
          disabled={page + 1 >= pages}
          onClick={() => setPage((p) => p + 1)}
          className="rounded-sm border border-rule px-3 py-1 disabled:opacity-40"
        >
          Next
        </button>
      </nav>
    </div>
  )
}
