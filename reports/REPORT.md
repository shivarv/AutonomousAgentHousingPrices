# Massachusetts Housing Need & Site Finder — Report

Status: in progress. Sections are filled as each phase is completed; results below are from
the data loaded on 2026-11-10.

## 1. Question

How many people are homeless or at risk in Massachusetts, where is the affordable housing
shortage, and which places are available and suitable for building new homes?

## 2. Data

All datasets, URLs, download dates, licences and columns are listed in `DATA_SOURCES.md`;
row counts, years and missing-value rates are in `reports/data_audit.md`.

## 3. Methods

### 3.1 Affordable housing shortage (HUD CHAS 2018-2022)

Per tract: extremely-low-income (<= 30% AMI) and very-low-income (<= 50% AMI) renter
households (Table 8); units affordable **and available** to them, i.e. units at or below the
affordable rent that are vacant for rent or occupied by a household at or below that income
(Tables 15C and 14B); gap = households - available units (negative = surplus); available units
per 100 ELI renters. Statewide: 314,258 ELI renter households, 144,912 available units (46 per
100), gap 169,346.

Town, county, CoC, Boston neighbourhood and state totals are sums of tract values. Tracts nest
in counties; 38 tracts cross town lines and are apportioned to towns by their 2020 census-block
housing units in each town, so all 351 towns have figures and town totals add up to the state.

### 3.2 Homelessness: official counts and modelled estimates

**Official counts.** The HUD Point-in-Time (PIT) count is published only for each Continuum of
Care (CoC); Massachusetts has 11 CoCs covering the state. These are the only exact figures in
this product and are always presented as CoC totals ("official CoC count"). Statewide figures
are the sum of the 11 CoCs: 28,311 people on the night of the 2025 count (26,563 sheltered,
1,748 unsheltered), down from 29,360 in 2024 and up from 15,507 in 2022. HIC year-round beds
(emergency, transitional, safe haven) in 2025: 19,647.

**Modelled tract estimates ("estimate").** To show where need is likely concentrated inside a
CoC, each CoC's 2025 PIT count is distributed across the tracts whose primary CoC it is:

    estimate(tract) = PIT(CoC) x w(tract) / sum of w over the CoC's tracts

where `w` is the tract's number of extremely-low-income renter households paying more than 50%
of income for rent (HUD CHAS 2018-2022). Sheltered and unsheltered counts are allocated
separately with the same weight and added. The tract estimates of every CoC sum exactly to its
official count (checked by tests and `scripts/validate.py`). They are stored as
`homeless_estimate` (and `_sheltered`, `_unsheltered`) with `is_estimate = true`, year 2025 and
a method text beginning "ESTIMATE:". Values are not rounded: they are expected counts.

**Limits — read before using a tract number:**

- A tract estimate is **not a count** of people experiencing homelessness in that tract. It is
  the CoC's official count shared out in proportion to an at-risk indicator.
- The weight measures *risk of* homelessness (severely cost-burdened very poor renters), not
  where people sleep. People in shelters are counted where the shelter is; families in the
  state Emergency Assistance system may be placed in hotels or motels far from their home town.
  PLAN.md asked for sheltered people to be allocated by the share of shelter beds located in
  each tract; no public source gives shelter bed counts by location (the HIC is published per
  CoC only, and the 9 OpenStreetMap shelter points have no bed counts), so the same at-risk weight is
  used. Tracts with large shelters are therefore likely under-estimated and others
  over-estimated.
- Unsheltered people concentrate in places (downtowns, transit hubs, encampments) that a
  housing-cost weight does not capture.
- Periods differ: PIT 2025 counts, CHAS 2018-2022 weights.
- A tract assigned to a CoC by largest land share keeps its whole estimate in that CoC.
- The Balance of State CoC (MA-516, 10,539 people) covers 115 towns (623 tracts); its estimates are spread
  over a very large and varied area.
- Sums over a user-drawn area (rings, benefit areas) inherit these limits; only the CoC-level
  figure is an official count.

**Sensitivity check** (`reports/homeless_sensitivity.md`). Re-allocating the same CoC counts
by tract population share instead of the at-risk weight:

| Level | Top-20 overlap | Spearman rank correlation | People allocated to a different area |
|---|---|---|---|
| Tract (1,620) | 2 / 20 | 0.36 | 37.0% |
| Town (351) | 15 / 20 | 0.89 | 19.3% |

Town-level patterns are fairly robust to the weight (8 of the top 10 towns are the same), but
**individual tract estimates and tract rankings depend strongly on the chosen weight**. Tract
estimates should be read as "where severely cost-burdened very poor renters, and hence risk,
are concentrated within the CoC", not as local counts; summaries over towns or larger areas are
more reliable than single tracts.

### 3.3 Housing Need Index (0-100)

Eight tract components, each oriented so that higher means more need: affordable gap per ELI
renter household (CHAS), severe rent burden share (ACS), eviction filing rate (Eviction Lab
2014-2016), poverty rate (ACS), overcrowding rate (ACS), 5-year rent growth (Zillow ZORI),
homeless estimate per 1,000 residents (modelled estimate, 3.2), and distance to the nearest
shelter or subsidised housing development (farther = less access). Each is scaled to 0-1 by
its statewide percentile rank. The index is 100 x the equal-weight mean of the components a
tract has, with a minimum of 5 of 8; missing components are never imputed, the weights are
renormalised over the available ones, and the row flag names what is missing. 1,591 of 1,620
tracts have an index; the 29 without one (mostly water, park and other non-residential tracts,
plus 7 populated tracts without renter-household data) are flagged.

Limits: rent growth exists for only 519 tracts and eviction data for 1,137 (and is from
2014-2016); percentile scores show relative, not absolute, need; components are correlated
(several measure poverty and rent burden), so equal weights still emphasise affordability.

**Sensitivity** (`reports/need_index_sensitivity.md`): with three alternative weightings the
rank correlation with the main index stays at 0.95-0.98. Of the main top 20 tracts, 15 stay
in the top 20 when affordability components are doubled, 16 when homelessness and eviction are
doubled, but only 10 when the two sparse components (rent growth, eviction) are dropped —
the top of the ranking is partly driven by where those sparse data exist. Individual tracts
can move far (e.g. a top-20 Amherst tract falls to rank 228 when homelessness/eviction are
doubled), so the index is best used to shortlist areas, not to order neighbouring tracts.

Town, county and state indexes are population-weighted means of their tracts
(`reports/municipality_need.csv`, `reports/top_tracts.csv`). Small rural towns rank high in the
town list, largely through the distance-to-service component and because one or two tracts
decide their value; towns that share a single tract (e.g. Ashfield and Conway) share its index.

## 4. Results

To be completed (Phases 6-8 and 12).

## 5. Limitations

See the limits listed with each method above, `BLOCKERS.md`, and `reports/data_audit.md`.

## 6. Next steps

To be completed.
