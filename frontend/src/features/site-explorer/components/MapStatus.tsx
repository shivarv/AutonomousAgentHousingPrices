import { useOutlines, useTracts } from '@/features/site-explorer/hooks/useExplorerData'
import type { AreaLevel, BackgroundLayer, ExplorerMode } from '@/features/site-explorer/types'

interface MapStatusProps {
  layer: BackgroundLayer
  mode: ExplorerMode
  level: AreaLevel
}

/** Loading and error messages for the map layers (the map itself has no text). */
export function MapStatus({ layer, mode, level }: MapStatusProps) {
  const tracts = useTracts()
  const outlines = useOutlines(mode === 'areas' ? level : null)
  const messages: string[] = []
  if (layer !== 'sites' && tracts.isPending) messages.push('Loading the tract layer…')
  if (layer !== 'sites' && tracts.isError) messages.push(`Tract layer failed: ${tracts.error.message}`)
  if (mode === 'areas' && outlines.isPending) messages.push('Loading area outlines…')
  if (mode === 'areas' && outlines.isError)
    messages.push(`Area outlines failed: ${outlines.error.message}`)
  if (!messages.length) return null
  const failed = tracts.isError || outlines.isError
  return (
    <div
      role={failed ? 'alert' : 'status'}
      className={`pointer-events-none absolute top-2 left-14 z-[500] rounded-sm px-3 py-1.5 text-sm shadow-sm ${failed ? 'bg-shortage text-paper-raised' : 'bg-paper-raised/95 text-ink'}`}
    >
      {messages.map((m) => (
        <p key={m}>{m}</p>
      ))}
    </div>
  )
}
