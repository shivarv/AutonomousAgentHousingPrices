import { useAreaAt } from '@/features/site-explorer/hooks/useExplorerData'
import type { ExplorerState } from '@/features/site-explorer/hooks/useExplorerState'
import { BaseMap } from '@/features/site-explorer/components/BaseMap'
import { MapViewport } from '@/features/site-explorer/components/MapViewport'
import { NearbyDots } from '@/features/site-explorer/components/NearbyDots'
import { OutlineLayer } from '@/features/site-explorer/components/OutlineLayer'
import { PinLayer } from '@/features/site-explorer/components/PinLayer'
import { RingsLayer } from '@/features/site-explorer/components/RingsLayer'
import { SiteMarkers } from '@/features/site-explorer/components/SiteMarkers'
import { TractChoropleth } from '@/features/site-explorer/components/TractChoropleth'
import type { AreaStatsResponse, LatLon } from '@/features/site-explorer/types'

interface ExplorerMapProps {
  s: ExplorerState
  pin: LatLon | null
  stats: AreaStatsResponse | undefined
  focus: { pin: LatLon; zoom: number; seq: number } | null
}

export function ExplorerMap({ s, pin, stats, focus }: ExplorerMapProps) {
  const at = useAreaAt(pin, s.level, s.mode === 'areas')
  return (
    <BaseMap>
      {s.layer !== 'sites' && <TractChoropleth metric={s.layer} dim={s.mode === 'rings'} />}
      {s.mode === 'areas' && (
        <OutlineLayer
          level={s.level}
          selectedId={at.data?.id ?? null}
          benefit={s.benefit}
          onToggle={s.toggleBenefit}
        />
      )}
      {s.layer === 'sites' && (
        <SiteMarkers filter={s.filter} onSelect={(x) => s.setPin({ lat: x.lat, lon: x.lon }, x.id)} />
      )}
      {s.mode === 'rings' && s.pin && <RingsLayer pin={s.pin} radii={s.radii} />}
      {s.mode === 'rings' && stats && (
        <NearbyDots tracts={stats.nearby_tracts} shelters={stats.nearby_shelters} />
      )}
      <PinLayer pin={s.pin} onMove={(p) => s.setPin(p)} />
      <MapViewport filter={s.filter} focus={focus} />
    </BaseMap>
  )
}
