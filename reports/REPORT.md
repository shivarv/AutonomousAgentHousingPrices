# Massachusetts Housing Need & Site Finder — Report

Data downloaded and loaded on 2026-11-10. Every figure below comes from those downloads or is
computed from them; detailed tables are in `reports/STATISTICS.md` (generated from the
database by `pipeline.stats_report`). Homelessness figures below Continuum of Care (CoC) level
are modelled **estimates** (section 3.2).

## 1. Question

How many people are homeless or at risk in Massachusetts, where is the affordable housing
shortage, and which places are available and suitable for building new homes?

The audience is city planners and housing nonprofits, so the product covers the whole state
(1,620 census tracts, 351 cities and towns, 14 counties, 11 CoCs, Boston neighbourhoods) and
delivers (1) statewide, county and town statistics with a ranked list of candidate sites and
(2) an interactive site explorer: drop or drag a pin and see the estimated people experiencing
homelessness, at-risk households and the affordable shortage or surplus for the area under the
pin (tract, Boston neighbourhood, town, county or CoC, extendable into a "benefit area") or
for three distance rings.

## 2. Data

All datasets, URLs, download dates, licences and columns are listed in `DATA_SOURCES.md`;
row counts, years and missing-value rates are in `reports/data_audit.md`. In short (23
datasets, all public, no paid data):

| Need | Dataset | Year(s) | Geography |
|---|---|---|---|
| Boundaries | Census TIGER/Line tracts, towns, counties; BPDA Boston neighbourhoods; HUD CoC boundaries | 2026 vintage; CoC 2025 | tract, town, county, neighbourhood, CoC |
| Population, income, poverty, crowding, rent burden, vacancy | ACS 5-year (api.census.gov) | 2020-2024 | tract |
| Affordable gap | HUD CHAS | 2018-2022 | tract |
| Homeless counts and beds | HUD PIT and HIC | 2007-2025 (2012-2025 used for MA CoC series) | CoC only |
| Subsidised housing | HUD LIHTC; HUD Picture of Subsidized Households | to 2024; 2025 | property, tract |
| Shelters (locations only) | OpenStreetMap, domestic-violence facilities excluded | download snapshot | point |
| Parcels and values | MassGIS Standardized Assessors' Parcels (L3) | FY 2023-2027 by town | parcel |
| Build constraints | MassGIS open space; MassDEP wetlands; FEMA NFHL | 2026; 2005 mapping; 2025 | polygon |
| Multifamily zoning | MBTA Communities (Section 3A) districts | 2026-10 | polygon |
| Transit | MBTA and regional transit authority GTFS | current feeds | stop |
| Rents and values | Zillow ZORI and ZHVI with Census ZCTA-tract relationship | 2015-2026; 2000-2026 | ZIP -> tract |
| Evictions | Eviction Lab tract filings | MA validated 2004-2018 | tract |

Sources that could not be used are recorded in `BLOCKERS.md`: shelter bed counts by location
(not published; HIC is per CoC), DESE homeless student counts (pages refuse automated
clients) and Trial Court eviction filings (no downloadable dataset; Eviction Lab used).

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

### 3.4 Home-value model (cost context for sites)

Target: assessed total value of 2.05 M residential assessor records (MassGIS L3, use codes
101-105, 109, 111, 112; fiscal years 2023-2027). Split once 70/15/15, stratified by county and
grouped by parcel so condo units of one building never straddle splits. Baseline: the median
assessed value of the record's town in the train split (county median fallback). Models:
ridge regression and histogram gradient boosting (scikit-learn; LightGBM could not load on
this machine, see BLOCKERS.md) on log value, with parcel size, building, age, location,
train-only town/tract medians and tract context (ACS income and value, Zillow ZHVI).
Hyper-parameters and the model were chosen on the validation split only; the test split was
scored once.

| | Validation MAPE | Test MAPE | Test median APE |
|---|---|---|---|
| Baseline (town median) | 33.2% | 32.6% | 21.5% |
| Ridge (best alpha) | 18.5% | — | — |
| Gradient boosting (chosen) | 11.6% | 11.4% | 7.0% |

