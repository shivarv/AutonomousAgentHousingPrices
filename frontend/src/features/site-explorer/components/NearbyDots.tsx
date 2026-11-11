import { divIcon } from 'leaflet'
import { CircleMarker, Marker, Tooltip } from 'react-leaflet'
import type { NearbyShelter, NearbyTract } from '@/features/site-explorer/types'
import { formatDecimal } from '@/utils/format'

const SHELTER = divIcon({
  className: '',
  html: '<span style="display:block;width:12px;height:12px;background:#ffffff;border:3px solid #14324a"></span>',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
})

interface NearbyDotsProps {
  tracts: NearbyTract[]
  shelters: NearbyShelter[]
}

/** Tract centroids sized by the estimated homeless count, and shelters as squares. */
export function NearbyDots({ tracts, shelters }: NearbyDotsProps) {
  return (
    <>
      {tracts
        .filter((t) => (t.homeless.value ?? 0) > 0)
        .map((t) => (
          <CircleMarker
            key={t.geoid}
            center={[t.lat, t.lon]}
            radius={Math.min(10, 1.5 + Math.sqrt(t.homeless.value ?? 0))}
            pathOptions={{ color: '#ffffff', weight: 1, fillColor: '#6b4fa0', fillOpacity: 0.6 }}
          >
            <Tooltip>
              Tract {t.geoid}: {formatDecimal(t.homeless.value)} people (estimate)
            </Tooltip>
          </CircleMarker>
        ))}
      {shelters.map((s) => (
        <Marker key={`${s.lat},${s.lon}`} position={[s.lat, s.lon]} icon={SHELTER}>
          <Tooltip>
            {s.name} ({s.shelter_type}); beds: {s.beds ?? 'not published'}
          </Tooltip>
        </Marker>
      ))}
    </>
  )
}
