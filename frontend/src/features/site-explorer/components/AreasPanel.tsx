import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { SelectField } from '@/components/ui/SelectField'
import { FiguresList } from '@/features/site-explorer/components/FiguresList'
import type { ExplorerState } from '@/features/site-explorer/hooks/useExplorerState'
import { useAreaAt, useAreaSummary } from '@/features/site-explorer/hooks/useExplorerData'
import type { AreaLevel, LatLon } from '@/features/site-explorer/types'

const LEVEL_OPTIONS: { value: AreaLevel; label: string }[] = [
  { value: 'tract', label: 'Census tract' },
  { value: 'neighbourhood', label: 'Boston neighbourhood' },
  { value: 'municipality', label: 'City or town' },
  { value: 'county', label: 'County' },
  { value: 'coc', label: 'Homelessness region (CoC)' },
]

export function AreasPanel({ s, pin }: { s: ExplorerState; pin: LatLon | null }) {
  const at = useAreaAt(pin, s.level, s.mode === 'areas')
  const ids = at.data ? [at.data.id, ...s.benefit] : []
  const summary = useAreaSummary(s.level, ids)
  return (
    <div className="space-y-4">
      <SelectField
        label="Boundary level"
        value={s.level}
        options={LEVEL_OPTIONS}
        onChange={(v) => s.setLevel(v as AreaLevel)}
      />
      {at.isPending && s.pin && <LoadingState label="Finding the area under the pin" />}
      {at.isError && <ErrorState title="No area here" error={at.error} />}
      {at.data && (
        <section aria-live="polite">
          <h2 className="text-lg font-bold">{at.data.name}</h2>
          <p className="mb-2 text-xs text-ink-soft">{at.data.note}</p>
          <FiguresList f={at.data.figures} />
          <p className="mt-2 text-xs text-ink-soft">
            Click neighbouring areas on the map to add them to a benefit area.
          </p>
        </section>
      )}
      {at.data && s.benefit.length > 0 && (
        <section className="rounded-sm border border-marker bg-marker-soft/40 p-3" aria-live="polite">
          <div className="flex items-center justify-between">
            <h2 className="font-bold">Benefit area: {ids.length} areas</h2>
            <button
              type="button"
              onClick={s.clearBenefit}
              className="rounded-sm border border-rule bg-paper-raised px-2 py-0.5 text-sm"
            >
              Clear
            </button>
          </div>
          <p className="mb-2 text-xs text-ink-soft">
            {(summary.data?.areas ?? []).map((a) => a.name).join(', ')}
          </p>
          {summary.isPending && <LoadingState label="Adding up" />}
          {summary.isError && <ErrorState error={summary.error} />}
          {summary.data && <FiguresList f={summary.data.figures} />}
        </section>
      )}
    </div>
  )
}
