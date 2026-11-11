# Decisions

Format: date — decision — alternatives considered — reason.

- 2026-11-10 — Merge mode is `pr` (gh is logged in and `origin` exists) — local merges — run-agent.sh
  rule: PR mode whenever GitHub is available.
- 2026-11-10 — Stack task branches (each branched from the previous task branch) and push them —
  local `--no-ff` merge (also needs approval); stop working — `gh pr` and `git merge` into main
  need an interactive approval that can't be given unattended (see BLOCKERS.md); stacking lets
  later tasks build on earlier ones while leaving the merge decision to the owner.
- 2026-11-10 — gh works in session 2: drop branch stacking, return to normal PR mode (branch each
  task from up-to-date main) — keep stacking — stacking was only a workaround for the blocker.
- 2026-11-10 — scripts/db.sh uses `-k /tmp` for the Unix socket and connects over TCP
  (localhost:5544) — socket in data/pg — the project path contains a space, which breaks socket
  paths in some clients; TCP matches DATABASE_URL.
- 2026-11-10 — Backend is a non-packaged uv project (`tool.uv.package = false`), imports rooted at
  backend/ (`app.*`, `pipeline.*`) — src-layout package — simplest for `uv run` and Alembic.
- 2026-11-10 — Alembic URL from app settings, overridable by ALEMBIC_DATABASE_URL (to migrate
  housing_test) — separate ini sections — one source of truth for the URL.
- 2026-11-10 — Frontend look: "survey map" palette (paper #eef2f4, harbour ink #14324a, survey-marker
  ochre #c98a0b focus/accent; shortage #b3261e and surplus #1f7a5c always paired with a sign/label;
  estimate violet #6b4fa0), Public Sans (US civic typeface, self-hosted via @fontsource, tabular
  numerals) — cream/serif or dark dashboard defaults — fits a civic planning audience, no
  external font requests.
- 2026-11-10 — Frontend lint is oxlint (the current Vite template default) — add ESLint —
  `npm run lint` is what the plan requires; oxlint covers react hooks rules.
- 2026-11-10 — Latest vintages: TIGER/Line 2026 (2020 tracts, 1,620 MA tracts; 351 towns =
  county subdivisions excluding the 6 "not defined" water records), ACS 2020-2024 5-year, CHAS
  2018-2022, PIT/HIC 2007-2025, HUD CoC boundaries 2025 (10 MA CoCs), Picture of Subsidized
  Households 2025 — older vintages — newest releases available on 2026-11-10.
- 2026-11-10 — huduser.gov answers non-browser clients with an empty HTTP 202; HUD downloads send
  a browser User-Agent string — skip HUD data — the files are public-domain federal data meant
  for download; no login or terms are bypassed.
- 2026-11-10 — ZIP→tract: HUD USPS crosswalk needs an API token we don't have; use the Census 2020
  ZCTA-tract relationship file, weighted by residential share = 2020 block housing units
  (TIGER tabblock20 HOUSING20, block internal point located in a ZCTA polygon) — land-area
  weights — residential weighting is what PLAN.md asks for.
- 2026-11-10 — RTA GTFS from the MobilityData catalogue mirror (latest.zip per feed), including
  WRTA and GATRA whose direct feeds are marked inactive — agency sites one by one — one stable
  source; stop locations change slowly. MBTA GTFS comes directly from cdn.mbta.com.
- 2026-11-10 — Parcels: MassGIS statewide L3 parcels gdb (754 MB, 2.2 M polygons, 2.55 M assessing
  rows) — 8.5 GB aggregate gdb / per-town downloads — fits the 8 GB budget. Owner name/address
  columns are never read or stored.
- 2026-11-10 — Shelters: no public structured list of MA shelter addresses with beds exists (HIC is
  CoC-level only). Use OpenStreetMap homeless-shelter features (10 in MA), with DV-related tags
  excluded in the Overpass query so DV locations are never downloaded — scraping commercial
  directories (terms) — only open-licensed option. Consequence handled in Phase 5.
- 2026-11-10 — Evictions: Eviction Lab tract filings (2000-2018, validated) — MA Trial Court
  dashboard (no machine-readable export) — only tract-level open source; its age is reported.
