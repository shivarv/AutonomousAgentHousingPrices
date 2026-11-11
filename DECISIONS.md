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
- 2026-11-10 — Home-value model: scikit-learn HistGradientBoostingRegressor replaces LightGBM
  (blocked, see BLOCKERS.md) — XGBoost/CatBoost (same libomp issue / heavy) — same algorithm
  family, OpenMP bundled. Log-value target, predictions clipped to the train log range; ridge
  on log1p sizes as the linear model. Grid: 3 ridge alphas, 8 HGB settings, chosen on
  validation MAPE (lr 0.1, 255 leaves, 600 iterations; val MAPE 0.116). Test scored once:
  0.114 vs baseline 0.326 (-65%, target -25% met). Session 4 re-ran the identical,
  deterministic script only because the saved model file was missing after the session-3
  checkpoint; no setting changed and the test numbers were bit-identical, so this is not a
  second look at the test split.
- 2026-11-10 — Site screening codes: MA DOR vacant-land codes 130/131 (developable / potentially
  developable residential), 390/391 (commercial), 440/441 (industrial); undevelopable vacant
  land (132/392/442) and tax-exempt (9xx, public land whose vacancy the code does not record)
  are excluded — all vacant codes (132 = undevelopable by definition). Minimum lot 0.5 acre
  (PLAN start value, kept) on GIS polygon area — assessor LOT_SIZE (missing for many vacant
  parcels, and it barely correlates with polygon area). Constraints: all MassGIS open-space
  polygons (any protection level, conservative), all MassDEP wetland types incl. open water,
  FEMA NFHL SFHA_TF='T' (A, AE, AH, AO, VE). A parcel is dropped when more than 50% of its
  area falls in the union of the three layers (stricter than per-layer, so no kept parcel
  exceeds 50% in any one layer); overlaps of 1% or more are flagged — <1% treated as boundary
  slivers and not flagged (shares still stored). Result: 44,935 lots -> 40,873 sites
  (4,062 dropped, 14,067 flagged). 3A district = interior point inside a district (194).
- 2026-11-10 — Ring statistics (sites and /api/area-stats share one module, app.services.rings):
  geodesic circle built in an azimuthal-equidistant projection centred on the point, then
  projected to MA State Plane; tract counts are summed with the share of the tract's area
  inside the circle (uniform spread within a tract assumed), using the same simplified tract
  boundaries the database stores; ring Need Index = population x share weighted mean —
  centroid-in-circle (unstable for 1.5 km rings), block-level weights (would need a new
  table; PLAN specifies tract area shares). Shelter beds within rings are not available
  (OSM shelters have no bed counts; HIC beds are CoC-level only) — shelters are counted.
- 2026-11-10 — Site score weights: need 0.25, ELI shortage 0.20, homeless estimate 0.15 (all
  within 5 km), transit closeness 0.15, 3A district 0.10, low land cost per sq ft 0.10, lot size
  0.05; continuous components as statewide percentile ranks among the 40,873 screened sites —
  min-max (outlier-driven: lot sizes reach 5,000 acres), learned weights (no outcome to learn
  from). 5 km is the main ring (walk/short transit trip catchment for residents); 1.5 and 15 km
  are stored and shown. Weights favour need (60% on need, shortage and homelessness) because
  the audience is housing-need planning; they are a documented judgement, not an optimum.
- 2026-11-10 — API tests run on a copy of the real loaded data: scripts/seed_test_db.sh migrates
  housing_test and copies housing into it (data-only dump/restore) — synthetic fixtures (would
  be invented numbers, and spatial endpoints need real boundaries). Data-dependent tests skip
  with a message when housing_test is empty.
- 2026-11-10 — Overview shelter beds = HIC year-round beds summed over the CoCs that overlap the
  area (latest year all of them report), labelled "official CoC count" with the CoC list —
  HIC is CoC-level only, so a county or town gets its CoCs' totals, never an apportioned number.
- 2026-11-10 — Frontend: charts are hand-built SVG/HTML (single-series PIT trend line, single-series
  county bars, tables) — a chart library (new dependency for two simple charts). Choropleths use
  classed ColorBrewer scales (Blues for the Need Index, BrBG diverging for the ELI gap, Purples for
  the homeless estimate), colour-blind safe, always with a legend and words (shortage/surplus).
  The Census Geocoder is called through GET /api/geocode because it sends no CORS headers.
- 2026-11-10 — Docker (Phase 11): backend image built with uv (`uv sync --locked --no-dev`) on
  python:3.12-slim, non-root uid 1001, code at /srv/backend so pipeline/paths.py's project root
  is /srv and an on-demand `pipeline` compose profile mounts data/, reports/ and DATA_SOURCES.md
  there; frontend served by nginx-unprivileged which proxies /api to the backend (same origin,
  no CORS or build-time API URL needed) — a Node static server (`serve`/`vite preview`: no
  proxy, so the browser would need the API URL and CORS). The database password defaults to a
  local-only `${POSTGRES_PASSWORD:-housing}`; CENSUS_API_KEY is passed through from the shell.
  Docker is not installed, so validation is static (pytest test_docker_files.py); pyyaml added
  as a dev dependency for it.
- 2026-11-10 — reports/STATISTICS.md is generated (pipeline.stats_report) through the API
  services, not written by hand, so report and app always agree. Per-county homelessness is
  shown as the summed tract estimate (labelled "estimate") next to the overlapping CoCs, whose
  official totals are listed separately — apportioning official counts to counties would be an
  estimate anyway. Town rankings show all towns and, separately, towns with 10,000+ residents
  because one- or two-tract towns dominate the top of the population-weighted index.
- 2026-11-10 — scripts/validate.py checks /api/areas/at against an independent brute-force
  shapely point-in-polygon over the stored boundaries (not the API's own STRtree), calls the
  API in-process with FastAPI's TestClient on the `housing` database (no server needed), and
  sums of fractional estimates are compared with a 0.5-person tolerance. The git check requires
  a clean `main` with no unmerged task branches or open PRs, so on a task branch it is run with
  `--skip-git`; the final run is on main after the merge.
- 2026-11-11 — Vercel deployment (Phase 13, requested by the owner): two Vercel projects from
  one repo. The API is a root-level `api/index.py` that adds backend/ to sys.path and exports
  the FastAPI app, with a root `requirements.txt` of runtime packages only (about 88 MB
  installed). Alternatives considered: (1) a Vercel project rooted at backend/, which would
  install the full pyproject (geopandas, scikit-learn, pyarrow, matplotlib and more, close to
  Vercel's 500 MB Python limit), and Vercel's docs don't say which file wins when pyproject.toml
  and requirements.txt both exist; (2) moving pipeline packages into extras or dependency
  groups, which would change every local `uv run` command. A test keeps requirements.txt in
  step with the app's imports. Serverless instances are frozen between requests, so
  `DB_NULL_POOL=true` uses SQLAlchemy NullPool with the provider's pooled URL, and
  `postgres://` URLs are normalised to the psycopg driver. The frontend reads the API origin
  from `VITE_API_BASE_URL` (already supported), and the API allows it through `CORS_ORIGINS`.
  A rewrite proxy was rejected because it would hard-code the API URL in vercel.json. The data
  reaches the hosted database through `scripts/publish_db.sh` (pg_dump/pg_restore, URL taken
  from the environment). The pipeline itself is not run on Vercel.
