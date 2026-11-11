import { ErrorState } from '@/components/ui/ErrorState'
import { FigureLabel } from '@/components/ui/FigureLabel'
import { LoadingState } from '@/components/ui/LoadingState'
import { METRIC_LABELS, formatMetric } from '@/config/metricLabels'
import type { MetricLabel } from '@/config/metricLabels'
import { useTractDetail } from '@/features/site-explorer/hooks/useTractDetail'

const GROUPS: MetricLabel['group'][] = [
  'Homelessness',
  'Affordable housing',
  'People and homes',
  'Need Index',
  'Market and context',
]

/** Every published figure for one tract, each with its source and year. */
export function TractDetailPanel({ geoid }: { geoid: string }) {
  const { data, isPending, isError, error } = useTractDetail(geoid)
  if (isPending) return <LoadingState label="Loading tract figures" />
  if (isError) return <ErrorState error={error} />
  const towns = data.municipalities.map((m) => m.name).join(', ')
  return (
    <div className="space-y-3 text-sm">
      <p className="text-ink-soft">
        {data.name} ({data.geoid}), {towns}, {data.county_name}. CoC {data.coc_number}
        {data.neighbourhood_name ? `, ${data.neighbourhood_name}` : ''}. {data.land_area_km2} km² of
        land.
      </p>
      {GROUPS.map((g) => {
        const rows = Object.entries(METRIC_LABELS).filter(
          ([k, l]) => l.group === g && data.metrics[k],
        )
        if (!rows.length) return null
        return (
          <section key={g}>
            <h3 className="font-semibold">
              {g} {g === 'Homelessness' && <FigureLabel label="estimate" />}
            </h3>
            <dl>
              {rows.map(([k, l]) => {
                const m = data.metrics[k]
                return (
                  <div key={k} className="grid grid-cols-[1fr_auto] gap-x-3 border-b border-rule/60 py-1">
                    <dt>{l.label}</dt>
                    <dd className="text-right font-semibold tabular-nums">
                      {formatMetric(l.kind, m.value)}
                    </dd>
                    <dd className="col-span-2 text-xs text-ink-soft">
                      {m.source}, {m.year}
                      {m.is_estimate && ', modelled estimate'}
                      {data.flags[k] && `. Note: ${data.flags[k]}`}
                    </dd>
                  </div>
                )
              })}
            </dl>
          </section>
        )
      })}
    </div>
  )
}
