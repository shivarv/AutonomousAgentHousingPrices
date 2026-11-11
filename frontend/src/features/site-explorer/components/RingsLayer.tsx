import { Circle } from 'react-leaflet'
import { RING_DASH } from '@/features/site-explorer/mapStyles'
import type { LatLon } from '@/features/site-explorer/types'

export function RingsLayer({ pin, radii }: { pin: LatLon; radii: number[] }) {
  return (
    <>
      {[...radii]
        .sort((a, b) => b - a)
        .map((r, i) => (
          <Circle
            key={`${r}-${i}`}
            center={[pin.lat, pin.lon]}
            radius={r * 1000}
            interactive={false}
            pathOptions={{
              color: '#14324a',
              weight: 2.5,
              dashArray: RING_DASH[radii.length - 1 - i],
              fillColor: '#14324a',
              fillOpacity: 0.04,
            }}
          />
        ))}
    </>
  )
}
