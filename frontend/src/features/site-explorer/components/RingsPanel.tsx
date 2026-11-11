import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { FiguresList } from '@/features/site-explorer/components/FiguresList'
import { RingSliders } from '@/features/site-explorer/components/RingSliders'
import type { ExplorerState } from '@/features/site-explorer/hooks/useExplorerState'
import type { AreaStatsResponse } from '@/features/site-explorer/types'

interface RingsPanelProps {
  s: ExplorerState
  stats: { data?: AreaStatsResponse; isPending: boolean; isError: boolean; error: unknown }
}

export function RingsPanel({ s, stats }: RingsPanelProps) {
  return (
    <div className="space-y-4">
      <RingSliders s={s} />
      {stats.isPending && s.pin && <LoadingState label="Adding up the rings" />}
      {stats.isError && <ErrorState title="No statistics here" error={stats.error} />}
      {stats.data &&
        stats.data.rings.map((r) => (
          <section key={r.radius_km} aria-live="polite">
            <h2 className="font-bold">Within {r.radius_km} km</h2>
            <FiguresList f={r} />
          </section>
        ))}
      {stats.data && (
        <ul className="space-y-1 text-xs text-ink-soft">
          {stats.data.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
