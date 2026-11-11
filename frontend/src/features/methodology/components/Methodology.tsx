import { Link } from 'react-router'
import { ModelSummary } from '@/features/methodology/components/ModelSummary'
import { Prose } from '@/features/methodology/components/Prose'
import { SourcesTable } from '@/features/methodology/components/SourcesTable'

export function Methodology() {
  return (
    <div className="space-y-10">
      <Prose title="Affordable housing shortage">
        <p>
          For every census tract, HUD CHAS 2018-2022 gives the number of renter households with
          extremely low incomes (at or below 30% of area median income) and the number of rental
          homes that are both affordable to them and not occupied by higher-income households.
          The gap is the first minus the second: a positive gap is a shortage, a negative gap a
          surplus. Town, county and region totals are sums of tracts; tracts that cross town
          lines are shared by their 2020 census-block housing units.
        </p>
      </Prose>
      <Prose id="homeless-estimate" title="Homelessness: official counts and estimates">
        <p>
          The HUD Point-in-Time count is published only for each Continuum of Care (CoC). Those
          counts are the only official figures here and are labelled “official CoC count”.
        </p>
        <p>
          To show where risk is concentrated inside a CoC, its count is shared out across its
          tracts in proportion to the number of extremely-low-income renter households paying
          more than half their income in rent. These tract figures are labelled “estimate”;
          inside each CoC they add up exactly to the official count.{' '}
          <Link to="/estimates" className="font-medium underline">
            Read the limits before using them.
          </Link>
        </p>
      </Prose>
      <Prose title="Housing Need Index (0-100)">
        <p>
          Eight tract indicators are ranked statewide and scaled 0-1: ELI affordable gap per ELI
          renter, severe rent burden, poverty, overcrowding, estimated homelessness per 1,000
          residents, rent growth (Zillow), eviction filing rate (Eviction Lab) and distance to
          the nearest shelter or subsidised development. The index is 100 times their equal-
          weighted mean, computed when at least five are available; missing indicators are never
          filled in. Areas larger than a tract use the population-weighted mean of their tracts.
        </p>
      </Prose>
      <Prose title="Rings and areas on the map">
        <p>
          A ring is a true-distance circle around the pin. Each tract contributes the share of its
          area inside the ring, assuming people and homes are spread evenly inside the tract. In
          Areas mode the numbers are those of the chosen boundary; adding neighbours sums them,
          with every tract counted once.
        </p>
      </Prose>
      <Prose title="Candidate construction sites">
        <p>
          Sites are assessor parcels coded as developable or potentially developable vacant land
          (residential, commercial or industrial), at least half an acre, with no more than half
          their area in protected open space, wetlands or FEMA 100-year flood zones; smaller
          overlaps are flagged. Each site is scored 0-100 from its surroundings within 5 km
          (need, shortage, estimated homelessness), transit access, MBTA Communities zoning,
          estimated land cost and lot size, using the weights below. Ownership, contamination,
          slope and local zoning other than Section 3A are not screened.
        </p>
      </Prose>
      <section className="border-t border-rule pt-6">
        <h2 className="text-xl font-bold tracking-tight">Models</h2>
        <div className="mt-4">
          <ModelSummary />
        </div>
      </section>
      <section className="border-t border-rule pt-6">
        <h2 className="text-xl font-bold tracking-tight">Data sources</h2>
        <p className="mt-2 max-w-prose text-ink-soft">
          Every dataset was downloaded from its public source; the raw files are kept unchanged
          and every figure is computed from them.
        </p>
        <div className="mt-4">
          <SourcesTable />
        </div>
      </section>
    </div>
  )
}
