import type { Feature } from 'geojson'
import type { Layer, PathOptions } from 'leaflet'
import { GeoJSON } from 'react-leaflet'
import { useTracts } from '@/features/site-explorer/hooks/useExplorerData'
import { colorFor } from '@/features/site-explorer/mapStyles'
import type { BackgroundLayer } from '@/features/site-explorer/types'
import { formatDecimal } from '@/utils/format'

type Metric = Exclude<BackgroundLayer, 'sites'>

/** Tracts coloured by the chosen metric (homeless values are modelled estimates). */
export function TractChoropleth({ metric, dim = false }: { metric: Metric; dim?: boolean }) {
  const { data } = useTracts()
  if (!data) return null
  const style = (f?: Feature): PathOptions => {
    const v = (f?.properties?.[metric] as number | null) ?? null
    return { fillColor: colorFor(metric, v), fillOpacity: dim ? 0.4 : 0.7, color: '#ffffff', weight: 0.4 }
  }
  const onEach = (f: Feature, layer: Layer) => {
    const p = f.properties ?? {}
    const v = formatDecimal(p[metric] as number | null)
    const suffix = metric === 'homeless_estimate' ? ' (estimate)' : ''
    layer.bindTooltip(`${p.name}, ${p.municipality}: ${v}${suffix}`, { sticky: true })
  }
  return (
    <GeoJSON
      key={`${metric}-${dim}`}
      data={data as unknown as GeoJSON.FeatureCollection}
      style={style}
      onEachFeature={onEach}
      interactive
    />
  )
}
