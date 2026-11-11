import type { Feature } from 'geojson'
import type { Layer, PathOptions } from 'leaflet'
import { useEffect, useRef } from 'react'
import { GeoJSON } from 'react-leaflet'
import { useOutlines } from '@/features/site-explorer/hooks/useExplorerData'
import type { AreaLevel } from '@/features/site-explorer/types'

interface OutlineLayerProps {
  level: AreaLevel
  selectedId: string | null
  benefit: string[]
  onToggle: (id: string) => void
}

/** Faint outlines of every area at a level; the pin's area and benefit areas are filled. */
export function OutlineLayer({ level, selectedId, benefit, onToggle }: OutlineLayerProps) {
  const { data } = useOutlines(level)
  const toggle = useRef(onToggle)
  const selected = useRef(selectedId)
  useEffect(() => {
    toggle.current = onToggle
    selected.current = selectedId
  }, [onToggle, selectedId])
  if (!data) return null
  const style = (f?: Feature): PathOptions => {
    const id = String(f?.id ?? '')
    if (id === selectedId)
      return { color: '#14324a', weight: 3, fillColor: '#14324a', fillOpacity: 0.18 }
    if (benefit.includes(id))
      return { color: '#c98a0b', weight: 2.5, fillColor: '#c98a0b', fillOpacity: 0.28 }
    return { color: '#14324a', weight: 0.8, opacity: 0.45, fillOpacity: 0 }
  }
  const onEach = (f: Feature, layer: Layer) => {
    layer.bindTooltip(String(f.properties?.name ?? ''), { sticky: true })
    layer.on('click', (e) => {
      const id = String(f.id ?? '')
      if (selected.current && id !== selected.current) {
        e.originalEvent.stopPropagation()
        toggle.current(id)
      }
    })
  }
  return (
    <GeoJSON
      key={level}
      data={data as unknown as GeoJSON.FeatureCollection}
      style={style}
      onEachFeature={onEach}
      bubblingMouseEvents={false}
    />
  )
}
