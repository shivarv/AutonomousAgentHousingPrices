import { formatCount, formatDecimal, formatMoney, formatShare } from '@/utils/format'

type Kind = 'count' | 'share' | 'decimal' | 'money' | 'km' | 'perSqft'

export interface MetricLabel {
  label: string
  kind: Kind
  group: 'Homelessness' | 'Affordable housing' | 'People and homes' | 'Need Index' | 'Market and context'
}

export const METRIC_LABELS: Record<string, MetricLabel> = {
  homeless_estimate: { label: 'People experiencing homelessness', kind: 'decimal', group: 'Homelessness' },
  homeless_estimate_sheltered: { label: 'Sheltered', kind: 'decimal', group: 'Homelessness' },
  homeless_estimate_unsheltered: { label: 'Unsheltered', kind: 'decimal', group: 'Homelessness' },
  homeless_estimate_per_1000: { label: 'Per 1,000 residents', kind: 'decimal', group: 'Homelessness' },
  eli_renter_households: { label: 'Extremely-low-income renter households', kind: 'count', group: 'Affordable housing' },
  eli_severely_burdened_renters: { label: 'ELI renters paying over half of income (at risk)', kind: 'count', group: 'Affordable housing' },
  eli_severe_burden_share: { label: 'Share of ELI renters at risk', kind: 'share', group: 'Affordable housing' },
  units_affordable_available_eli: { label: 'Homes affordable and available to ELI renters', kind: 'count', group: 'Affordable housing' },
  affordable_gap_eli: { label: 'ELI shortage (+) or surplus (-)', kind: 'count', group: 'Affordable housing' },
  affordable_units_per_100_eli: { label: 'Affordable homes per 100 ELI renters', kind: 'decimal', group: 'Affordable housing' },
  vli_renter_households: { label: 'Very-low-income renter households', kind: 'count', group: 'Affordable housing' },
  units_affordable_available_vli: { label: 'Homes affordable and available to VLI renters', kind: 'count', group: 'Affordable housing' },
  affordable_gap_vli: { label: 'VLI shortage (+) or surplus (-)', kind: 'count', group: 'Affordable housing' },
  hud_assisted_units: { label: 'HUD-assisted units', kind: 'count', group: 'Affordable housing' },
  lihtc_low_income_units: { label: 'LIHTC low-income units', kind: 'count', group: 'Affordable housing' },
  population: { label: 'Population', kind: 'count', group: 'People and homes' },
  households: { label: 'Households', kind: 'count', group: 'People and homes' },
  renter_households: { label: 'Renter households', kind: 'count', group: 'People and homes' },
  owner_households: { label: 'Owner households', kind: 'count', group: 'People and homes' },
  housing_units: { label: 'Housing units', kind: 'count', group: 'People and homes' },
  vacant_units: { label: 'Vacant units', kind: 'count', group: 'People and homes' },
  vacancy_rate: { label: 'Vacancy rate', kind: 'share', group: 'People and homes' },
  poverty_rate: { label: 'Poverty rate', kind: 'share', group: 'People and homes' },
  overcrowding_rate: { label: 'Overcrowded households', kind: 'share', group: 'People and homes' },
  rent_burden_share: { label: 'Renters paying over 30% of income', kind: 'share', group: 'People and homes' },
  severe_rent_burden_share: { label: 'Renters paying over 50% of income', kind: 'share', group: 'People and homes' },
  median_household_income: { label: 'Median household income', kind: 'money', group: 'People and homes' },
  median_gross_rent: { label: 'Median gross rent', kind: 'money', group: 'People and homes' },
  median_home_value: { label: 'Median home value', kind: 'money', group: 'People and homes' },
  need_index: { label: 'Housing Need Index (0-100)', kind: 'decimal', group: 'Need Index' },
  need_index_components: { label: 'Components available (of 8)', kind: 'count', group: 'Need Index' },
  distance_to_service_km: { label: 'Distance to nearest shelter or subsidised housing', kind: 'km', group: 'Need Index' },
  zhvi_latest: { label: 'Zillow home value index', kind: 'money', group: 'Market and context' },
  zhvi_growth_5yr: { label: 'Home value growth, 5 years', kind: 'share', group: 'Market and context' },
  zori_latest: { label: 'Zillow rent index', kind: 'money', group: 'Market and context' },
  zori_growth_5yr: { label: 'Rent growth, 5 years', kind: 'share', group: 'Market and context' },
  eviction_filings_annual: { label: 'Eviction filings per year', kind: 'decimal', group: 'Market and context' },
  eviction_filing_rate: { label: 'Eviction filing rate', kind: 'share', group: 'Market and context' },
  land_value_per_sqft: { label: 'Assessed land value per sq ft (median)', kind: 'perSqft', group: 'Market and context' },
  land_value_parcels: { label: 'Parcels behind the land value', kind: 'count', group: 'Market and context' },
}

export function formatMetric(kind: Kind, v: number | null): string {
  switch (kind) {
    case 'count':
      return formatCount(v)
    case 'share':
      return formatShare(v)
    case 'money':
      return formatMoney(v)
    case 'km':
      return v === null ? 'no data' : `${formatDecimal(v)} km`
    case 'perSqft':
      return v === null ? 'no data' : `$${formatDecimal(v)}`
    default:
      return formatDecimal(v)
  }
}
