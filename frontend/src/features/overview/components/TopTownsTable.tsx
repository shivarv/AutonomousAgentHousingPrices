import type { AreaStatsRow } from '@/features/areas'
import { describeGap, formatCount, formatDecimal } from '@/utils/format'

export function TopTownsTable({ rows, limit = 15 }: { rows: AreaStatsRow[]; limit?: number }) {
  const top = rows
    .filter((r) => r.need_index !== null)
    .sort((a, b) => (b.need_index ?? 0) - (a.need_index ?? 0))
    .slice(0, limit)
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[32rem] text-sm">
        <caption className="sr-only">Cities and towns with the highest Housing Need Index</caption>
        <thead className="border-b border-rule text-left text-ink-soft">
          <tr>
            <th scope="col" className="py-2 font-medium">City or town</th>
            <th scope="col" className="py-2 text-right font-medium">Need Index</th>
            <th scope="col" className="py-2 text-right font-medium">Population</th>
            <th scope="col" className="py-2 text-right font-medium">Affordable homes</th>
            <th scope="col" className="py-2 text-right font-medium">Homeless (estimate)</th>
          </tr>
        </thead>
        <tbody>
          {top.map((r) => (
            <tr key={r.id} className="border-b border-rule/60">
              <th scope="row" className="py-1.5 text-left font-normal">{r.name}</th>
              <td className="py-1.5 text-right font-semibold tabular-nums">
                {formatDecimal(r.need_index)}
              </td>
              <td className="py-1.5 text-right tabular-nums">{formatCount(r.population)}</td>
              <td className="py-1.5 text-right tabular-nums">{describeGap(r.affordable_gap_eli)}</td>
              <td className="py-1.5 text-right tabular-nums">
                {formatDecimal(r.homeless_estimate)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-ink-soft">
        Small towns rank high partly through distance to services, and towns sharing one census
        tract share its index; see Methodology.
      </p>
    </div>
  )
}
