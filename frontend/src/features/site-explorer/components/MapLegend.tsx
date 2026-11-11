import { LAYER_SCALES, LAYER_TITLES, NO_DATA_COLOR } from '@/features/site-explorer/mapStyles'
import type { BackgroundLayer } from '@/features/site-explorer/types'

export function MapLegend({ layer, showRings }: { layer: BackgroundLayer; showRings: boolean }) {
  return (
    <div className="pointer-events-auto max-w-56 rounded-sm bg-paper-raised/95 p-3 text-xs shadow-sm">
      <p className="font-semibold">{LAYER_TITLES[layer]}</p>
      {layer === 'sites' ? (
        <p className="mt-1 flex items-center gap-2">
          <span className="inline-block size-3 rounded-full border border-ink bg-marker" />
          Top 500 sites; larger = higher score
        </p>
      ) : (
        <ul className="mt-1 space-y-0.5">
          {LAYER_SCALES[layer].map((c) => (
            <li key={c.label} className="flex items-center gap-2">
              <span className="inline-block h-3 w-5 border border-rule" style={{ background: c.color }} />
              {c.label}
            </li>
          ))}
          <li className="flex items-center gap-2">
            <span className="inline-block h-3 w-5 border border-rule" style={{ background: NO_DATA_COLOR }} />
            no data
          </li>
        </ul>
      )}
      {showRings && (
        <ul className="mt-2 space-y-0.5 border-t border-rule pt-2">
          <li className="flex items-center gap-2">
            <span className="inline-block size-3 rounded-full bg-estimate" /> homeless estimate per
            tract
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block size-3 border-2 border-ink bg-paper-raised" /> shelter
          </li>
        </ul>
      )}
    </div>
  )
}
