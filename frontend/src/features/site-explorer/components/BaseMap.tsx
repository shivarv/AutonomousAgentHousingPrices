import type { ReactNode } from 'react'
import { MapContainer, TileLayer } from 'react-leaflet'
import { MASSACHUSETTS_BOUNDS, OSM_ATTRIBUTION, OSM_TILE_URL } from '@/config/map'

export function BaseMap({ children }: { children?: ReactNode }) {
  return (
    <MapContainer
      bounds={MASSACHUSETTS_BOUNDS}
      className="size-full min-h-[24rem]"
      keyboard
      preferCanvas
      aria-label="Map of Massachusetts. Click the map or use the pin controls to choose a place."
    >
      <TileLayer url={OSM_TILE_URL} attribution={OSM_ATTRIBUTION} opacity={0.75} />
      {children}
    </MapContainer>
  )
}