- 2026-11-10 — DATA_SOURCES.md is generated from a Python registry (pipeline/sources.py) plus the
  download manifests, and parsed back to load `data_sources` (matched to a stable key by dataset
  name) — hand-written markdown — keeps file, table and manifests consistent.
- 2026-11-10 — Schema additions beyond PLAN.md's list: coc_bed_counts (HIC per CoC/year),
  tract_municipalities (tract x town area shares), zip_tracts (ZIP to tract residential weights),
  neighbourhood_tracts (area shares). Each tract also gets one primary municipality, CoC and
  neighbourhood: the one holding the largest share of its area.
- 2026-11-10 — PIT/HIC series start in 2012: 2007-2011 include MA-501 (Holyoke) and MA-514
  (Framingham/Waltham), which HUD lists in no merger record, so they cannot be put on current
  CoC boundaries. Earlier merged CoCs are summed into their post-merger CoC (HUD CoC Mergers
  sheet) — keep 2007-2011 with partial coverage — totals would be inconsistent across years.
- 2026-11-10 — HIC total beds = ES + TH + SH year-round beds computed from the components
  (2013 published totals include rapid re-housing) — published totals — consistent definition.
- 2026-11-10 — Zillow ZIP values to tracts: residential-share weighted mean over ZIPs that have a
  value, renormalised over the covered share; rows with coverage < 100% carry a flag. ZORI covers
  only 204 MA ZIPs (and 30% of them five years ago), so rent growth exists for ~520 tracts —
  missing values stay NULL (no imputation here).
- 2026-11-10 — Evictions: Eviction Lab monthly file on 2020 tracts; metric = mean annual observed
  filings 2014-2016 (best-covered validated years, 1,144 tracts) / ACS 2020-2024 renter
  households. Periods differ; documented in each row's method. Tracts without validated data
  stay NULL.
- 2026-11-10 — Subsidised units are kept as two metrics, hud_assisted_units (HUD PSH 2025, all
  HUD programs incl. vouchers) and lihtc_low_income_units (LIHTC), because the programs overlap
  and summing them would double count — one combined figure.
- 2026-11-10 — Affordable and available units (CHAS): units with rent at or below the
  threshold that are occupied by a household at or below that income, plus vacant-for-rent units
  at that rent (Tables 15C, 14B); complete-facility units only. ELI/VLI renters and severe burden
  from Table 8. Statewide: 314,258 ELI renters, 144,912 available units (46 per 100), gap
  169,346 — alternative ACS income x rent tables — CHAS is the primary source in PLAN.md.
- 2026-11-10 — Area aggregates: counties, CoCs, Boston neighbourhoods and state sum each tract
  once in its primary area (tracts nest exactly in counties). Towns: 37 small towns are no
  tract's primary town and 38 tracts cross town lines, so tract counts are apportioned to towns
  by each tract's share of 2020 census-block housing units in the town (block internal point in
  town polygon), stored as tract_municipalities.housing_share; 14 tracts with no housing units
  use their area share. Weights sum to 1 per tract, so town totals add up to the state total.
  Rates are recomputed from summed numerators/denominators — primary-town only (leaves 37 towns
  with no figures); area-share weights (poor proxy for where people live) — all 351 towns need
  figures and housing units track where households are.
- 2026-11-10 — Statewide homelessness = sum of the 11 MA CoC PIT counts, only for years every CoC
  reported; a statewide sub-total (sheltered/unsheltered/beds) is left empty if any CoC lacks it —
  partial sums — a partial sum would understate the total.
- 2026-11-10 — Homeless estimate per tract: each CoC's PIT 2025 sheltered and unsheltered counts
  are allocated to the tracts whose primary CoC it is, by the tract's share of the CoC's ELI
  renters with severe rent burden (CHAS 2018-2022); sheltered uses the same weight because no
  source gives shelter beds by location (BLOCKERS.md), instead of the bed-share weighting in
  PLAN.md. Fallback for a CoC with zero weight: ACS population share, flagged (not triggered).
  Values are unrounded expected counts (sum exactly to the CoC counts); stored as
  homeless_estimate / _sheltered / _unsheltered, is_estimate=true, method starting "ESTIMATE:",
  source hud_pit — OSM shelter locations (10 points, no beds) as a sheltered weight;
  integer rounding (false precision at tract level, rounding drift) — only defensible weight
  available for every tract.
