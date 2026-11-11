import { Prose } from '@/features/methodology/components/Prose'

export function AboutEstimates() {
  return (
    <div className="space-y-10">
      <Prose title="What an estimate is">
        <p>
          A tract estimate is the official Point-in-Time count of its Continuum of Care, shared
          out in proportion to the tract’s share of the CoC’s extremely-low-income renters who pay
          more than half their income in rent. It answers “where within this region are the
          people most at risk of homelessness concentrated?”, not “how many people are homeless
          in this tract?”.
        </p>
        <p>
          Estimates are always shown with the word “estimate”, the year of the count and this
          method. Only figures for a whole CoC (the “Homelessness region” level on the map) are
          official counts.
        </p>
      </Prose>
      <Prose title="Why they can be wrong for a single place">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            The share-out uses risk of homelessness, not where people sleep. People in shelters
            are counted where the shelter is, and families in state emergency assistance may be
            placed in hotels far from their home town.
          </li>
          <li>
            Shelter bed counts are not published by location, so tracts with large shelters are
            likely under-estimated and others over-estimated.
          </li>
          <li>
            People sleeping outside gather in places (downtowns, transit hubs) that a
            housing-cost measure does not capture.
          </li>
          <li>
            The count is from 2025; the rent-burden data behind the share-out is from 2018-2022.
          </li>
          <li>
            The Balance of State CoC covers more than a hundred towns, so its count is spread
            over a very large and varied area.
          </li>
        </ul>
      </Prose>
      <Prose title="How sensitive they are">
        <p>
          Sharing the same counts out by population instead of risk changes which tracts come
          out on top a great deal, while town rankings stay broadly similar. Use town, county or
          region totals where you can, and treat a single tract as an indication of risk.
        </p>
      </Prose>
      <Prose title="Privacy">
        <p>
          No location of any individual is used or shown. Domestic-violence shelters are never
          downloaded or displayed; other shelters come from public OpenStreetMap entries.
        </p>
      </Prose>
    </div>
  )
}
