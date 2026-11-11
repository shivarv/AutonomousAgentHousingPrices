import { Link } from 'react-router'
import { FigureLabel } from '@/components/ui/FigureLabel'
import type { SiteSummary } from '@/features/sites/types'
import { describeGap, formatDecimal, formatKm } from '@/utils/format'

export function SiteRow({ site }: { site: SiteSummary }) {
  return (
    <li className="grid grid-cols-[3rem_1fr_auto] items-start gap-3 border-b border-rule py-3">
      <span className="text-right text-lg font-bold tabular-nums text-ink-soft">
        {site.rank_state}
      </span>
      <div className="min-w-0">
        <Link
          to={`/?site=${site.id}`}
          className="font-semibold text-ink underline-offset-2 hover:underline"
        >
          {site.municipality}, {site.county}
        </Link>
        <p className="text-sm text-ink-soft">
          {formatDecimal(site.lot_size_acres)} acres of {site.use_description},{' '}
          {formatKm(site.nearest_stop_km)} to transit
          {site.in_mbta3a_district && ', in an MBTA 3A district'}
        </p>
        <p className="mt-1 text-sm">
          Within 5 km: need {formatDecimal(site.need_index_5km)},{' '}
          <span className={gapClass(site.affordable_gap_eli_5km)}>
            {describeGap(site.affordable_gap_eli_5km)}
          </span>{' '}
          affordable homes, {formatDecimal(site.homeless_5km.value)} homeless{' '}
          <FigureLabel label={site.homeless_5km.label} />
        </p>
      </div>
      <span className="rounded-sm bg-marker-soft px-2 py-1 text-sm font-bold tabular-nums">
        {site.score.toFixed(1)}
      </span>
    </li>
  )
}

function gapClass(gap: number | null): string {
  if (gap === null) return ''
  return gap > 0 ? 'font-medium text-shortage' : 'font-medium text-surplus'
}