- 2026-11-10 — Homeless estimate limits (full list in reports/REPORT.md 3.2): weight measures risk,
  not where people sleep; large-shelter tracts under-estimated; unsheltered hot spots not
  captured; PIT 2025 vs CHAS 2018-2022 periods differ. API responses must carry tract or summed
  homeless figures as app.schemas.estimate.HomelessFigure (label "estimate", method, year);
  only CoC-level figures use "official CoC count" — free-text labels per endpoint — one typed
  schema makes the label impossible to omit.
- 2026-11-10 — Sensitivity result kept as is: the tract-level estimate is highly weight-dependent
  (2/20 top tracts shared with population-share allocation), towns are robust (15/20). Main
  weight unchanged (PLAN.md's at-risk weight); REPORT.md tells users to prefer town or larger
  summaries — switching weight to look more stable — the test is diagnostic, not a selection.
- 2026-11-10 — Need Index components are scaled by statewide percentile rank, (rank-1)/(n-1), among
  tracts with a value — min-max (dominated by small-denominator outliers, e.g. poverty_rate 1.0
  in tiny tracts); z-scores (not 0-1) — robust and comparable across components. Directions:
  all "higher = more need"; distance to nearest shelter or subsidised development counts as
  need (farther = less access). Rent growth is ZORI only (519 tracts; no other tract rent
  series) and eviction rate is Eviction Lab 2014-2016 (1,137 tracts); missing stays NULL.
- 2026-11-10 — Need Index = 100 x equal-weight mean of the available component scores, minimum 5 of 8
  components; weights renormalised over available components and the missing ones named in
  the row flag (1,212 tracts lack rent growth and/or eviction rate). 29 tracts get no index
  (flagged "index not computed"): 22 have under 250 residents (water, parks, airport, other
  non-residential tracts) and 7 populated tracts lack household-based ACS/CHAS renter data —
  impute missing components (would invent values) / require all 8 (only 408 tracts). Stored
  year 2026 (build year; inputs span 2014-2026). need_index source_id = hud_chas (primary
  component) because source_id holds one source; the method text lists every input source.
- 2026-11-10 — Need Index alternatives: affordability x2, homelessness+eviction x2, sparse components
  dropped. Equal weights kept as the main index (PLAN.md default; no alternative is better
  justified); the 10/20 top-20 overlap without sparse components is reported, not hidden.
- 2026-11-10 — Town/county/state Need Index = population-weighted mean of tract indexes (town
  weights = population x tract housing share); tracts without an index are excluded. Town
  summary in reports/municipality_need.csv. Small rural towns rank high (distance-to-service
  component, one or two tracts each); towns that share a single tract share its index — kept,
  and noted in REPORT.md — dropping the distance component (it is in PLAN.md's list).
- 2026-11-10 — Parcels: assessor record key = TOWN_ID:PROP_ID:n (PROP_ID is unique only within a
  town; 273 town+PROP_ID pairs list two different lines); only 96 fully identical rows dropped.
  Parcel polygons read with the non-Arrow GDAL reader, which linearises curved boundaries.
- 2026-11-10 — Home-value dataset: residential use codes 101-105, 109, 111, 112 (first three
  digits of the DOR code), total value >= $10,000 and building value > 0 (4,673 records
  dropped, logged); target TOTAL_VAL (assessed value; fiscal years 2023-2027 differ by town, so
  FY is a feature). Split 70/15/15 stratified by county and grouped by parcel LOC_ID so condo
  units of one building never straddle train and test — record-level split (leaks
  near-identical units). Split saved once (data/processed/model/split.parquet), reused after.
- 2026-11-10 — Tract land value per sq ft = median over taxable, non-condominium parcels of
  assessed LAND_VAL / lot size (0.01-500 acres, land value > 0); parcels with several assessor
  lines are summed once. Condos (102) excluded (unit land share vs whole-lot size), exempt (9xx)
  excluded (nominal land values in many towns) — mean (outlier-driven), residential-only
  (vacant/commercial land is what sites are). Tracts with < 10 parcels flagged; 16 tracts with
  none stay NULL. Tract-level only (a median is not summable, so no area aggregates).
