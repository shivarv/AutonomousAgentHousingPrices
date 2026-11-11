import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'
import { ErrorState } from '@/components/ui/ErrorState'
import { AreaFilters } from '@/features/areas'
import { AddressSearch } from '@/features/site-explorer/components/AddressSearch'
import { AreasPanel } from '@/features/site-explorer/components/AreasPanel'
import { BestSiteButtons } from '@/features/site-explorer/components/BestSiteButtons'
import { ExplorerMap } from '@/features/site-explorer/components/ExplorerMap'
import { LayerSelect } from '@/features/site-explorer/components/LayerSelect'
import { MapLegend } from '@/features/site-explorer/components/MapLegend'
import { MapStatus } from '@/features/site-explorer/components/MapStatus'
import { ModeToggle } from '@/features/site-explorer/components/ModeToggle'
import { PinNudger } from '@/features/site-explorer/components/PinNudger'
import { RingsPanel } from '@/features/site-explorer/components/RingsPanel'
import { SiteCard } from '@/features/site-explorer/components/SiteCard'
import { useAreaStats } from '@/features/site-explorer/hooks/useExplorerData'
import { useExplorerState } from '@/features/site-explorer/hooks/useExplorerState'
import type { LatLon } from '@/features/site-explorer/types'
import { fetchBestSite, fetchSite } from '@/features/sites'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

type Focus = { pin: LatLon; zoom: number; seq: number }

export function SiteExplorer() {
  const s = useExplorerState()
  const qc = useQueryClient()
  const [params] = useSearchParams()
  const [focus, setFocus] = useState<Focus | null>(null)
  const [bestError, setBestError] = useState<unknown>(null)
  const [bestLoading, setBestLoading] = useState(false)
  const pin = useDebouncedValue(s.pin, 300)
  const radii = useDebouncedValue(s.radii, 300)
  const stats = useAreaStats(pin, radii, s.mode === 'rings')
  const seq = useRef(0)

  const goTo = (p: LatLon, zoom: number, siteId: number | null = null) => {
    s.setPin(p, siteId)
    seq.current += 1
    setFocus({ pin: p, zoom, seq: seq.current })
  }

  const siteParam = params.get('site')
  const latParam = params.get('lat')
  const lonParam = params.get('lon')
  const modeParam = params.get('mode')
  const { setPin, setMode } = s
  useEffect(() => {
    if (modeParam === 'rings' || modeParam === 'areas') setMode(modeParam)
    const lat = Number(latParam)
    const lon = Number(lonParam)
    if (latParam && lonParam && Number.isFinite(lat) && Number.isFinite(lon)) {
      setPin({ lat, lon })
      seq.current += 1
      setFocus({ pin: { lat, lon }, zoom: 12, seq: seq.current })
    }
  }, [latParam, lonParam, modeParam, setPin, setMode])
  useEffect(() => {
    if (!siteParam) return
    const id = Number(siteParam)
    void qc
      .fetchQuery({ queryKey: ['site', id], queryFn: () => fetchSite(id) })
      .then((site) => {
        setPin({ lat: site.lat, lon: site.lon }, site.id)
        seq.current += 1
        setFocus({ pin: { lat: site.lat, lon: site.lon }, zoom: 14, seq: seq.current })
      })
      .catch(setBestError)
  }, [siteParam, qc, setPin])

  const showBest = (offset: number) => {
    setBestLoading(true)
    setBestError(null)
    qc.fetchQuery({
      queryKey: ['best-site', s.filter, offset],
      queryFn: () => fetchBestSite(s.filter, offset),
    })
      .then((site) => {
        s.setBestOffset(offset)
        goTo({ lat: site.lat, lon: site.lon }, 14, site.id)
      })
      .catch(setBestError)
      .finally(() => setBestLoading(false))
  }

  return (
    <div className="flex flex-1 flex-col lg:h-[calc(100dvh-7.5rem)] lg:flex-none lg:flex-row">
      <section className="relative flex h-[60vh] min-h-80 lg:h-auto lg:flex-1" aria-label="Map">
        <ExplorerMap s={s} pin={pin} stats={stats.data} focus={focus} />
        <MapStatus layer={s.layer} mode={s.mode} level={s.level} />
        <div className="pointer-events-none absolute bottom-6 left-2 z-[500]">
          <MapLegend layer={s.layer} showRings={s.mode === 'rings'} />
        </div>
      </section>
      <aside
        className="w-full space-y-4 border-t border-rule bg-paper-raised p-4 lg:w-[27rem] lg:overflow-y-auto lg:border-t-0 lg:border-l"
        aria-label="Controls and numbers"
      >
        <div>
          <h1 className="text-xl font-bold tracking-tight">Site explorer</h1>
          <p className="text-sm text-ink-soft">
            Drop a pin to see who could benefit from new affordable homes there.
          </p>
        </div>
        <AreaFilters value={s.filter} onChange={s.changeFilter} />
        <BestSiteButtons offset={s.bestOffset} loading={bestLoading} onShow={showBest} />
        {Boolean(bestError) && <ErrorState title="Could not show a site" error={bestError} />}
        <AddressSearch onFound={(p) => goTo(p, 15)} />
        <div className="flex flex-wrap items-end justify-between gap-3">
          <ModeToggle mode={s.mode} onChange={s.setMode} />
          <LayerSelect layer={s.layer} onChange={s.setLayer} />
        </div>
        <PinNudger pin={s.pin} onMove={(p) => s.setPin(p, s.siteId)} />
        {s.siteId !== null && <SiteCard siteId={s.siteId} />}
        {s.mode === 'areas' ? (
          <AreasPanel s={s} pin={pin} />
        ) : (
          <RingsPanel s={s} stats={stats} />
        )}
      </aside>
    </div>
  )
}
