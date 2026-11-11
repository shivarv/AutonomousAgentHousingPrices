import { FigureLabel } from '@/components/ui/FigureLabel'
import type { SiteDetail } from '@/features/sites'
import { describeGap, formatDecimal, formatKm, formatMoney, formatShare } from '@/utils/format'

function prov(site: SiteDetail, key: string): string {
  const p = site.provenance[key]
  if (!p) return ''
  return [p.source, p.year, p.note].filter(Boolean).join(', ')
}

export function SiteDetailPanel({ site }: { site: SiteDetail }) {
  const f = site.features as Record<string, number | string | boolean | null>
  const parts = Object.entries(site.weights).map(([k, w]) => ({
    key: k,
    weight: w,
    points: 100 * w * (site.components[k] ?? 0),
    text: site.component_descriptions[k] ?? k,
  }))
  return (
    <section className="space-y-3 rounded-sm border border-marker bg-marker-soft/40 p-3" aria-live="polite">
      <div>
        <p className="text-sm text-ink-soft">
          Candidate site #{site.rank_state} statewide, #{site.rank_county} in {site.county}
        </p>
        <h2 className="text-lg font-bold">
          {site.municipality}: score {site.score.toFixed(1)} of 100
        </h2>
        <p className="mt-1 text-sm">{site.summary}</p>
      </div>
      <div>
        <h3 className="text-sm font-semibold">How the score adds up</h3>
        <ul className="mt-1 space-y-1 text-xs">
          {parts.map((p) => (
            <li key={p.key} className="grid grid-cols-[1fr_3.5rem] items-center gap-2">
              <span>
                {p.text} <span className="text-ink-soft">(weight {formatShare(p.weight)})</span>
                <span className="mt-0.5 block h-1.5 rounded-sm bg-rule">
                  <span className="block h-full rounded-sm bg-ink" style={{ width: `${(p.points / (100 * p.weight || 1)) * 100}%` }} />
                </span>
              </span>
              <span className="text-right tabular-nums">{p.points.toFixed(1)} pts</span>
            </li>
          ))}
        </ul>
      </div>
      <table className="w-full text-xs">
        <caption className="text-left text-sm font-semibold">Around the site</caption>
        <thead className="text-ink-soft">
          <tr>
            <th scope="col" className="text-left font-medium">Ring</th>
            <th scope="col" className="text-right font-medium">Need</th>
            <th scope="col" className="text-right font-medium">Affordable homes</th>
            <th scope="col" className="text-right font-medium">Homeless</th>
          </tr>
        </thead>
        <tbody>
          {site.rings.map((r) => (
            <tr key={r.radius_km} className="border-t border-rule/60">
              <th scope="row" className="py-0.5 text-left font-normal">{r.radius_km} km</th>
              <td className="text-right tabular-nums">{formatDecimal(r.need_index)}</td>
              <td className="text-right tabular-nums">{describeGap(r.affordable_gap_eli)}</td>
              <td className="text-right tabular-nums">
                {formatDecimal(r.homeless.value)} <FigureLabel label={r.homeless.label} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-ink-soft">
        Need: {prov(site, 'need_index')}. Homes: {prov(site, 'affordable_gap_eli')}. Homeless:{' '}
        {prov(site, 'homeless_estimate')}.
      </p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
        <dt className="text-ink-soft">Lot</dt>
        <dd>{formatDecimal(site.lot_size_acres)} acres, {site.use_description} (use code {site.use_code}), parcel {site.loc_id}</dd>
        <dt className="text-ink-soft">Land cost</dt>
        <dd>
          about {formatMoney(site.est_land_cost)} at ${formatDecimal(f.tract_land_value_per_sqft as number | null)}/sq ft (tract median assessed land value; {prov(site, 'land_value_per_sqft')}); parcel assessed land value {formatMoney(site.land_value)} ({prov(site, 'parcel')})
        </dd>
        <dt className="text-ink-soft">Transit</dt>
        <dd>
          {String(f.nearest_stop_name)} ({String(f.nearest_stop_mode)}) {formatKm(site.nearest_stop_km)}; rapid transit {formatKm(f.nearest_rapid_km as number | null)} ({prov(site, 'transit')})
        </dd>
        <dt className="text-ink-soft">Zoning</dt>
        <dd>{site.in_mbta3a_district ? 'Inside' : 'Not inside'} an MBTA Communities (3A) district</dd>
        <dt className="text-ink-soft">Constraints</dt>
        <dd>
          open space {formatShare(site.overlaps.open_space)}, wetlands {formatShare(site.overlaps.wetlands)}, 100-year flood zone {formatShare(site.overlaps.flood_zone_100yr)} of the lot ({prov(site, 'constraints')})
        </dd>
      </dl>
      {site.flags.length > 0 && (
        <ul className="list-disc pl-4 text-xs">
          {site.flags.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