Test MAPE is 65% below the baseline's, so the target (at least 25% lower) is met. Errors are
largest on Nantucket (28%), Dukes (25%) and Berkshire (20%), where values are most dispersed
(`reports/model_error_by_county.png`). The most important features (permutation importance on
validation) are residential floor area, location (x, y) and the town and tract medians.
Limits: the target is assessed value, not sale price; assessment years differ by town.
Tract land value per sq ft (median assessed land value per lot sq ft, taxable non-condo
parcels) is computed separately for site cost scoring (1,604 of 1,620 tracts).

### 3.5 Candidate construction sites

Screening (`pipeline.sites.screen`): parcels whose state use code is developable or
potentially developable vacant land (130/131 residential, 390/391 commercial, 440/441
industrial), at least 0.5 acre by GIS polygon area, tax parcels only. For each parcel the
share of its area in MassGIS open space (all protection levels), MassDEP wetlands (all
types) and FEMA 100-year flood zones (SFHA) is computed, and parcels with more than half
their area in the union of these layers are dropped; any overlap of 1% or more is flagged.
44,935 lots -> 40,873 sites (4,062 dropped; 14,067 flagged).

Features (`pipeline.sites.features`): for geodesic rings of 1.5, 5 and 15 km, tract values
summed by the share of each tract's area inside the ring (ELI affordable gap, homeless
estimate — a modelled estimate — and population) and the population-weighted Need Index;
OSM shelters in the ring (no per-shelter bed counts exist); distance to the nearest MBTA/RTA
stop and rapid-transit stop; MBTA Communities (3A) district; land cost = tract median
assessed land value per sq ft x lot area.

Score (`pipeline.sites.score`): 100 x weighted mean of statewide percentile ranks among the
screened sites — Need Index within 5 km 25%, ELI shortage within 5 km 20%, homeless estimate
within 5 km 15%, transit closeness 15%, inside a 3A district 10%, low land cost 10%, lot size
5%. Weights are a documented judgement favouring need, not an optimum. Each site has a
plain-English summary generated only from its own features. Scores range 4.6-87.2; the top
sites are in Fall River, Lawrence and Worcester. `reports/candidate_sites.csv` lists the top
100 statewide plus the top 10 in each county (185 rows); all sites are in `site_candidates`.
Limits: use codes and assessed values come from town assessors and vary in quality;
zoning other than 3A, ownership, contamination and slopes are not screened; tract-level
values are assumed evenly spread within each tract.

## 4. Results

**Homelessness (official CoC counts).** On the night of the January 2025 Point-in-Time count,
28,311 people were experiencing homelessness in Massachusetts (sum of the 11 CoCs): 26,563
sheltered and 1,748 unsheltered. That is 1,049 (3.6%) fewer than the 2024 peak of 29,360 but
61.8% more than in 2012 (17,501); the series low was 15,079 in 2021, and the count nearly
doubled between 2022 (15,507) and 2024. The Balance of State CoC (MA-516, 10,539 people) and
Boston (MA-500, 5,540) account for 57% of the total; Worcester (2,864) and Springfield/Hampden
(2,709) follow. Year-round shelter beds (HIC 2025) total 19,647, 0.69 per person counted.

**At risk.** 314,258 renter households have extremely low incomes (<= 30% of area median);
170,134 of them pay more than half their income for housing.

**Affordable housing shortage.** Only 144,912 homes are both affordable and available to those
households — 46 per 100 — a statewide shortage of 169,346 (CHAS 2018-2022). Every county has a
shortage; the largest are Suffolk (34,964), Middlesex (33,346), Essex (23,301) and Worcester
(19,192). By town the largest shortages are Boston (30,053), Worcester (9,303), Springfield
(7,001), Fall River (4,686), Lowell (4,580), Lynn (4,430) and Lawrence (4,321). Among those
15 largest-shortage towns, coverage is lowest in Everett (27 available units per 100 ELI
households) and Salem (29).

