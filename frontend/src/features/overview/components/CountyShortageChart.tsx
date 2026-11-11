import type { AreaStatsRow } from '@/features/areas'
import { describeGap } from '@/utils/format'

/** Horizontal bars: ELI affordable-home gap per county (single series, signed labels). */
export function CountyShortageChart({ rows }: { rows: AreaStatsRow[] }) {
  const data = rows
    .filter((r) => r.affordable_gap_eli !== null)
    .sort((a, b) => (b.affordable_gap_eli ?? 0) - (a.affordable_gap_eli ?? 0))
  const max = Math.max(...data.map((r) => Math.abs(r.affordable_gap_eli ?? 0)), 1)
  return (
    <figure>
      <figcaption className="text-sm text-ink-soft">
        Homes affordable and available to extremely-low-income renters, minus those renters (HUD
        CHAS 2018-2022). Longer bar = larger shortage.
      </figcaption>
      <ul className="mt-3 space-y-1.5">
        {data.map((r) => {
          const gap = r.affordable_gap_eli ?? 0
          return (
            <li key={r.id} className="grid grid-cols-[8rem_1fr_7rem] items-center gap-2 text-sm">
              <span className="truncate">{r.name.replace(' County', '')}</span>
              <span className="h-3.5 rounded-r-sm bg-paper">
                <span
                  className={`block h-full rounded-r-sm ${gap > 0 ? 'bg-shortage/80' : 'bg-surplus/80'}`}
                  style={{ width: `${(Math.abs(gap) / max) * 100}%` }}
                />
              </span>
              <span className="text-right tabular-nums">{describeGap(gap)}</span>
            </li>
          )
        })}
      </ul>
    </figure>
  )
}
