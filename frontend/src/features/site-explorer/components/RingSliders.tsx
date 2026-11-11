import { RING_PRESETS } from '@/features/site-explorer/hooks/useExplorerState'
import type { ExplorerState } from '@/features/site-explorer/hooks/useExplorerState'

export function RingSliders({ s }: { s: ExplorerState }) {
  return (
    <fieldset>
      <legend className="text-sm font-medium text-ink-soft">Ring distances</legend>
      <div className="mt-1 flex gap-2">
        {(Object.keys(RING_PRESETS) as (keyof typeof RING_PRESETS)[]).map((k) => (
          <button
            key={k}
            type="button"
            aria-pressed={s.preset === k}
            onClick={() => s.choosePreset(k)}
            className={`rounded-sm border px-2.5 py-1 text-sm ${s.preset === k ? 'border-ink bg-ink text-paper-raised' : 'border-rule bg-paper-raised'}`}
          >
            {RING_PRESETS[k].label} {RING_PRESETS[k].radii.join(' / ')} km
          </button>
        ))}
      </div>
      <div className="mt-2 space-y-1">
        {s.radii.map((r, i) => (
          <label key={i} className="grid grid-cols-[4.5rem_1fr_3.5rem] items-center gap-2 text-sm">
            <span>Ring {i + 1}</span>
            <input
              type="range"
              min={0.5}
              max={80}
              step={0.5}
              value={r}
              onChange={(e) => s.setRadius(i, Number(e.target.value))}
              className="accent-ink"
            />
            <span className="text-right tabular-nums">{r} km</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