**Where need is greatest.** Among cities and towns with at least 10,000 residents, the
population-weighted Housing Need Index is highest in Ware (66.3), Lawrence (63.8), Lynn (62.8),
Hull (61.9), Lowell (61.8), Fall River (61.7), Southbridge (61.3), Gardner and Chelsea (60.7)
and Fitchburg (60.0); the statewide mean is 49.5. Several very small towns rank above them on a
single tract (section 3.3). Of the 20 highest-scoring tracts statewide, 4 are in Springfield,
3 each in Lowell and Lynn, and 2 in Boston (`reports/top_tracts.csv`).

**Candidate sites.** 40,873 developable parcels of at least 0.5 acre pass the constraint
screen. The highest-scoring sites (score 87.2 to 83.9 for the top 15) are close to transit
inside MBTA Communities districts in Fall River, Lawrence, Worcester, Taunton and Lowell, each
with an estimated shortage of 1,400-8,700 ELI homes and an estimated 170-1,300 people
experiencing homelessness within 5 km (estimates). The best site in every county is listed in
`reports/STATISTICS.md` 6.2; on the Islands (Dukes, Nantucket) the best sites score only 42-44
because need, transit and zoning components are low there.

**Home-value model.** Test MAPE 11.4% against 32.6% for the town-median baseline, a 65%
reduction; the target (at least 25%) is met (section 3.4, `reports/model_metrics.json`).

**Product.** A FastAPI backend serves every figure with its source and year (statistics,
tracts, sites, ring statistics for any point in under a second, area lookup, outlines,
benefit-area summaries, official CoC series, shelters, model metrics, sources), and a React app
provides the overview, the site explorer map and the methodology pages. Docker files are
provided but could not be run on the build machine (README).

## 5. Limitations

- **Tract homelessness numbers are modelled estimates, not counts** (3.2). They distribute
  each CoC's official count by an at-risk weight; tract rankings change a lot under another
  weight (top-20 overlap 2/20 with a population weight), town rankings much less (15/20).
  Shelter bed locations are not published, so sheltered people could not be placed by beds.
- **Periods differ**: CHAS 2018-2022, ACS 2020-2024, PIT/HIC 2025, Eviction Lab 2004-2018,
  assessor fiscal years 2023-2027. The shortage reflects 2018-2022 conditions.
- **Sparse components**: rent growth covers 519 tracts and evictions 1,137; the top of the
  Need Index partly depends on where these exist (3.3). 29 tracts have no index (flagged).
- **Small areas**: ACS and CHAS tract values carry sampling error (margins are not
  propagated); CHAS rounds counts. Small towns with one or two tracts are volatile.
- **Site screen is partial**: zoning other than 3A, ownership, contamination, slopes, utilities
  and the willingness of owners to sell are not checked; assessor use codes vary in quality;
  land cost is a tract median assessed value, not a price; site weights are a judgement.
- **Uniform-spread assumption**: ring and benefit-area totals assume tract counts are spread
  evenly over each tract's area.
- **Home values** are assessed values, not sale prices; the gradient-boosting model ran in
  scikit-learn because LightGBM could not load on the build machine.
- **Untested Docker files** (no Docker on the build machine).

See also `BLOCKERS.md` and `reports/data_audit.md`.

## 6. Next steps

1. Obtain shelter bed counts by site (from CoCs under a data-sharing agreement, without
   domestic-violence shelters) to allocate sheltered people by bed location as planned.
2. Add the MA DESE homeless student counts and Trial Court eviction filings when they can be
   downloaded, and refresh Eviction Lab with newer years.
3. Propagate ACS margins of error into the Need Index and ring totals, and show ranges.
4. Screen sites further: local zoning by-laws, MassDEP contamination sites, slope (LiDAR),
   sewer and water service, and public ownership (often the most feasible land).
5. Calibrate site weights with planners and nonprofits; let users change them in the app.
6. Re-run the pipeline when PIT 2026, CHAS 2019-2023 and ACS 2021-2025 are released, and build
   and test the Docker images on a machine with Docker.
