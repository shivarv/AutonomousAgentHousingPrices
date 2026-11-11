import type { CocHomelessness } from '@/features/overview/types'
import { formatCount } from '@/utils/format'

export function CocTable({ cocs }: { cocs: CocHomelessness[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[32rem] text-sm">
        <caption className="sr-only">Official homelessness counts by Continuum of Care</caption>
        <thead className="border-b border-rule text-left text-ink-soft">
          <tr>
            <th scope="col" className="py-2 font-medium">Continuum of Care</th>
            <th scope="col" className="py-2 text-right font-medium">Count</th>
            <th scope="col" className="py-2 text-right font-medium">Change on year</th>
            <th scope="col" className="py-2 text-right font-medium">Year-round beds</th>
          </tr>
        </thead>
        <tbody>
          {[...cocs]
            .sort((a, b) => b.latest.total - a.latest.total)
            .map((c) => (
              <tr key={c.coc_number} className="border-b border-rule/60">
                <th scope="row" className="py-1.5 text-left font-normal">
                  {c.coc_name} <span className="text-ink-soft">({c.coc_number})</span>
                </th>
                <td className="py-1.5 text-right tabular-nums">{formatCount(c.latest.total)}</td>
                <td className="py-1.5 text-right tabular-nums">
                  {c.latest.pct_change_from_previous === null
                    ? 'n/a'
                    : `${c.latest.pct_change_from_previous > 0 ? '+' : ''}${c.latest.pct_change_from_previous}%`}
                </td>
                <td className="py-1.5 text-right tabular-nums">
                  {formatCount(c.latest.total_year_round_beds)}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-ink-soft">
        HUD Point-in-Time count and Housing Inventory Count, {cocs[0]?.latest_year}. Official
        counts exist only per Continuum of Care.
      </p>
    </div>
  )
}
