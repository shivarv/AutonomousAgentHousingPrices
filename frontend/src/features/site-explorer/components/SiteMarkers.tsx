import { CircleMarker, Tooltip } from 'react-leaflet'
import { useSites } from '@/features/sites'
import type { SiteFilter, SiteSummary } from '@/features/sites'

interface SiteMarkersProps {
  filter: SiteFilter
  onSelect: (site: SiteSummary) => void
}

const LIMIT = 500

/** Top-ranked candidate sites (for the current filter) as markers. */
export function SiteMarkers({ filter, onSelect }: SiteMarkersProps) {
  const { data } = useSites(filter, LIMIT)
  if (!data) return null
  return (
    <>
      {data.sites.map((s) => (
        <CircleMarker
          key={s.id}
          center={[s.lat, s.lon]}
          radius={4 + (s.score / 100) * 5}
          pathOptions={{ color: '#14324a', weight: 1, fillColor: '#c98a0b', fillOpacity: 0.9 }}
          eventHandlers={{ click: () => onSelect(s) }}
          bubblingMouseEvents={false}
        >
          <Tooltip>
            #{s.rank_state} {s.municipality}: score {s.score.toFixed(1)}
          </Tooltip>
        </CircleMarker>
      ))}
    </>
  )
}
