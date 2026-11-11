import { geoJSON, latLng } from 'leaflet'
import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import { MASSACHUSETTS_BOUNDS } from '@/config/map'
import type { AreaFilterValue } from '@/features/areas'
import { useOutlines } from '@/features/site-explorer/hooks/useExplorerData'
import type { LatLon } from '@/features/site-explorer/types'

interface MapViewportProps {
  filter: AreaFilterValue
  focus: { pin: LatLon; zoom: number; seq: number } | null
}

/** Zooms to the county or town filter, and flies to a searched or best-site pin. */
export function MapViewport({ filter, focus }: MapViewportProps) {
  const map = useMap()
  const counties = useOutlines(filter.county ? 'county' : null)
  const towns = useOutlines(filter.municipality ? 'municipality' : null)
  useEffect(() => {
    const id = filter.municipality || filter.county
    const data = filter.municipality ? towns.data : counties.data
    if (!id) {
      map.fitBounds(MASSACHUSETTS_BOUNDS)
      return
    }
    const f = data?.features.find((x) => x.id === id)
    if (f) map.fitBounds(geoJSON(f as unknown as GeoJSON.Feature).getBounds(), { padding: [20, 20] })
  }, [filter.county, filter.municipality, counties.data, towns.data, map])
  useEffect(() => {
    if (focus) map.flyTo(latLng(focus.pin.lat, focus.pin.lon), focus.zoom, { duration: 0.8 })
  }, [focus, map])
  return null
}
