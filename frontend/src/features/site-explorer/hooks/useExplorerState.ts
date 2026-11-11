import { useCallback, useState } from 'react'
import type { AreaFilterValue } from '@/features/areas'
import type {
  AreaLevel,
  BackgroundLayer,
  ExplorerMode,
  LatLon,
} from '@/features/site-explorer/types'

export const RING_PRESETS = {
  urban: { label: 'Urban', radii: [1.5, 5, 15] },
  regional: { label: 'Regional', radii: [5, 25, 50] },
} as const
export type RingPreset = keyof typeof RING_PRESETS | 'custom'

/** All UI state of the site explorer in one place. */
export function useExplorerState() {
  const [pin, setPinState] = useState<LatLon | null>(null)
  const [mode, setMode] = useState<ExplorerMode>('areas')
  const [level, setLevelState] = useState<AreaLevel>('tract')
  const [radii, setRadii] = useState<number[]>([...RING_PRESETS.urban.radii])
  const [preset, setPreset] = useState<RingPreset>('urban')
  const [benefit, setBenefit] = useState<string[]>([])
  const [layer, setLayer] = useState<BackgroundLayer>('need_index')
  const [filter, setFilter] = useState<AreaFilterValue>({ county: '', municipality: '' })
  const [siteId, setSiteId] = useState<number | null>(null)
  const [bestOffset, setBestOffset] = useState<number | null>(null)

  const setPin = useCallback((p: LatLon | null, fromSite: number | null = null) => {
    setPinState(p)
    setBenefit([])
    setSiteId(fromSite)
  }, [])
  const setLevel = useCallback((l: AreaLevel) => {
    setLevelState(l)
    setBenefit([])
  }, [])
  const toggleBenefit = useCallback((id: string) => {
    setBenefit((b) => (b.includes(id) ? b.filter((x) => x !== id) : [...b, id]))
  }, [])
  const choosePreset = useCallback((p: keyof typeof RING_PRESETS) => {
    setPreset(p)
    setRadii([...RING_PRESETS[p].radii])
  }, [])
  const setRadius = useCallback((i: number, km: number) => {
    setPreset('custom')
    setRadii((r) => r.map((v, j) => (j === i ? km : v)))
  }, [])
  const changeFilter = useCallback((f: AreaFilterValue) => {
    setFilter(f)
    setBestOffset(null)
  }, [])

  return {
    pin,
    setPin,
    mode,
    setMode,
    level,
    setLevel,
    radii,
    preset,
    choosePreset,
    setRadius,
    benefit,
    toggleBenefit,
    clearBenefit: () => setBenefit([]),
    layer,
    setLayer,
    filter,
    changeFilter,
    siteId,
    bestOffset,
    setBestOffset,
  }
}

export type ExplorerState = ReturnType<typeof useExplorerState>
