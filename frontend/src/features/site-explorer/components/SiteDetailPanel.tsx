import type { SiteDetail } from '@/features/sites'
import { formatDecimal } from '@/utils/format'

export function SiteDetailPanel({ site }: { site: SiteDetail }) {
  return (
    <section className="rounded-sm border border-marker bg-marker-soft/40 p-3" aria-live="polite">
      <p className="text-sm text-ink-soft">
        Candidate site #{site.rank_state} statewide, #{site.rank_county} in {site.county}
      </p>
      <h2 className="text-lg font-bold">
        {site.municipality}: score {site.score.toFixed(1)} of 100
      </h2>
      <p className="mt-1 text-sm">{site.summary}</p>
      <p className="mt-1 text-xs text-ink-soft">
        {formatDecimal(site.lot_size_acres)} acres, parcel {site.loc_id}
      </p>
    </section>
  )
}
