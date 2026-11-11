import type { KeyboardEvent } from 'react'
import type { LatLon } from '@/features/site-explorer/types'

const STEP = 0.005 // degrees, about 0.5 km

/** Keyboard access to the pin: focus this control and use the arrow keys. */
export function PinNudger({ pin, onMove }: { pin: LatLon | null; onMove: (p: LatLon) => void }) {
  const onKey = (e: KeyboardEvent) => {
    if (!pin) return
    const step = e.shiftKey ? STEP * 5 : STEP
    const moves: Record<string, [number, number]> = {
      ArrowUp: [step, 0],
      ArrowDown: [-step, 0],
      ArrowLeft: [0, -step],
      ArrowRight: [0, step],
    }
    const m = moves[e.key]
    if (!m) return
    e.preventDefault()
    onMove({ lat: pin.lat + m[0], lon: pin.lon + m[1] })
  }
  return (
    <div
      tabIndex={0}
      role="application"
      aria-label="Pin position. Use the arrow keys to move the pin; hold Shift for larger steps."
      onKeyDown={onKey}
      className="rounded-sm border border-dashed border-rule px-2 py-1.5 text-xs text-ink-soft"
    >
      {pin
        ? `Pin at ${pin.lat.toFixed(4)}, ${pin.lon.toFixed(4)}. Focus here and use arrow keys to move it.`
        : 'No pin yet: click the map, search an address or show the best location.'}
    </div>
  )
}
