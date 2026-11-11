import { FigureLabel } from '@/components/ui/FigureLabel'
import { StatFigure } from '@/features/overview/components/StatFigure'
import type { StatsOverview } from '@/features/overview/types'
import type { MetricValue } from '@/types/figures'
import { describeGap, formatCount, formatDecimal, formatShare } from '@/utils/format'

function src(m: MetricValue | undefined): string {
  return m ? `${m.source ?? 'unknown source'}, ${m.year ?? 'year unknown'}` : 'no data'
}

export function HeadlineStats({ data }: { data: StatsOverview }) {
  const m = data.metrics
  const h = data.homelessness
  const isState = data.level === 'state'
  const latest = h.official_state?.years.at(-1)
  const gap = m.affordable_gap_eli?.value ?? null
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-5 sm:grid-cols-2 lg:grid-cols-4">
      {isState && latest ? (
        <StatFigure
          label={`People experiencing homelessness, ${latest.year}`}
          value={formatCount(latest.total)}
          detail={
            <>
              <FigureLabel label="official CoC count" /> HUD Point-in-Time, sum of{' '}
              {h.official_state?.coc_count} CoCs
            </>
          }
        />
      ) : (
        <StatFigure
          label={`People experiencing homelessness, ${h.area_estimate.year ?? ''}`}
          value={formatDecimal(h.area_estimate.value)}
          detail={
            <>
              <FigureLabel label="estimate" /> sum of modelled tract estimates
            </>
          }
        />
      )}
      <StatFigure
        label="Extremely-low-income renter households"
        value={formatCount(m.eli_renter_households?.value)}
        detail={`${formatCount(m.eli_severely_burdened_renters?.value)} pay over half their income in rent (at risk); ${src(m.eli_renter_households)}`}
      />
      <StatFigure
        label="Affordable homes for them"
        value={describeGap(gap)}
        tone={gap !== null && gap > 0 ? 'shortage' : 'surplus'}
        detail={`${formatDecimal(m.affordable_units_per_100_eli?.value)} affordable and available per 100 households; ${src(m.affordable_gap_eli)}`}
      />
      <StatFigure
        label="Shelter beds (year-round)"
        value={formatCount(data.shelter_beds.value)}
        detail={`HUD HIC ${data.shelter_beds.year ?? ''}, ${isState ? `all ${h.official_cocs.length} CoCs` : data.shelter_beds.geography} (official, CoC level)`}
      />
      <StatFigure
        label="Population"
        value={formatCount(m.population?.value)}
        detail={src(m.population)}
      />
      <StatFigure
        label="Vacancy rate"
        value={formatShare(m.vacancy_rate?.value)}
        detail={`${formatCount(m.vacant_units?.value)} vacant homes; ${src(m.vacancy_rate)}`}
      />
      <StatFigure
        label="Housing Need Index (0-100)"
        value={formatDecimal(m.need_index?.value)}
        detail="Population-weighted mean of tract indexes"
      />
      <StatFigure
        label="Subsidised low-income units"
        value={formatCount(
          (m.hud_assisted_units?.value ?? 0) + (m.lihtc_low_income_units?.value ?? 0),
        )}
        detail="HUD-assisted plus LIHTC (programmes can overlap)"
      />
    </dl>
  )
}
