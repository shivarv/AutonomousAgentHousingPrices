import { divIcon } from 'leaflet'
import { Marker, useMapEvents } from 'react-leaflet'
import type { LatLon } from '@/features/site-explorer/types'

const PIN = divIcon({
  className: '',
  html: '<span style="display:block;width:22px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#c98a0b;border:3px solid #14324a;box-shadow:0 1px 3px rgba(0,0,0,.4)"></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 22],
})

interface PinLayerProps {
  pin: LatLon | null
  onMove: (p: LatLon) => void
}

/** Draggable pin; clicking anywhere on the map moves it there. */
export function PinLayer({ pin, onMove }: PinLayerProps) {
  useMapEvents({ click: (e) => onMove({ lat: e.latlng.lat, lon: e.latlng.lng }) })
  if (!pin) return null
  return (
    <Marker
      position={[pin.lat, pin.lon]}
      icon={PIN}
      draggable
      keyboard={false}
      title="Selected place (drag to move)"
      eventHandlers={{
        dragend: (e) => {
          const ll = e.target.getLatLng()
          onMove({ lat: ll.lat, lon: ll.lng })
        },
      }}
    />
  )
}
