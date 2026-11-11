import { FigureLabel } from '@/components/ui/FigureLabel'
import type { AreaFigures } from '@/features/site-explorer/types'
import { describeGap, formatCount, formatDecimal } from '@/utils/format'

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-rule/60 py-1">
      <dt className="text-ink-soft">{label}</dt>
      <dd className="text-right font-semibold tabular-nums">{children}</dd>
    </div>
  )
}

/** The standard set of numbers for a ring or an area. */
export function FiguresList({ f }: { f: AreaFigures }) {
  const gapTone =
    f.gap_status === 'shortage' ? 'text-shortage' : f.gap_status === 'surplus' ? 'text-surplus' : ''
  return (
    <dl className="text-sm">
      <Row label="People experiencing homelessness">
        <span className="mr-1.5">{formatDecimal(f.homeless.value)}</span>
        <FigureLabel label={f.homeless.label} />
      </Row>
      <Row label="At-risk households">{formatCount(f.at_risk_households)}</Row>
      <Row label="Extremely-low-income renters">{formatCount(f.eli_renter_households)}</Row>
      <Row label="Affordable homes available to them">{formatCount(f.affordable_units_available)}</Row>
      <Row label="Shortage or surplus">
        <span className={gapTone}>{describeGap(f.affordable_gap)}</span>
      </Row>
      <Row label="Shelters / beds">
        {f.shelters} / {f.shelter_beds === null ? 'not published' : formatCount(f.shelter_beds)}
      </Row>
      <Row label="Subsidised low-income units">{formatCount(f.subsidised_units)}</Row>
      <Row label="Population">{formatCount(f.population)}</Row>
      <Row label="Need Index">{formatDecimal(f.need_index)}</Row>
    </dl>
  )
}
