import { SelectField } from '@/components/ui/SelectField'
import { LAYER_TITLES } from '@/features/site-explorer/mapStyles'
import type { BackgroundLayer } from '@/features/site-explorer/types'

const OPTIONS = (Object.keys(LAYER_TITLES) as BackgroundLayer[]).map((k) => ({
  value: k,
  label: LAYER_TITLES[k],
}))

export function LayerSelect({ layer, onChange }: { layer: BackgroundLayer; onChange: (l: BackgroundLayer) => void }) {
  return (
    <SelectField
      label="Map background"
      value={layer}
      options={OPTIONS}
      onChange={(v) => onChange(v as BackgroundLayer)}
    />
  )
}
