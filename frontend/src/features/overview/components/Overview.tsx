import { useState } from 'react'
import { ErrorState } from '@/components/ui/ErrorState'
import { LoadingState } from '@/components/ui/LoadingState'
import { AreaFilters, useAreaTable } from '@/features/areas'
import type { AreaFilterValue } from '@/features/areas'
import { CocTable } from '@/features/overview/components/CocTable'
import { CountyShortageChart } from '@/features/overview/components/CountyShortageChart'
import { HeadlineStats } from '@/features/overview/components/HeadlineStats'
import { HomelessTrendChart } from '@/features/overview/components/HomelessTrendChart'
import { Section } from '@/features/overview/components/Section'
import { TopTownsTable } from '@/features/overview/components/TopTownsTable'
import { useOverview } from '@/features/overview/hooks/useOverview'
import { SiteRankingList } from '@/features/sites'

export function Overview() {
  const [filter, setFilter] = useState<AreaFilterValue>({ county: '', municipality: '' })
  const overview = useOverview(filter.county, filter.municipality)
  const counties = useAreaTable('county')
  const towns = useAreaTable('municipality')
  const townRows = (towns.data?.rows ?? []).filter(
    (r) => !filter.county || r.county_geoid === filter.county,
  )
  return (
    <div className="space-y-10">
      <div className="max-w-xl">
        <AreaFilters value={filter} onChange={setFilter} />
      </div>
      <section aria-live="polite">
        {overview.isPending && <LoadingState label="Loading statistics" />}
        {overview.isError && (
          <ErrorState error={overview.error} onRetry={() => void overview.refetch()} />
        )}
        {overview.data && (
          <>
            <h2 className="mb-5 text-2xl font-bold tracking-tight">{overview.data.name}</h2>
            <HeadlineStats data={overview.data} />
            <p className="mt-5 max-w-prose text-sm text-ink-soft">
              {overview.data.homelessness.note}
            </p>
          </>
        )}
      </section>
      {overview.data && (
        <Section title="Homelessness over time (official counts)">
          {overview.data.homelessness.official_state && (
            <HomelessTrendChart
              years={overview.data.homelessness.official_state.years}
              title="People counted on one night in January, all Massachusetts CoCs"
            />
          )}
          <div className="mt-6">
            <CocTable cocs={overview.data.homelessness.official_cocs} />
          </div>
        </Section>
      )}
      <Section title="Affordable housing shortage by county">
        {counties.isPending && <LoadingState />}
        {counties.isError && <ErrorState error={counties.error} />}
        {counties.data && <CountyShortageChart rows={counties.data.rows} />}
      </Section>
      <Section title="Cities and towns with the highest need">
        {towns.isPending && <LoadingState />}
        {towns.isError && <ErrorState error={towns.error} />}
        {towns.data && <TopTownsTable rows={townRows} />}
      </Section>
      <Section title="Candidate construction sites">
        <SiteRankingList filter={filter} />
      </Section>
    </div>
  )
}
