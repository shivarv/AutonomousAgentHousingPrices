import { SelectField } from '@/components/ui/SelectField'
import { useAreaTable } from '@/features/areas/hooks/useAreaTable'

export interface AreaFilterValue {
  county: string
  municipality: string
}

interface AreaFiltersProps {
  value: AreaFilterValue
  onChange: (value: AreaFilterValue) => void
}

/** County and town selects; choosing a county limits the town list. */
export function AreaFilters({ value, onChange }: AreaFiltersProps) {
  const counties = useAreaTable('county')
  const towns = useAreaTable('municipality')
  const countyOptions = (counties.data?.rows ?? []).map((r) => ({ value: r.id, label: r.name }))
  const townOptions = (towns.data?.rows ?? [])
    .filter((r) => !value.county || r.county_geoid === value.county)
    .map((r) => ({ value: r.id, label: r.name }))
    .sort((a, b) => a.label.localeCompare(b.label))
  return (
    <div className="grid grid-cols-2 gap-3">
      <SelectField
        label="County"
        value={value.county}
        options={countyOptions}
        placeholder="All counties"
        onChange={(county) => onChange({ county, municipality: '' })}
      />
      <SelectField
        label="City or town"
        value={value.municipality}
        options={townOptions}
        placeholder="All towns"
        onChange={(municipality) => {
          const town = towns.data?.rows.find((r) => r.id === municipality)
          onChange({ county: town?.county_geoid ?? value.county, municipality })
        }}
      />
    </div>
  )
}
